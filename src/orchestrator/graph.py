def execution_waves(tasks):
    """Group tasks into waves. Tasks in the same wave can run together."""
    remaining = {task["id"]: set(task["depends_on"]) for task in tasks}
    done = set()
    waves = []

    while remaining:
        wave = [tid for tid, deps in remaining.items() if deps <= done]
        if not wave:
            raise ValueError("Circular dependency between tasks")
        waves.append(wave)
        done.update(wave)
        for tid in wave:
            del remaining[tid]

    return waves


def check_task_graph(tasks):
    """Make sure the plan is valid, and return its waves."""
    ids = [task["id"] for task in tasks]

    if len(ids) != len(set(ids)):
        raise ValueError("Two tasks share the same id")

    for task in tasks:
        for dep in task["depends_on"]:
            if dep not in ids:
                raise ValueError(f"{task['id']} depends on unknown task {dep}")

    return execution_waves(tasks)