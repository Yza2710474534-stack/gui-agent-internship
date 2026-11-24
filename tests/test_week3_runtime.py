import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from src.week3_runtime import (
    run_long_task,
    verify_search_results_ocr,
    verify_saved_desktop_step,
    verify_screenshot_target,
)


def long_state(step_count=6):
    return {
        "task": "打开浏览器，搜索 GUI Agent，并检查结果",
        "status": "ready",
        "current_step": 0,
        "steps": [
            {"step_id": number, "description": f"长任务第 {number} 步", "status": "pending"}
            for number in range(1, step_count + 1)
        ],
        "done_condition": "结果页出现 GUI Agent",
        "history": [],
    }


class Week3RuntimeTests(unittest.TestCase):
    def run_in_temp(self, state, execute, verify, complete, **options):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        log_path = Path(directory.name) / "runtime.jsonl"
        result = run_long_task(
            state, execute, verify, complete, log_path, **options
        )
        logs = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
        return result, logs

    def test_six_step_task_collects_structured_logs_and_completes(self):
        result, logs = self.run_in_temp(
            long_state(),
            lambda step: {"clicked": step["step_id"]},
            lambda step, output: {"success": output["clicked"] == step["step_id"],
                                  "message": "画面符合预期"},
            lambda state: {"success": len(state["history"]) == 6,
                           "message": "结果页包含目标关键词"},
        )
        self.assertEqual(result["status"], "done")
        self.assertEqual(result["action_count"], 6)
        self.assertEqual(len(result["history"]), 6)
        self.assertEqual(logs[0]["event"], "task_started")
        self.assertEqual(logs[-1]["event"], "task_completed")

    def test_failed_step_retries_then_recovers(self):
        calls = {"count": 0}

        def verify(step, output):
            calls["count"] += 1
            return {"success": calls["count"] >= 2, "message": "第二次画面才符合预期"}

        result, logs = self.run_in_temp(
            long_state(1), lambda step: {}, verify, lambda state: True, max_retries=2
        )
        self.assertEqual(result["status"], "done")
        self.assertEqual(result["action_count"], 2)
        self.assertIn("retry_scheduled", [item["event"] for item in logs])

    def test_exception_is_retried_and_can_recover(self):
        calls = {"count": 0}

        def execute(step):
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("模拟窗口短暂消失")
            return {"visible": True}

        result, _ = self.run_in_temp(
            long_state(1), execute,
            lambda step, output: output["visible"], lambda state: True,
        )
        self.assertEqual(result["status"], "done")
        self.assertEqual(result["history"][0]["evidence"]["error_type"], "RuntimeError")

    def test_retry_exhaustion_stops_remaining_steps(self):
        result, logs = self.run_in_temp(
            long_state(3), lambda step: {}, lambda step, output: False,
            lambda state: True, max_retries=1,
        )
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["current_step"], 0)
        self.assertEqual(len(result["history"]), 2)
        self.assertEqual(logs[-1]["event"], "task_failed")

    def test_steps_pass_but_completion_check_fails(self):
        result, _ = self.run_in_temp(
            long_state(2), lambda step: {}, lambda step, output: True,
            lambda state: {"success": False, "message": "结果页没有目标关键词"},
        )
        self.assertEqual(result["status"], "completion_failed")
        self.assertEqual(result["failure_reason"], "结果页没有目标关键词")

    def test_max_action_guard_stops_runaway_retry(self):
        result, _ = self.run_in_temp(
            long_state(1), lambda step: {}, lambda step, output: False,
            lambda state: True, max_retries=10, max_actions=3,
        )
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["failure_reason"], "超过最大动作次数")

    def test_real_saved_screenshot_single_step_is_verified(self):
        run_dir = Path("output/demo/20260910_201203_070856")
        result = verify_saved_desktop_step(run_dir)
        self.assertTrue(result["success"], result["message"])
        self.assertEqual(result["evidence"]["proposed_action"],
                         {"type": "click", "x": 184, "y": 16})
        self.assertEqual(result["evidence"]["visual_feedback"]["status"],
                         "menu_likely_open")

    def test_screenshot_size_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "screen.png"
            cv2.imwrite(str(path), np.zeros((20, 30, 3), dtype=np.uint8))
            result = verify_screenshot_target(
                path, {"image_size": [300, 200], "items": []}, "编辑", [0, 0, 30, 20]
            )
        self.assertFalse(result["success"])
        self.assertIn("尺寸", result["message"])

    def test_real_chrome_search_screenshot_meets_done_condition(self):
        result = verify_search_results_ocr(
            "output/screenshots/screen_1_20260919_171319_864597.png",
            "output/ocr/ocr_20260919_171420_361782.json",
            "GUI Agent",
        )
        self.assertTrue(result["success"], result["message"])
        self.assertTrue(result["evidence"]["query_evidence"])
        self.assertGreaterEqual(len(result["evidence"]["result_evidence"]), 2)

    def test_query_without_search_results_is_not_done(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image_path = root / "screen.png"
            ocr_path = root / "ocr.json"
            cv2.imwrite(str(image_path), np.zeros((100, 200, 3), dtype=np.uint8))
            ocr_path.write_text(json.dumps({
                "image_size": [200, 100],
                "items": [
                    {"text": "Chrome", "center": [30, 10]},
                    {"text": "GUI Agent", "center": [80, 30]},
                ],
            }), encoding="utf-8")
            result = verify_search_results_ocr(image_path, ocr_path, "GUI Agent")
        self.assertFalse(result["success"])
        self.assertEqual(result["evidence"]["result_evidence"], [])


if __name__ == "__main__":
    unittest.main()
