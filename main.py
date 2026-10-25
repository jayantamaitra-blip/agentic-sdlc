from src.orchestrator.state import new_state
from src.orchestrator.runner import Task, run_workflow

calls = {"count": 0}


def step_one(state):
    state["assumptions"].append("step one done")


def flaky_step(state):
    calls["count"] += 1
    if calls["count"] == 1:
        raise ValueError("pretend failure")
    state["tasks"].append("flaky step finally worked")


def step_three(state):
    state["summary"] = "all done"


state = new_state("demo requirement")
tasks = [
    Task("one", step_one),
    Task("two", flaky_step, depends_on=["one"]),
    Task("three", step_three, depends_on=["two"], needs_approval=True),
]
run_workflow(tasks, state)
print(state)