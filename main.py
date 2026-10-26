from src.orchestrator.state import new_state
from src.orchestrator.runner import Task, run_workflow
from src.agents.analyst import analyze_requirement
from src.agents.architect import design_system
from src.agents.planner import plan_tasks
from src.agents.coder import implement, repair_implementation
from src.agents.tester import run_tests
from src.orchestrator.repair_loop import run_test_repair_loop
from src.agents.reviewer import inspect_code, review_output

REQUIREMENT = (
    "Build a scalable URL shortener service with APIs, "
    "persistence, and analytics."
)

state = new_state(REQUIREMENT)

def validate_and_repair(workflow_state):
    run_test_repair_loop(
        workflow_state,
        test_func=run_tests,
        repair_func=repair_implementation,
        max_repairs=2,
        review_func=inspect_code,
    )

tasks = [
    Task("analyze", analyze_requirement, needs_approval=True),
    Task("design", design_system, depends_on=["analyze"], needs_approval=True),
    Task("plan", plan_tasks, depends_on=["design"], needs_approval=True),
    Task("implement", implement, depends_on=["plan"], needs_approval=True),
    Task("validate_and_repair", validate_and_repair, depends_on=["implement"]),
    Task("review", review_output, depends_on=["validate_and_repair"]),
]

run_workflow(tasks, state)

print("\nFinal engineering summary:")
print(state["summary"])
print(f"\nGenerated project: {state['output_dir']}")
print(f"Repair attempts: {state.get('repair_attempts', 0)}")
print(f"Validation/review rounds: {state.get('quality_rounds', 0)}")
print(f"Validation loop passed: {state.get('repair_loop_passed', False)}")
print("\nPlanned tasks:")
for task in state["tasks"]:
    print(f" - {task['id']}: {task['title']} (depends on: {task['depends_on']})")
print("\nDesign decisions:")
for decision in state["design"]["decisions"]:
    print(f" - {decision['choice']}: {decision['tradeoff']}")
