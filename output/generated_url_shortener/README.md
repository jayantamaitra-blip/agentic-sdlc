# Generated URL Shortener

A small Python standard-library URL shortener for the Agentic SDLC demo.

## Run

```bash
python shortener.py
```

The service listens on `http://127.0.0.1:8000`.

## API

- `POST /shorten` with JSON `{"url":"https://example.com"}` and optional `expires_in_days`.
- `GET /{code}` redirects to the original URL and records a click.
- `GET /stats/{code}` returns total clicks and counts by day.

## Test

```bash
python -m unittest discover -s tests -v
```

SQLite is used for persistence. This is an interview prototype, not a production deployment: it does not include authentication, rate limiting, migrations, or a production WSGI server.
