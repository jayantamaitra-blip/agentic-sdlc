"""Build the runnable URL-shortener project from the approved design and plan."""
from pathlib import Path

OUTPUT_DIR = Path("output/generated_url_shortener")

SHORTENER_SOURCE = r'''import json
import sqlite3
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode_base62(number):
    if number == 0:
        return BASE62[0]
    result = []
    while number:
        number, remainder = divmod(number, len(BASE62))
        result.append(BASE62[remainder])
    return "".join(reversed(result))


class URLShortener:
    def __init__(self, db_path="shortener.db"):
        self.db_path = db_path
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                original_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link_id INTEGER NOT NULL REFERENCES links(id),
                clicked_at TEXT NOT NULL
            )""")

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def shorten(self, url, expires_in_days=None):
        parsed = urlparse(url or "")
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("url must be an absolute http or https URL")
        now = datetime.now(timezone.utc)
        expires_at = None
        if expires_in_days is not None:
            if not isinstance(expires_in_days, int) or isinstance(expires_in_days, bool) or expires_in_days < 1:
                raise ValueError("expires_in_days must be a positive integer")
            expires_at = (now + timedelta(days=expires_in_days)).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO links(code, original_url, created_at, expires_at) VALUES('', ?, ?, ?)",
                (url, now.isoformat(), expires_at),
            )
            code = encode_base62(cursor.lastrowid)
            conn.execute("UPDATE links SET code = ? WHERE id = ?", (code, cursor.lastrowid))
        return {"code": code, "short_url": f"http://localhost:8000/{code}"}

    def resolve(self, code):
        now = datetime.now(timezone.utc)
        with self._connect() as conn:
            link = conn.execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()
            if link is None:
                return None
            if link["expires_at"] and datetime.fromisoformat(link["expires_at"]) <= now:
                return None
            conn.execute("INSERT INTO clicks(link_id, clicked_at) VALUES(?, ?)", (link["id"], now.isoformat()))
            return link["original_url"]

    def stats(self, code):
        with self._connect() as conn:
            link = conn.execute("SELECT id FROM links WHERE code = ?", (code,)).fetchone()
            if link is None:
                return None
            rows = conn.execute(
                "SELECT substr(clicked_at, 1, 10) AS day, COUNT(*) AS count "
                "FROM clicks WHERE link_id = ? GROUP BY day ORDER BY day",
                (link["id"],),
            ).fetchall()
            total = sum(row["count"] for row in rows)
            return {"code": code, "total_clicks": total,
                    "clicks_by_day": [{"date": row["day"], "clicks": row["count"]} for row in rows]}


def make_handler(service):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, status, payload):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != "/shorten":
                return self._json(404, {"error": "not found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length) or b"{}")
                result = service.shorten(payload.get("url"), payload.get("expires_in_days"))
                self._json(201, result)
            except (ValueError, json.JSONDecodeError) as error:
                self._json(400, {"error": str(error)})

        def do_GET(self):
            if self.path.startswith("/stats/"):
                result = service.stats(self.path.removeprefix("/stats/"))
                return self._json(200, result) if result else self._json(404, {"error": "unknown code"})
            code = self.path.lstrip("/")
            if not code or "/" in code:
                return self._json(404, {"error": "not found"})
            url = service.resolve(code)
            if url is None:
                return self._json(404, {"error": "unknown or expired code"})
            self.send_response(302)
            self.send_header("Location", url)
            self.end_headers()

        def log_message(self, *_args):
            pass
    return Handler


def main():
    service = URLShortener()
    server = HTTPServer(("127.0.0.1", 8000), make_handler(service))
    print("URL shortener listening on http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
'''

TEST_SOURCE = r'''import tempfile
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
'''

PROJECT_README = '''# Generated URL Shortener\n\nA small Python standard-library URL shortener for the Agentic SDLC demo.\n\n## Run\n\n```bash\npython shortener.py\n```\n\nThe service listens on `http://127.0.0.1:8000`.\n\n## API\n\n- `POST /shorten` with JSON `{"url":"https://example.com"}` and optional `expires_in_days`.\n- `GET /{code}` redirects to the original URL and records a click.\n- `GET /stats/{code}` returns total clicks and counts by day.\n\n## Test\n\n```bash\npython -m unittest discover -s tests -v\n```\n\nSQLite is used for persistence. This is an interview prototype, not a production deployment: it does not include authentication, rate limiting, migrations, or a production WSGI server.\n'''


def implement(state):
    """Write the implementation and tests, using design and plan as inputs."""
    if not state.get("design"):
        raise ValueError("Coder requires an approved design")
    if not state.get("tasks"):
        raise ValueError("Coder requires the planner's task list")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "tests").mkdir(exist_ok=True)
    files = {
        "shortener.py": SHORTENER_SOURCE,
        "tests/test_shortener.py": TEST_SOURCE,
        "README.md": PROJECT_README,
    }
    for relative_path, content in files.items():
        destination = OUTPUT_DIR / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
    state["output_dir"] = str(OUTPUT_DIR)
    state["code_files"] = {name: str(OUTPUT_DIR / name) for name in files}
    state["implementation_notes"] = {
        "tasks_considered": [task.get("title", task.get("id")) for task in state["tasks"]],
        "design_components": [item.get("name") for item in state["design"].get("components", [])],
    }


def repair_implementation(state):
    """Attempt a bounded recovery using the captured test diagnostics.

    This prototype's Coder uses a deterministic reference implementation, so
    its available repair action is to regenerate that known-good scaffold. The
    failure output is preserved in state for inspection and for a future
    model-driven Coder to use for targeted edits.
    """
    feedback = state.get("repair_feedback")
    if not feedback:
        raise ValueError("Coder repair requires captured test failure diagnostics")

    print("Coder repair received validation/code-review diagnostics:")
    print(feedback.get("output", "No diagnostic output was captured."))
    # The current Coder is a deterministic reference implementation. Regenerating
    # it is a bounded recovery for accidental edits/corruption, not an adaptive
    # fix for arbitrary findings. A model-driven Coder can use the structured
    # test_output and review_findings fields for targeted edits.
    implement(state)
    state.setdefault("repair_history", []).append({
        "attempt": feedback.get("attempt"),
        "action": "regenerated deterministic reference implementation",
        "diagnostics_received": bool(feedback.get("output")),
        "review_findings_received": len(feedback.get("review_findings", [])),
    })
