import unittest

from src.orchestrator.graph import check_task_graph
from src.orchestrator.runner import Task, run_workflow
from src.orchestrator.state import new_state


def approve_all(task_name):
    return True


class RunnerTests(unittest.TestCase):
    def test_tasks_run_in_dependency_order(self):
        order = []
        tasks = [
            Task("c", lambda s: order.append("c"), depends_on=["b"]),
            Task("b", lambda s: order.append("b"), depends_on=["a"]),
            Task("a", lambda s: order.append("a")),
        ]
        run_workflow(tasks, new_state("demo"), approve=approve_all)
        self.assertEqual(order, ["a", "b", "c"])

    def test_failed_task_is_retried(self):
        calls = {"count": 0}

        def flaky(state):
            calls["count"] += 1
            if calls["count"] == 1:
                raise ValueError("first attempt fails")

        run_workflow([Task("flaky", flaky)], new_state("demo"), approve=approve_all)
        self.assertEqual(calls["count"], 2)

    def test_gives_up_after_max_retries(self):
        def always_fails(state):
            raise ValueError("always")

        with self.assertRaises(RuntimeError):
            run_workflow(
                [Task("bad", always_fails)], new_state("demo"),
                max_retries=1, approve=approve_all,
            )

    def test_human_rejection_stops_workflow(self):
        tasks = [Task("gate", lambda s: None, needs_approval=True)]
        with self.assertRaises(RuntimeError):
            run_workflow(tasks, new_state("demo"), approve=lambda name: False)

    def test_unknown_dependency_is_rejected(self):
        tasks = [Task("a", lambda s: None, depends_on=["missing"])]
        with self.assertRaises(ValueError):
            run_workflow(tasks, new_state("demo"), approve=approve_all)


class TaskGraphTests(unittest.TestCase):
    def test_waves_group_independent_tasks(self):
        tasks = [
            {"id": "T1", "depends_on": []},
            {"id": "T2", "depends_on": ["T1"]},
            {"id": "T3", "depends_on": ["T1"]},
        ]
        self.assertEqual(check_task_graph(tasks), [["T1"], ["T2", "T3"]])

    def test_circular_dependency_is_rejected(self):
        tasks = [
            {"id": "T1", "depends_on": ["T2"]},
            {"id": "T2", "depends_on": ["T1"]},
        ]
        with self.assertRaises(ValueError):
            check_task_graph(tasks)

    def test_duplicate_ids_are_rejected(self):
        tasks = [
            {"id": "T1", "depends_on": []},
            {"id": "T1", "depends_on": []},
        ]
        with self.assertRaises(ValueError):
            check_task_graph(tasks)


if __name__ == "__main__":
    unittest.main()