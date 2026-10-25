class Task:
    """One step in the workflow, like one stage in a pipeline."""

    def __init__(self, name, func, depends_on=None, needs_approval=False):
        self.name = name
        self.func = func
        self.depends_on = depends_on or []
        self.needs_approval = needs_approval


def ask_human(task_name):
    answer = input(f"Approve the result of '{task_name}'? (y/n): ")
    return answer.strip().lower() == "y"


def run_with_retries(task, state, max_retries):
    """Run one task. If it fails, try again up to max_retries times."""
    for attempt in range(1, max_retries + 2):
        try:
            print(f"  Running '{task.name}' (attempt {attempt})")
            task.func(state)
            return
        except Exception as error:
            print(f"  '{task.name}' failed: {error}")
            if attempt > max_retries:
                raise RuntimeError(f"'{task.name}' failed after {attempt} attempts")


def run_workflow(tasks, state, max_retries=2, approve=ask_human):
    names = {task.name for task in tasks}

    # Check up front that every dependency actually exists.
    for task in tasks:
        for dep in task.depends_on:
            if dep not in names:
                raise ValueError(f"'{task.name}' depends on unknown task '{dep}'")

    done = set()
    while len(done) < len(tasks):
        # Tasks that have not run yet and whose prerequisites are all finished.
        ready = [
            task for task in tasks
            if task.name not in done
            and all(dep in done for dep in task.depends_on)
        ]
        if not ready:
            raise RuntimeError("No task can run. Check for circular dependencies.")

        for task in ready:
            run_with_retries(task, state, max_retries)
            if task.needs_approval and not approve(task.name):
                raise RuntimeError(f"Human rejected '{task.name}'")
            done.add(task.name)