"""Inspect generated source code and summarize engineering quality."""
import ast
from pathlib import Path


DANGEROUS_CALLS = {"eval", "exec", "compile"}
REQUIRED_SOURCE_SYMBOLS = {"URLShortener", "make_handler"}
REQUIRED_TESTS = {
    "test_create_and_resolve_link",
    "test_invalid_url_is_rejected",
    "test_redirect_resolution_records_analytics",
}


def inspect_code(state):
    """Perform lightweight, deterministic source-code review.

    This is a useful prototype review, not a substitute for a human security
    review or a full static-analysis tool. Findings include file and line where
    available so they can be passed back to the Coder.
    """
    findings = []
    files = state.get("code_files", {})
    source_path = files.get("shortener.py")
    tests_path = files.get("tests/test_shortener.py")

    if not source_path or not Path(source_path).is_file():
        findings.append({
            "severity": "high", "file": "shortener.py", "line": None,
            "message": "Implementation source is missing; cannot review code.",
        })
        state["code_review"] = {"passed": False, "findings": findings}
        return state["code_review"]

    source_path = Path(source_path)
    source = source_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError as error:
        findings.append({
            "severity": "high", "file": "shortener.py", "line": error.lineno,
            "message": f"Python syntax error: {error.msg}",
        })
        state["code_review"] = {"passed": False, "findings": findings}
        return state["code_review"]

    defined_symbols = {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    for symbol in sorted(REQUIRED_SOURCE_SYMBOLS - defined_symbols):
        findings.append({
            "severity": "high", "file": "shortener.py", "line": None,
            "message": f"Expected implementation symbol '{symbol}' is missing.",
        })

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_CALLS:
                findings.append({
                    "severity": "high", "file": "shortener.py", "line": node.lineno,
                    "message": f"Avoid dynamic code execution via {node.func.id}().",
                })
            if isinstance(node.func, ast.Attribute) and node.func.attr == "execute":
                if node.args and isinstance(node.args[0], ast.JoinedStr):
                    findings.append({
                        "severity": "high", "file": "shortener.py", "line": node.lineno,
                        "message": "SQL query uses an f-string; use parameterized SQL instead.",
                    })
            if isinstance(node.func, ast.Attribute) and node.func.attr == "run":
                for keyword in node.keywords:
                    if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                        findings.append({
                            "severity": "high", "file": "shortener.py", "line": node.lineno,
                            "message": "subprocess.run(shell=True) can enable command injection.",
                        })

    # URL validation is a core safety requirement for a URL shortener.
    if "parsed.scheme not in (\"http\", \"https\")" not in source and "parsed.scheme not in ('http', 'https')" not in source:
        findings.append({
            "severity": "high", "file": "shortener.py", "line": None,
            "message": "Could not find explicit HTTP/HTTPS URL scheme validation.",
        })

    if not tests_path or not Path(tests_path).is_file():
        findings.append({
            "severity": "medium", "file": "tests/test_shortener.py", "line": None,
            "message": "Test file is missing.",
        })
    else:
        test_source = Path(tests_path).read_text(encoding="utf-8")
        try:
            ast.parse(test_source, filename=str(tests_path))
        except SyntaxError as error:
            findings.append({
                "severity": "high", "file": "tests/test_shortener.py", "line": error.lineno,
                "message": f"Test file has a Python syntax error: {error.msg}",
            })
        for test_name in sorted(REQUIRED_TESTS):
            if test_name not in test_source:
                findings.append({
                    "severity": "medium", "file": "tests/test_shortener.py", "line": None,
                    "message": f"Core behavior lacks an expected test: {test_name}.",
                })

    result = {"passed": not findings, "findings": findings}
    state["code_review"] = result
    print(f"Code review: {'PASSED' if result['passed'] else 'FINDINGS'} ({len(findings)} finding(s))")
    for finding in findings:
        location = f"{finding['file']}:{finding['line']}" if finding.get("line") else finding["file"]
        print(f" - [{finding['severity']}] {location}: {finding['message']}")
    return result


def review_output(state):
    """Produce the final review and engineering summary after the repair loop."""
    code_review = inspect_code(state)
    findings = list(code_review["findings"])
    files = state.get("code_files", {})
    for name, path in files.items():
        if not Path(path).is_file():
            findings.append({
                "severity": "high", "file": name, "line": None,
                "message": f"Artifact does not exist: {path}",
            })

    test_results = state.get("test_results", {})
    if not test_results:
        findings.append({"severity": "high", "file": "tests", "line": None,
                         "message": "Tests were not executed."})
    elif not test_results.get("passed"):
        findings.append({"severity": "high", "file": "tests", "line": None,
                         "message": "Generated project tests did not pass."})

    design = state.get("design", {})
    if not design.get("api") or not design.get("schema"):
        findings.append({"severity": "medium", "file": "design", "line": None,
                         "message": "Design does not document both API and persistence schema."})

    state["risks"] = [
        "Static code review uses targeted checks; it is not a complete security audit.",
        "Prototype does not include authentication or rate limiting.",
        "SQLite is suitable for a local demo but may need replacement for high write throughput.",
    ]
    state["review"] = {"passed": not findings, "findings": findings}
    state["summary"] = (
        "Engineering workflow completed. "
        f"Artifacts: {len(files)}. "
        f"Tests: {'PASSED' if test_results.get('passed') else 'FAILED/NOT RUN'}. "
        f"Code review: {'PASSED' if code_review['passed'] else 'NEEDS ATTENTION'}. "
        f"Overall review: {'PASSED' if not findings else 'NEEDS ATTENTION'}. "
        f"Repair attempts: {state.get('repair_attempts', 0)}."
    )
    print("\nFinal review:")
    print(state["summary"])
    for finding in findings:
        location = f"{finding['file']}:{finding['line']}" if finding.get("line") else finding["file"]
        print(f" - [{finding['severity']}] {location}: {finding['message']}")
    print("Known risks:")
    for risk in state["risks"]:
        print(f" - {risk}")
    return state["review"]
