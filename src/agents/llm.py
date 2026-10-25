import json

# Fixed answers used while we build. A real model call replaces this later.
MOCK_RESPONSES = {
    "analyst": {
        "ambiguities": [
            "How many links per day should the service handle?",
            "Should short links expire?",
            "Is user login required, or are links anonymous?",
        ],
        "assumptions": [
            "Links do not expire unless the user sets an expiry",
            "Anonymous use, no login in version one",
            "Short codes are 7 characters long",
        ],
    },
    "planner": {
        "tasks": [
            {"id": "T1", "title": "Design the data model", "depends_on": []},
            {"id": "T2", "title": "Define the API contract", "depends_on": ["T1"]},
            {"id": "T3", "title": "Build the short code generator", "depends_on": ["T1"]},
            {"id": "T4", "title": "Build the storage layer", "depends_on": ["T1"]},
            {"id": "T5", "title": "Build the API endpoints", "depends_on": ["T2", "T3", "T4"]},
            {"id": "T6", "title": "Build click analytics", "depends_on": ["T4", "T5"]},
            {"id": "T7", "title": "Write unit tests", "depends_on": ["T3", "T4"]},
            {"id": "T8", "title": "Write integration tests", "depends_on": ["T5", "T6"]},
            {"id": "T9", "title": "Write documentation", "depends_on": ["T5", "T6"]},
        ],
    },
    "architect": {
        "components": [
            {"name": "API layer", "purpose": "Receives web requests and sends replies"},
            {"name": "Code generator", "purpose": "Creates unique short codes"},
            {"name": "Storage layer", "purpose": "Saves links and clicks in the database"},
            {"name": "Analytics", "purpose": "Records clicks and summarizes them"},
        ],
        "api": [
            {
                "method": "POST",
                "path": "/shorten",
                "purpose": "Create a short link",
                "request": {"url": "text", "expires_in_days": "number, optional"},
                "response": {"code": "text", "short_url": "text"},
            },
            {
                "method": "GET",
                "path": "/{code}",
                "purpose": "Send the visitor to the original URL",
                "request": {},
                "response": {"status": "302 redirect"},
            },
            {
                "method": "GET",
                "path": "/stats/{code}",
                "purpose": "Show click counts for a link",
                "request": {},
                "response": {"total_clicks": "number", "clicks_by_day": "list"},
            },
        ],
        "schema": {
            "links": {
                "id": "number, primary key",
                "code": "text, unique",
                "original_url": "text",
                "created_at": "date and time",
                "expires_at": "date and time, optional",
            },
            "clicks": {
                "id": "number, primary key",
                "link_id": "number, points to links.id",
                "clicked_at": "date and time",
                "referrer": "text, optional",
            },
        },
        "decisions": [
            {
                "choice": "Base62 encoding of the row id for short codes",
                "why": "Every id gives a different code, so no collisions",
                "tradeoff": "Codes can be guessed in order. A shuffle can be added later",
            },
            {
                "choice": "SQLite database for version one",
                "why": "Needs no setup, so anyone can run the project",
                "tradeoff": "Only one writer at a time. Move to PostgreSQL for real scale",
            },
            {
                "choice": "302 redirect instead of 301",
                "why": "Browsers do not cache it, so every click is counted",
                "tradeoff": "Slightly more load on the service",
            },
            {
                "choice": "Clicks stored in a separate table",
                "why": "Keeps the redirect fast and analytics queries simple",
                "tradeoff": "The table grows quickly and needs archiving later",
            },
        ],
    },
}


def ask_model(agent_name, prompt, use_mock=True):
    """Send a prompt to the model and get the reply back as text."""
    if use_mock:
        return json.dumps(MOCK_RESPONSES[agent_name])
    raise NotImplementedError("Real model call will be added later")