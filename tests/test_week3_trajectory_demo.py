import json
import tempfile
import unittest
from pathlib import Path

from src.week3_trajectory_demo import read_tasks, run_demo, simulate_task


def sample_record(source="webarena", task_id="task_1"):
    return {
        "source_dataset": source,
        "task_id": task_id,
        "instruction": "点击编辑菜单",
        "environment": {},
        "steps": [{"step_id": 1, "action_text": "click edit"}],
        "evaluation": {},
    }


class Week3TrajectoryDemoTests(unittest.TestCase):
    def test_read_tasks_respects_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.jsonl"
            records = [sample_record(task_id=f"task_{index}") for index in range(3)]
            path.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in records),
                encoding="utf-8",
            )
            result = read_tasks([path], max_records=2)
        self.assertEqual(len(result), 2)

    def test_bad_record_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.jsonl"
            path.write_text('{"task_id":"missing-fields"}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                read_tasks([path])

    def test_simulation_finishes_without_desktop_action(self):
        result = simulate_task(sample_record())
        self.assertEqual(result["execution_mode"], "offline_simulation")
        self.assertEqual(result["agent_state"]["status"], "done")
        self.assertTrue(result["agent_state"]["history"])

    def test_run_demo_saves_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "tasks.jsonl"
            output_path = Path(directory) / "result.json"
            input_path.write_text(
                json.dumps(sample_record("mind2web"), ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            result = run_demo([input_path], output_path, max_records=1)
            saved = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(result["summary"]["completed_tasks"], 1)
        self.assertEqual(saved["summary"]["real_desktop_actions"], 0)

    def test_invalid_limit_is_rejected(self):
        with self.assertRaises(ValueError):
            read_tasks([], max_records=0)


if __name__ == "__main__":
    unittest.main()
