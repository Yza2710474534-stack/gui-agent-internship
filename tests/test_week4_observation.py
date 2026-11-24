import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import cv2
import numpy as np

from src.week4_observation import capture_observation, make_screen_observer


class Week4ObservationTests(unittest.TestCase):
    def fake_capture(self, monitor_index, output_size):
        return np.zeros((20, 30, 3), dtype=np.uint8), {
            "image_size": [30, 20],
            "screen_region": [100, 50, 30, 20],
            "scale_to_screen": [1.0, 1.0],
        }

    def fake_save(self, image, prefix, output_dir):
        path = Path(output_dir) / f"{prefix}.png"
        self.assertTrue(cv2.imwrite(str(path), image))
        return path

    def test_capture_observation_saves_aligned_ocr_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = Mock()
            engine.recognize.return_value = {
                "image_size": [30, 20], "items": [{"text": "Chrome"}],
                "low_confidence_items": [],
            }
            result = capture_observation(
                engine, directory, capture=self.fake_capture, save=self.fake_save
            )
            self.assertEqual(result["image_size"], [30, 20])
            self.assertEqual(result["ocr_item_count"], 1)
            self.assertTrue(Path(result["image"]).is_file())
            self.assertTrue(Path(result["ocr"]).is_file())
            saved = json.loads(Path(result["ocr"]).read_text(encoding="utf-8"))
            self.assertEqual(saved["image_size"], [30, 20])
            engine.recognize.assert_called_once()

    def test_mismatched_ocr_size_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = Mock()
            engine.recognize.return_value = {"image_size": [99, 99], "items": []}
            with self.assertRaisesRegex(ValueError, "尺寸"):
                capture_observation(
                    engine, directory, capture=self.fake_capture, save=self.fake_save
                )

    def test_observer_forwards_state_independently(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = Mock()
            engine.recognize.return_value = {
                "image_size": [30, 20], "items": [], "low_confidence_items": []
            }
            observer = make_screen_observer(
                engine, directory, capture=self.fake_capture, save=self.fake_save
            )
            first = observer({"cycle": 1})
            second = observer({"cycle": 2})
            self.assertEqual(first["screen_region"], [100, 50, 30, 20])
            self.assertEqual(second["ocr_item_count"], 0)
            self.assertEqual(engine.recognize.call_count, 2)


if __name__ == "__main__":
    unittest.main()

