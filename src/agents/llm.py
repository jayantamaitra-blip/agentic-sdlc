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
}


def ask_model(agent_name, prompt, use_mock=True):
    """Send a prompt to the model and get the reply back as text."""
    if use_mock:
        return json.dumps(MOCK_RESPONSES[agent_name])
    raise NotImplementedError("Real model call will be added later")