"""第三周批处理测试。"""

import json
from pathlib import Path
import tempfile
import unittest

from src.week3_batch import action_name, choose_split, split_and_report, validate


def sample(task_id="one"):
    return {"source_dataset": "webarena", "task_id": task_id, "instruction": "打开页面",
            "environment": {}, "steps": [{"step_id": 1, "action_text": "button.click()"}],
            "evaluation": {}}


class Week3BatchTests(unittest.TestCase):
    def test_validate_good_and_missing_field(self):
        self.assertEqual(validate(sample()), "")
        bad = sample()
        bad.pop("instruction")
        self.assertEqual(validate(bad), "缺少字段：instruction")

    def test_step_numbers_must_be_continuous(self):
        record = sample()
        record["steps"][0]["step_id"] = 2
        self.assertIn("第1步", validate(record))

    def test_split_is_stable(self):
        first = choose_split("same-task")
        self.assertEqual(first, choose_split("same-task"))
        with self.assertRaises(ValueError):
            choose_split("x", 0)

    def test_action_text_classification(self):
        self.assertEqual(action_name({"action_text": "page.click()"}), "CLICK")
        self.assertEqual(action_name({"action_text": "page.fill('x')"}), "TYPE")
        self.assertEqual(action_name({"action_type": "SELECT"}), "SELECT")

    def test_batch_writes_splits_stats_and_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.jsonl"
            source.write_text("\n".join((json.dumps(sample("one"), ensure_ascii=False),
                                         json.dumps(sample("two"), ensure_ascii=False),
                                         json.dumps(sample("one"), ensure_ascii=False), "bad json")), encoding="utf-8")
            report = split_and_report([source], root / "out", 20)
            self.assertEqual(report["total_records"], 4)
            self.assertEqual(report["valid_records"], 2)
            self.assertEqual(report["invalid_records"], 2)
            self.assertEqual(report["action_counts"], {"CLICK": 2})
            self.assertTrue((root / "out/statistics.json").is_file())


if __name__ == "__main__":
    unittest.main()
