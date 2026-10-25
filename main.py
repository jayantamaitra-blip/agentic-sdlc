from src.orchestrator.state import new_state
from src.orchestrator.runner import Task, run_workflow
from src.agents.analyst import analyze_requirement
from src.agents.planner import plan_tasks

REQUIREMENT = (
    "Build a scalable URL shortener service with APIs, "
    "persistence, and analytics."
)

state = new_state(REQUIREMENT)

tasks = [
    Task("analyze", analyze_requirement, needs_approval=True),
    Task("plan", plan_tasks, depends_on=["analyze"], needs_approval=True),
]

run_workflow(tasks, state)

print("\nAssumptions:")
for item in state["assumptions"]:
    print(" -", item)

print("\nExecution plan:")
titles = {task["id"]: task["title"] for task in state["tasks"]}
for number, wave in enumerate(state["waves"], start=1):
    print(f" Wave {number}:")
    for tid in wave:
        print(f"   {tid}: {titles[tid]}")