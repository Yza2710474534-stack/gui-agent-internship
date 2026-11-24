import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from scripts.run_week5_capture_probe import run_probe


class Week5CaptureProbeTests(unittest.TestCase):
    def test_success_saves_summary_without_desktop_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            capture = Mock(return_value=(object(), {
                "image_size": [100, 80],
                "screen_region": [0, 0, 100, 80],
                "scale_to_screen": [1.0, 1.0],
            }))
            save = Mock(return_value=Path(directory) / "week5_probe.png")
            result = run_probe(directory, capture=capture, save=save)
            self.assertEqual(result["status"], "capture_ready")
            self.assertEqual(result["mouse_keyboard_actions"], 0)
            self.assertEqual(json.loads((Path(directory) / "result.json").read_text())["status"], "capture_ready")
            capture.assert_called_once_with(None, None)
            save.assert_called_once()

    def test_failure_is_recorded_and_does_not_raise(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_probe(directory, capture=Mock(side_effect=RuntimeError("屏幕不可用")))
            self.assertEqual(result["status"], "capture_failed")
            self.assertEqual(result["project_mss"], "unavailable")
            self.assertIn("屏幕不可用", result["error"])
            self.assertTrue((Path(directory) / "result.json").exists())


if __name__ == "__main__":
    unittest.main()
