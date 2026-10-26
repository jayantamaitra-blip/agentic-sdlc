import json
from src.agents.llm import ask_model
from src.orchestrator.graph import check_task_graph


def plan_tasks(state):
    """Break the requirement into tasks and work out the run order."""
    prompt = (
        "Break this requirement into small engineering tasks. Reply in JSON "
        "with a 'tasks' list. Each task needs an 'id', a 'title' and a "
        "'depends_on' list of task ids.\n\n"
        f"Requirement: {state['requirement']}\n"
        f"Assumptions: {state['assumptions']}\n"
        f"Approved design: {state['design']}"
    )
    reply = ask_model("planner", prompt)
    tasks = json.loads(reply)["tasks"]

    waves = check_task_graph(tasks)

    state["tasks"] = tasks
    state["waves"] = waves