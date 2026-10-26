import tempfile
import unittest
from pathlib import Path
from shortener import URLShortener


class URLShortenerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.service = URLShortener(str(Path(self.temp_dir.name) / "test.db"))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_and_resolve_link(self):
        result = self.service.shorten("https://example.com/path")
        self.assertTrue(result["code"])
        self.assertEqual(self.service.resolve(result["code"]), "https://example.com/path")

    def test_invalid_url_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.shorten("javascript:alert(1)")

    def test_unknown_code_returns_none(self):
        self.assertIsNone(self.service.resolve("missing"))
        self.assertIsNone(self.service.stats("missing"))

    def test_redirect_resolution_records_analytics(self):
        result = self.service.shorten("https://example.com")
        self.service.resolve(result["code"])
        self.service.resolve(result["code"])
        stats = self.service.stats(result["code"])
        self.assertEqual(stats["total_clicks"], 2)
        self.assertEqual(sum(day["clicks"] for day in stats["clicks_by_day"]), 2)

    def test_expiry_must_be_positive_integer(self):
        with self.assertRaises(ValueError):
            self.service.shorten("https://example.com", 0)


if __name__ == "__main__":
    unittest.main()
