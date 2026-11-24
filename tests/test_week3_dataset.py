"""第三周第一天测试，不访问网络。"""

import json
from pathlib import Path
import tempfile
import unittest

from src.week3_dataset import (
    detect_source, load_records, normalize_mind2web, normalize_screenagent,
    normalize_webarena, preprocess,
)
from scripts.week3_kaggle_full_preprocess import write_screenagent


class Week3DatasetTests(unittest.TestCase):
    def setUp(self):
        self.sample = {
            "task_id": 2,
            "sites": ["misc"],
            "intent": "Check out the classification section",
            "start_url": "https://example.test/start",
            "reference_action_sequence": {
                "action_sequence": ["click Classification", "stop"]
            },
            "eval": {"eval_types": ["url_match"], "reference_url": "https://example.test/#two"},
        }

    def test_normalize_fields(self):
        result = normalize_webarena(self.sample)
        self.assertEqual(result["task_id"], "webarena_2")
        self.assertEqual(result["instruction"], self.sample["intent"])
        self.assertEqual(result["steps"][0], {"step_id": 1, "action_text": "click Classification"})
        self.assertEqual(result["evaluation"]["types"], ["url_match"])

    def test_input_is_not_modified(self):
        original = json.loads(json.dumps(self.sample))
        normalize_webarena(self.sample)
        self.assertEqual(self.sample, original)

    def test_missing_or_invalid_fields(self):
        for change in ({"intent": ""}, {"sites": "misc"}):
            bad = {**self.sample, **change}
            with self.assertRaises(ValueError):
                normalize_webarena(bad)
        bad = self.sample.copy()
        bad.pop("task_id")
        with self.assertRaises(ValueError):
            normalize_webarena(bad)

    def test_preprocess_writes_one_json_line(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            output = Path(directory) / "output.jsonl"
            source.write_text(json.dumps(self.sample), encoding="utf-8")
            records = preprocess(source, output)
            self.assertEqual(len(records), 1)
            self.assertEqual(len(output.read_text(encoding="utf-8").splitlines()), 1)

    def test_bad_json_reports_line(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.json"
            source.write_text("{\nwrong", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "第2行"):
                load_records(source)

    def test_screenagent_fields(self):
        sample = {"session_id": "abc", "task_prompt": "打开浏览器",
                  "video_width": 1024, "video_height": 768, "saved_image_name": "one.jpg",
                  "actions": [{"action_type": "PlanAction", "element": "点击浏览器"}]}
        result = normalize_screenagent(sample)
        self.assertEqual(result["source_dataset"], "screenagent")
        self.assertEqual(result["environment"]["image_size"], [1024, 768])
        self.assertEqual(result["steps"][0]["action_type"], "PlanAction")

    def test_screenagent_files_get_unique_task_ids(self):
        sample = {"session_id": "same", "task_prompt": "打开浏览器",
                  "actions": [{"action_type": "PlanAction", "element": "点击浏览器"}]}
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            (source / "a").mkdir(parents=True)
            (source / "b").mkdir(parents=True)
            for folder in ("a", "b"):
                (source / folder / "one_translate.json").write_text(
                    json.dumps(sample), encoding="utf-8")
            output = Path(directory) / "screenagent.jsonl"
            write_screenagent(source, output)
            task_ids = [json.loads(line)["task_id"] for line in output.read_text(
                encoding="utf-8").splitlines()]
            self.assertEqual(len(task_ids), len(set(task_ids)))

    def test_mind2web_drops_html_and_keeps_operations(self):
        sample = {"annotation_id": "xyz", "confirmed_task": "选择取餐", "website": "demo",
                  "action_reprs": ["SELECT: Pickup"], "actions": [{"action_uid": "a1",
                  "raw_html": "very large html", "operation": {"op": "SELECT", "value": "Pickup"}}]}
        result = normalize_mind2web(sample)
        self.assertNotIn("raw_html", json.dumps(result))
        self.assertEqual(result["steps"][0]["action_value"], "Pickup")

    def test_detect_three_sources(self):
        self.assertEqual(detect_source(self.sample), "webarena")
        self.assertEqual(detect_source({"session_id": "1", "task_prompt": "x"}), "screenagent")
        self.assertEqual(detect_source({"annotation_id": "1", "confirmed_task": "x"}), "mind2web")

    def test_huggingface_rows_wrapper(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "rows.json"
            source.write_text(json.dumps({"rows": [{"row": self.sample}]}), encoding="utf-8")
            self.assertEqual(load_records(source), [self.sample])

    def test_unknown_source(self):
        with self.assertRaisesRegex(ValueError, "无法判断"):
            detect_source({"name": "unknown"})


if __name__ == "__main__":
    unittest.main()
