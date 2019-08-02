from ...test.ion_test import IonTestCase


class ErrorPageTest(IonTestCase):
    """Tests that the error pages (currently just 404 errors) render properly."""

    def test_404_page(self):
        self.assertEqual(self.client.get("/nonexistent").status_code, 404)
        self.login()
        self.assertEqual(self.client.get("/nonexistent").status_code, 404)
