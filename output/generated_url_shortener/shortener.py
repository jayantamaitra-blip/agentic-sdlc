import json
import sqlite3
from contextlib import closing
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
        with closing(self._connect()) as conn, conn:
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
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute(
                "INSERT INTO links(code, original_url, created_at, expires_at) VALUES('', ?, ?, ?)",
                (url, now.isoformat(), expires_at),
            )
            code = encode_base62(cursor.lastrowid)
            conn.execute("UPDATE links SET code = ? WHERE id = ?", (code, cursor.lastrowid))
        return {"code": code, "short_url": f"http://localhost:8000/{code}"}

    def resolve(self, code):
        now = datetime.now(timezone.utc)
        with closing(self._connect()) as conn, conn:
            link = conn.execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()
            if link is None:
                return None
            if link["expires_at"] and datetime.fromisoformat(link["expires_at"]) <= now:
                return None
            conn.execute("INSERT INTO clicks(link_id, clicked_at) VALUES(?, ?)", (link["id"], now.isoformat()))
            return link["original_url"]

    def stats(self, code):
        with closing(self._connect()) as conn, conn:
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
