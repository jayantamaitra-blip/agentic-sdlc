def new_state(requirement):
    """Create the shared notebook that every agent reads from and writes to."""
    return {
        "requirement": requirement,
        "ambiguities": [],
        "assumptions": [],
        "tasks": [],
        "waves": [],
        "design": {},
        "code_files": {},
        "test_results": {},
        "risks": [],
        "summary": "",
    }