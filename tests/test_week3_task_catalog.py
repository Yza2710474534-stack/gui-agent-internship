import tempfile
import unittest
from pathlib import Path

from src.week3_runtime import run_long_task
from src.week3_task_catalog import get_task_scenario, list_task_scenarios


class Week3TaskCatalogTests(unittest.TestCase):
    def test_catalog_has_five_different_workflows(self):
        scenarios = list_task_scenarios()
        self.assertEqual(len(scenarios), 5)
        self.assertEqual(len({item["category"] for item in scenarios}), 5)
        self.assertEqual(len({item["done_condition"] for item in scenarios}), 5)

    def test_each_workflow_has_multiple_steps(self):
        for scenario in list_task_scenarios():
            with self.subTest(scenario=scenario["scenario_id"]):
                self.assertGreaterEqual(len(scenario["steps"]), 4)
                self.assertTrue(scenario["done_condition"])

    def test_browser_search_is_real_and_other_workflows_are_labeled(self):
        self.assertEqual(get_task_scenario("browser_search")["execution_status"], "real_single_run")
        self.assertEqual(get_task_scenario("open_file")["execution_status"], "simulation_only")
        self.assertEqual(get_task_scenario("message_draft")["execution_status"], "simulation_only")

    def test_unknown_workflow_is_rejected(self):
        with self.assertRaises(ValueError):
            get_task_scenario("unknown")

    def test_all_workflows_run_through_long_task_state_machine(self):
        for scenario in list_task_scenarios():
            with self.subTest(scenario=scenario["scenario_id"]), tempfile.TemporaryDirectory() as directory:
                state = {
                    "task": scenario["instruction"], "status": "ready", "current_step": 0,
                    "steps": [
                        {"step_id": number, "description": text, "status": "pending"}
                        for number, text in enumerate(scenario["steps"], 1)
                    ],
                    "done_condition": scenario["done_condition"], "history": [],
                }
                result = run_long_task(
                    state,
                    lambda step: {"scenario": scenario["scenario_id"], "step_id": step["step_id"]},
                    lambda step, output: output["step_id"] == step["step_id"],
                    lambda final_state: len(final_state["history"]) == len(scenario["steps"]),
                    Path(directory) / "events.jsonl",
                )
                self.assertEqual(result["status"], "done")


if __name__ == "__main__":
    unittest.main()
