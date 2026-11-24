"""定位计划、菜单反馈和点击边界测试；不发送真实鼠标事件。"""

import types
import unittest
from unittest.mock import Mock, patch

import numpy as np

from src.demo import feedback_summary, make_plan
from src.controller import click_edit_menu


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.item = {"text": "编辑", "center": [100, 10], "confidence": 0.95}
        self.result = {"image_size": [500, 40], "items": [self.item]}

    def test_scale_and_offset(self):
        plan = make_plan(self.result, "编辑", (50, 100, 1000, 80))
        self.assertEqual(plan["proposed_action"], {"type": "click", "x": 250, "y": 120})
        self.assertFalse(plan["executed"])

    def test_missing_or_ambiguous_target_never_proposes_click(self):
        self.assertIsNone(make_plan(self.result, "窗口", (0, 0, 1000, 80))["proposed_action"])
        self.result["items"].append(self.item.copy())
        self.assertIsNone(make_plan(self.result, "编辑", (0, 0, 1000, 80))["proposed_action"])

    def test_feedback_requires_new_labels_and_image_change(self):
        before = np.zeros((10, 10, 3), dtype=np.uint8)
        after = np.full_like(before, 255)
        no_menu = {"items": [{"text": "Hello GUI Agent"}]}
        menu = {"items": [{"text": "拷贝"}, {"text": "粘贴"}]}
        self.assertEqual(feedback_summary(before, after, no_menu, menu)["status"], "menu_likely_open")
        self.assertEqual(feedback_summary(before, before, no_menu, menu)["status"], "needs_visual_check")
        self.assertEqual(feedback_summary(before, after, menu, menu)["status"], "needs_visual_check")

    def test_click_guard(self):
        fake_mouse = types.SimpleNamespace(size=lambda: (1470, 956), click=Mock())
        with patch.dict("sys.modules", {"pyautogui": fake_mouse}):
            with patch("src.controller.require_textedit"):
                click_edit_menu(184, 16)
                fake_mouse.click.assert_called_once_with(184, 16, button="left")
                fake_mouse.click.reset_mock()
                for point in ((184, 60), (-1, 16), (1470, 16), (float("nan"), 16)):
                    with self.assertRaises(ValueError):
                        click_edit_menu(*point)
                fake_mouse.click.assert_not_called()
            with patch("src.controller.require_textedit", side_effect=RuntimeError("前台不匹配")):
                with self.assertRaises(RuntimeError):
                    click_edit_menu(184, 16)
                fake_mouse.click.assert_not_called()


if __name__ == "__main__":
    unittest.main()
