import json
import unittest

from src.week3_agent import (
    build_offline_agent,
    build_planner_prompt,
    get_current_action,
    parse_plan,
    record_feedback,
    validate_task,
)


class Week3AgentTests(unittest.TestCase):
    def test_empty_task_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_task("  ")

    def test_prompt_contains_original_task(self):
        result = build_planner_prompt({"task": "点击编辑菜单"})
        self.assertIn("点击编辑菜单", result["prompt"])

    def test_offline_agent_creates_search_plan(self):
        state = build_offline_agent().invoke("打开浏览器并搜索 GUI Agent")
        self.assertEqual(state["status"], "ready")
        self.assertEqual(state["model_name"], "mock")
        self.assertIn("GUI Agent", state["done_condition"])
        self.assertGreaterEqual(len(state["steps"]), 3)

    def test_invalid_json_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_plan({"task": "测试", "model_output": "not-json"})

    def test_more_than_eight_steps_is_rejected(self):
        output = json.dumps({"steps": ["步骤"] * 9})
        with self.assertRaises(ValueError):
            parse_plan({"task": "测试", "model_output": output})

    def test_current_action_is_first_step(self):
        state = build_offline_agent().invoke("点击编辑菜单")
        self.assertEqual(get_current_action(state)["step_id"], 1)

    def test_success_moves_to_next_step_without_changing_input(self):
        state = build_offline_agent().invoke("点击编辑菜单")
        updated = record_feedback(state, True, "界面已识别")
        self.assertEqual(state["current_step"], 0)
        self.assertEqual(updated["current_step"], 1)
        self.assertEqual(updated["steps"][0]["status"], "done")

    def test_failure_marks_step_for_retry(self):
        state = build_offline_agent().invoke("点击编辑菜单")
        updated = record_feedback(state, False, "没有找到目标")
        self.assertEqual(updated["current_step"], 0)
        self.assertEqual(updated["status"], "needs_retry")
        self.assertEqual(updated["steps"][0]["status"], "retry")

    def test_all_success_finishes_task(self):
        state = build_offline_agent().invoke("点击编辑菜单")
        while get_current_action(state):
            state = record_feedback(state, True, "模拟成功")
        self.assertEqual(state["status"], "done")
        self.assertIsNone(get_current_action(state))
        self.assertEqual(len(state["history"]), len(state["steps"]))


if __name__ == "__main__":
    unittest.main()
