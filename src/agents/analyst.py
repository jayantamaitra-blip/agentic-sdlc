import json
from src.agents.llm import ask_model


def analyze_requirement(state):
    """Find unclear points in the requirement and note our assumptions."""
    prompt = (
        "Read this software requirement. List the unclear points and the "
        "sensible assumptions you would make. Reply in JSON with the keys "
        "'ambiguities' and 'assumptions'.\n\n"
        f"Requirement: {state['requirement']}"
    )
    reply = ask_model("analyst", prompt)
    result = json.loads(reply)

    state["ambiguities"] = result["ambiguities"]
    state["assumptions"] = result["assumptions"]