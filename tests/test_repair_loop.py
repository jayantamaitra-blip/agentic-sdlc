import unittest
from src.orchestrator.repair_loop import run_test_repair_loop


class RepairLoopTests(unittest.TestCase):
    def test_passes_without_repair_when_first_test_passes(self):
        state = {"test_results": {}, "repair_history": []}
        calls = {"test": 0, "repair": 0}

        def tester(current):
            calls["test"] += 1
            current["test_results"] = {"passed": True, "output": "OK", "returncode": 0}

        def repair(_current):
            calls["repair"] += 1

        run_test_repair_loop(state, tester, repair, max_repairs=2)
        self.assertEqual(calls, {"test": 1, "repair": 0})
        self.assertTrue(state["repair_loop_passed"])
        self.assertEqual(state["repair_attempts"], 0)

    def test_retries_after_failure_and_passes_after_repair(self):
        state = {"test_results": {}, "repair_history": []}
        calls = {"test": 0, "repair": 0}

        def tester(current):
            calls["test"] += 1
            passed = calls["test"] >= 2
            current["test_results"] = {
                "passed": passed,
                "output": "OK" if passed else "AssertionError: expected 2, got 1",
                "returncode": 0 if passed else 1,
            }

        def repair(current):
            calls["repair"] += 1
            self.assertIn("AssertionError", current["repair_feedback"]["output"])

        run_test_repair_loop(state, tester, repair, max_repairs=2)
        self.assertEqual(calls, {"test": 2, "repair": 1})
        self.assertTrue(state["repair_loop_passed"])
        self.assertEqual(state["repair_attempts"], 1)

    def test_stops_after_repair_budget_and_preserves_failure(self):
        state = {"test_results": {}, "repair_history": []}
        calls = {"test": 0, "repair": 0}

        def tester(current):
            calls["test"] += 1
            current["test_results"] = {
                "passed": False, "output": "still failing", "returncode": 1
            }

        def repair(_current):
            calls["repair"] += 1

        run_test_repair_loop(state, tester, repair, max_repairs=2)
        self.assertEqual(calls, {"test": 3, "repair": 2})
        self.assertFalse(state["repair_loop_passed"])
        self.assertEqual(state["repair_attempts"], 2)
        self.assertEqual(state["test_results"]["output"], "still failing")

    def test_code_review_failure_also_triggers_repair_and_re_review(self):
        state = {"test_results": {}, "repair_history": []}
        calls = {"test": 0, "review": 0, "repair": 0}

        def tester(current):
            calls["test"] += 1
            current["test_results"] = {"passed": True, "output": "OK", "returncode": 0}

        def reviewer(_current):
            calls["review"] += 1
            passed = calls["review"] >= 2
            return {"passed": passed, "findings": [] if passed else [
                {"severity": "high", "file": "shortener.py", "message": "Missing validation"}
            ]}

        def repair(current):
            calls["repair"] += 1
            self.assertIn("Missing validation", current["repair_feedback"]["output"])

        run_test_repair_loop(state, tester, repair, max_repairs=2, review_func=reviewer)
        self.assertEqual(calls, {"test": 2, "review": 2, "repair": 1})
        self.assertTrue(state["repair_loop_passed"])
        self.assertEqual(state["quality_rounds"], 2)

    def test_stops_after_three_total_review_rounds(self):
        state = {"test_results": {}, "repair_history": []}
        calls = {"test": 0, "review": 0, "repair": 0}

        def tester(current):
            calls["test"] += 1
            current["test_results"] = {"passed": True, "output": "OK", "returncode": 0}

        def reviewer(_current):
            calls["review"] += 1
            return {"passed": False, "findings": [{"severity": "high", "file": "shortener.py", "message": "Issue"}]}

        def repair(_current):
            calls["repair"] += 1

        run_test_repair_loop(state, tester, repair, max_repairs=2, review_func=reviewer)
        self.assertEqual(calls, {"test": 3, "review": 3, "repair": 2})
        self.assertFalse(state["repair_loop_passed"])
        self.assertEqual(state["quality_rounds"], 3)

    def test_rejects_negative_repair_budget(self):
        with self.assertRaises(ValueError):
            run_test_repair_loop({}, lambda _s: None, lambda _s: None, max_repairs=-1)


if __name__ == "__main__":
    unittest.main()
