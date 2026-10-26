import tempfile
import unittest
from pathlib import Path

from src.agents.reviewer import inspect_code


class ReviewerCodeInspectionTests(unittest.TestCase):
    def test_reviews_source_and_reports_missing_url_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "shortener.py"
            tests = root / "tests" / "test_shortener.py"
            tests.parent.mkdir()
            source.write_text(
                "class URLShortener:\n    pass\n\ndef make_handler(service):\n    return service\n",
                encoding="utf-8",
            )
            tests.write_text(
                "def test_create_and_resolve_link(): pass\n"
                "def test_invalid_url_is_rejected(): pass\n"
                "def test_redirect_resolution_records_analytics(): pass\n",
                encoding="utf-8",
            )
            state = {"code_files": {"shortener.py": str(source), "tests/test_shortener.py": str(tests)}}
            result = inspect_code(state)
            self.assertFalse(result["passed"])
            self.assertTrue(any("HTTP/HTTPS URL scheme validation" in f["message"] for f in result["findings"]))

    def test_flags_dynamic_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "shortener.py"
            tests = root / "tests" / "test_shortener.py"
            tests.parent.mkdir()
            source.write_text(
                "class URLShortener:\n    pass\n\ndef make_handler(service):\n    eval('1 + 1')\n    return service\n"
                "\ndef shorten(url):\n    parsed = urlparse(url)\n    if parsed.scheme not in (\"http\", \"https\") and not parsed.netloc: pass\n",
                encoding="utf-8",
            )
            tests.write_text(
                "def test_create_and_resolve_link(): pass\n"
                "def test_invalid_url_is_rejected(): pass\n"
                "def test_redirect_resolution_records_analytics(): pass\n",
                encoding="utf-8",
            )
            state = {"code_files": {"shortener.py": str(source), "tests/test_shortener.py": str(tests)}}
            result = inspect_code(state)
            self.assertTrue(any("dynamic code execution" in f["message"] for f in result["findings"]))


if __name__ == "__main__":
    unittest.main()
