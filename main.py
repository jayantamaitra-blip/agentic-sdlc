from src.orchestrator.state import new_state
from src.orchestrator.runner import Task, run_workflow
from src.agents.analyst import analyze_requirement

REQUIREMENT = (
    "Build a scalable URL shortener service with APIs, "
    "persistence, and analytics."
)

state = new_state(REQUIREMENT)

tasks = [
    Task("analyze", analyze_requirement, needs_approval=True),
]

run_workflow(tasks, state)

print("\nUnclear points:")
for item in state["ambiguities"]:
    print(" -", item)

print("\nAssumptions:")
for item in state["assumptions"]:
    print(" -", item)