"""Run the generated project's tests and preserve the real test output."""
import subprocess
import sys
from pathlib import Path


def run_tests(state):
    output_dir = state.get("output_dir")
    if not output_dir:
        raise ValueError("Tester requires generated code")
    project_dir = Path(output_dir).resolve()
    test_dir = project_dir / "tests"
    if not test_dir.is_dir():
        raise ValueError(f"Test directory not found: {test_dir}")

    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=project_dir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
        check=False,
    )
    state["test_results"] = {
        "command": "python -m unittest discover -s tests -v",
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "output": completed.stdout,
    }
    print(completed.stdout)
    if completed.returncode != 0:
        print("Generated project tests failed; the Reviewer will record this outcome.")
