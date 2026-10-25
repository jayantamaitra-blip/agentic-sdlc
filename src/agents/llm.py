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
}


def ask_model(agent_name, prompt, use_mock=True):
    """Send a prompt to the model and get the reply back as text."""
    if use_mock:
        return json.dumps(MOCK_RESPONSES[agent_name])
    raise NotImplementedError("Real model call will be added later")