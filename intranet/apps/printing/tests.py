import datetime
import tempfile
from contextlib import ExitStack
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from ...test.ion_test import IonTestCase
from . import views


class PrintingTest(IonTestCase):
    def test_printing_view(self):
        self.make_admin()

        response = self.client.get(reverse("printing"))
        self.assertEqual(response.status_code, 200)


@override_settings(PRINTING_PAGES_LIMIT_TEACHERS=100, PRINTING_PAGES_LIMIT_STUDENTS=20)
class PrintingJobTest(SimpleTestCase):
    def run_job(self, watermark_fails=False, cover_fails=False, rotation=0, page_range="2"):
        packet = BytesIO()
        document = canvas.Canvas(packet)
        for text in ["First page", "Second page"]:
            document.drawString(100, 400, text)
            document.showPage()
        document.save()
        source = PdfReader(BytesIO(packet.getvalue()))
        writer = PdfWriter()
        for page in source.pages:
            page.cropbox.lower_left = (40, 45)
            page.cropbox.upper_right = (550, 740)
            page.rotate(rotation)
            writer.add_page(page)
        packet = BytesIO()
        writer.write(packet)
        job = SimpleNamespace(
            printer="test",
            file=SimpleUploadedFile("document.pdf", packet.getvalue()),
            user=SimpleNamespace(username="testuser", is_teacher=False, is_printing_admin=False),
            page_range=page_range,
            duplex=True,
            fit=True,
            printed=False,
            save=Mock(),
        )
        printed = []

        def submit(args, **kwargs):
            printed.append((args, Path(args[3]).read_bytes()))

        def cover(*args, **kwargs):
            if cover_fails:
                return None
            fd, name = tempfile.mkstemp()
            with open(fd, "wb") as output:
                output.write(b"cover sheet")
            return name

        with ExitStack() as stack:
            for name, replacement in {
                "get_printers": Mock(return_value={"test": ("Test printer", ["none"])}),
                "convert_file": Mock(side_effect=lambda filename, original: filename),
                "get_mimetype": Mock(return_value="application/pdf"),
                "get_user_ratelimit_status": Mock(return_value=False),
                "set_user_ratelimit_status": Mock(),
            }.items():
                stack.enter_context(patch.object(views, name, replacement))
            title = stack.enter_context(patch.object(views, "html_to_pdf", side_effect=cover))
            stack.enter_context(patch.object(views.subprocess, "check_output", side_effect=submit))
            if watermark_fails:
                stack.enter_context(patch.object(views, "PdfWriter", side_effect=ValueError("bad PDF")))
            if cover_fails and watermark_fails:
                with self.assertRaisesRegex(Exception, "Could not generate.*cover sheet"):
                    views.print_job(job)
                self.assertEqual(printed, [])
                self.assertFalse(job.printed)
                return printed, title
            views.print_job(job)
        self.assertTrue(job.printed)
        self.assertEqual(job.num_pages, 2)
        for args, _ in printed:
            self.assertFalse(Path(args[3]).exists())
        return printed, title

    def test_pdf_uses_one_print_job_and_no_cover_sheet(self):
        printed, title = self.run_job(cover_fails=True)
        title.assert_not_called()
        self.assertEqual(len(printed), 1)
        args, content = printed[0]
        self.assertIn("page-ranges=2", args)
        self.assertIn("sides=two-sided-long-edge", args)
        self.assertIn("fit-to-page", args)
        pdf = PdfReader(BytesIO(content))
        self.assertEqual(len(pdf.pages), 2)
        self.assertNotIn("Ion Printing | testuser", pdf.pages[0].extract_text())
        self.assertIn("Ion Printing | testuser", pdf.pages[1].extract_text())

    def test_watermark_failure_keeps_cover_sheet_fallback(self):
        printed, title = self.run_job(watermark_fails=True)
        title.assert_called_once()
        self.assertEqual(len(printed), 2)
        self.assertEqual(printed[0][1], b"cover sheet")
        self.assertNotIn("Ion Printing", PdfReader(BytesIO(printed[1][1])).pages[0].extract_text())

    @override_settings(TIME_ZONE="America/New_York")
    def test_footer_uses_ion_local_time(self):
        now = datetime.datetime(2026, 11, 17, 21, 0, tzinfo=datetime.UTC)
        with patch.object(views.timezone, "now", return_value=now):
            printed, _ = self.run_job()
        text = PdfReader(BytesIO(printed[0][1])).pages[1].extract_text()
        self.assertIn("2026-11-17 16:00", text)
        self.assertNotIn("2026-11-17 21:00", text)

    def test_failed_fallback_render_prevents_all_submission(self):
        self.run_job(watermark_fails=True, cover_fails=True)

    def test_rotated_cropped_pages_keep_the_footer(self):
        for rotation in (0, 90, 180, 270):
            with self.subTest(rotation=rotation):
                printed, _ = self.run_job(rotation=rotation, page_range="")
                for page in PdfReader(BytesIO(printed[0][1])).pages:
                    self.assertEqual(page.rotation, 0)
                    self.assert_footer_inside_crop(page)

    def assert_footer_inside_crop(self, page):
        footer_positions = []

        def check_footer(text, cm, tm, font, size):
            if "Ion Printing | testuser" in text:
                x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
                y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
                self.assertGreaterEqual(x, float(page.cropbox.left))
                self.assertGreaterEqual(y, float(page.cropbox.bottom))
                self.assertLessEqual(x + views.stringWidth(text.strip(), "Helvetica", size), float(page.cropbox.right))
                self.assertLessEqual(y + size, float(page.cropbox.top))
                footer_positions.append((x, y))

        page.extract_text(visitor_text=check_footer)
        self.assertEqual(len(footer_positions), 1)

    def test_printer_alerts_keep_upstream_list_format(self):
        output = "printer test is idle\n    Description: Test Printer\n    Alerts: media-empty-error toner-low-report\n"
        with (
            patch.object(views.cache, "get", return_value=None),
            patch.object(views.cache, "set"),
            patch.object(views.subprocess, "check_output", return_value=output),
            override_settings(CACHE_AGE={"printers_list": 60}),
        ):
            printers = views.get_printers()
        self.assertEqual(printers, {"test": ("Test Printer", ["media-empty-error", "toner-low-report"])})
        self.assertEqual(views.parse_alerts(printers["test"][1]), ("out of paper, low on toner", "broken"))
