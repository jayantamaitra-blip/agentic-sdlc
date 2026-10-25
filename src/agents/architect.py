import json
from src.agents.llm import ask_model

REQUIRED_PARTS = ["components", "api", "schema", "decisions"]


def check_design(design):
    """Guardrail: stop early if the design is missing something important."""
    for part in REQUIRED_PARTS:
        if part not in design or not design[part]:
            raise ValueError(f"Design is missing '{part}'")

    for endpoint in design["api"]:
        if "method" not in endpoint or "path" not in endpoint:
            raise ValueError(f"API endpoint is incomplete: {endpoint}")

    for decision in design["decisions"]:
        if "tradeoff" not in decision:
            raise ValueError(f"Decision has no trade-off: {decision['choice']}")


def design_system(state):
    """Design the components, API, database tables and key decisions."""
    prompt = (
        "Design the system for this requirement. Reply in JSON with the "
        "keys 'components', 'api', 'schema' and 'decisions'. Every decision "
        "needs a 'choice', a 'why' and a 'tradeoff'.\n\n"
        f"Requirement: {state['requirement']}\n"
        f"Assumptions: {state['assumptions']}\n"
        f"Tasks: {state['tasks']}"
    )
    reply = ask_model("architect", prompt)
    design = json.loads(reply)

    check_design(design)
    state["design"] = design