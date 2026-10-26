"""Bounded test -> code-review -> repair loop for the engineering workflow."""
from copy import deepcopy


def run_test_repair_loop(state, test_func, repair_func, max_repairs=2, review_func=None):
    """Run at most max_repairs + 1 validation rounds.

    Every round executes tests and, when supplied, a source-code review. A
    failed test run OR failed code review sends the actual diagnostics back to
    the Coder. With max_repairs=2 this allows three total validation rounds and
    at most two repair attempts.
    """
    if max_repairs < 0:
        raise ValueError("max_repairs must be non-negative")

    state.setdefault("repair_history", [])
    attempts_used = 0
    for attempt in range(max_repairs + 1):
        round_number = attempt + 1
        print(f"\nValidation/review round {round_number}/{max_repairs + 1}")
        test_func(state)
        test_result = state.get("test_results", {})
        review_result = review_func(state) if review_func else {"passed": True, "findings": []}

        tests_passed = bool(test_result.get("passed"))
        review_passed = bool(review_result.get("passed"))
        if tests_passed and review_passed:
            state["repair_attempts"] = attempts_used
            state["repair_loop_passed"] = True
            state["quality_rounds"] = round_number
            return state

        if attempt == max_repairs:
            break

        review_findings = review_result.get("findings", [])
        feedback = {
            "attempt": round_number,
            "command": test_result.get("command", ""),
            "returncode": test_result.get("returncode"),
            "tests_passed": tests_passed,
            "test_output": test_result.get("output", "No diagnostic output was captured."),
            "review_passed": review_passed,
            "review_findings": deepcopy(review_findings),
        }
        # Keep a combined, readable diagnostic for simple repair implementations,
        # while preserving structured fields for a future model-driven Coder.
        feedback["output"] = feedback["test_output"]
        if review_findings:
            feedback["output"] += "\nCode review findings:\n" + "\n".join(
                f"[{item.get('severity', 'unknown')}] {item.get('file', '')}: {item.get('message', '')}"
                for item in review_findings
            )
        state["repair_feedback"] = deepcopy(feedback)
        state["repair_history"].append({
            **feedback,
            "action": "repair requested",
        })
        attempts_used += 1
        print("Validation or code review failed; sending diagnostics to the Coder.")
        repair_func(state)

    state["repair_attempts"] = attempts_used
    state["repair_loop_passed"] = False
    state["quality_rounds"] = max_repairs + 1
    return state
