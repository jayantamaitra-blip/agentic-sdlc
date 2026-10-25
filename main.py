from src.orchestrator.state import new_state
from src.orchestrator.runner import Task, run_workflow
from src.agents.analyst import analyze_requirement
from src.agents.planner import plan_tasks
from src.agents.architect import design_system

REQUIREMENT = (
    "Build a scalable URL shortener service with APIs, "
    "persistence, and analytics."
)

state = new_state(REQUIREMENT)

tasks = [
    Task("analyze", analyze_requirement, needs_approval=True),
    Task("plan", plan_tasks, depends_on=["analyze"], needs_approval=True),
    Task("design", design_system, depends_on=["plan"], needs_approval=True),
]

run_workflow(tasks, state)

design = state["design"]

print("\nComponents:")
for part in design["components"]:
    print(f" - {part['name']}: {part['purpose']}")

print("\nAPI endpoints:")
for endpoint in design["api"]:
    print(f" - {endpoint['method']} {endpoint['path']}: {endpoint['purpose']}")

print("\nDatabase tables:")
for table, columns in design["schema"].items():
    print(f" - {table}: {', '.join(columns)}")

print("\nKey decisions:")
for decision in design["decisions"]:
    print(f" - {decision['choice']}")
    print(f"     Trade-off: {decision['tradeoff']}")