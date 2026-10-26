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
        "output_dir": "",
        "implementation_notes": {},
        "review": {},
        "code_review": {},
        "quality_rounds": 0,
        "repair_feedback": {},
        "repair_history": [],
        "repair_attempts": 0,
        "repair_loop_passed": False,
    }