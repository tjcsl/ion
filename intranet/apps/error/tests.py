from ...test.ion_test import IonTestCase


class ErrorPageTest(IonTestCase):
    """Tests that the error pages (currently just 404 errors) render properly."""

    def test_404_page(self):
        resp = self.client.get("/nonexistent")
        self.assertEqual(resp.status_code, 404)
        self.assertIn(b"The page you requested could not be found.", resp.content)
        self.login()
        resp = self.client.get("/nonexistent")
        self.assertEqual(resp.status_code, 404)
        self.assertIn(b"The page you requested could not be found.", resp.content)
