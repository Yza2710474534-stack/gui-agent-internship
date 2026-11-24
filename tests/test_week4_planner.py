import json
import unittest

from src.week4_planner import (
    build_structured_planner_prompt,
    make_model_decider,
    parse_structured_decision,
)


class Week4PlannerTests(unittest.TestCase):
    def test_parses_allowed_action(self):
        result = parse_structured_decision(
            '{"kind":"action","action":{"type":"click","x":10,"y":20}}'
        )
        self.assertEqual(result["action"]["type"], "click")

    def test_parses_done_and_stop(self):
        self.assertEqual(parse_structured_decision('{"kind":"done"}'), {"kind": "done"})
        self.assertEqual(
            parse_structured_decision('{"kind":"stop","reason":"请人工确认"}')["reason"],
            "请人工确认",
        )

    def test_rejects_code_shell_and_extra_fields(self):
        bad_outputs = [
            "not json",
            '{"kind":"action","action":{"type":"shell","command":"rm -rf"}}',
            '{"kind":"done","command":"open"}',
        ]
        for output in bad_outputs:
            with self.subTest(output=output):
                with self.assertRaises(ValueError):
                    parse_structured_decision(output)

    def test_prompt_has_task_and_safety_contract(self):
        prompt = build_structured_planner_prompt(
            "搜索 GUI Agent", {"image": "screen.png", "items": [{"text": "secret"}]}
        )
        self.assertIn("搜索 GUI Agent", prompt)
        self.assertIn("只返回一个 JSON 对象", prompt)
        self.assertIn("禁止任意代码", prompt)
        self.assertNotIn("secret", prompt)

    def test_model_decider_calls_model_and_parses_result(self):
        calls = []

        def fake_model(prompt):
            calls.append(prompt)
            return json.dumps({"kind": "action", "action": {"type": "wait", "seconds": 0}})

        decider = make_model_decider("等待页面", fake_model)
        result = decider({}, {"image_size": [100, 100]})
        self.assertEqual(result["action"]["type"], "wait")
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()

