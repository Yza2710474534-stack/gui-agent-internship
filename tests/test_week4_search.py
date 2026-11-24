import tempfile
import unittest
from pathlib import Path

from src.week4_search import (
    make_browser_search_completion,
    verify_browser_search_observation,
    verify_post_action_observation,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
REAL_IMAGE = PROJECT_DIR / "output/screenshots/screen_1_20260919_171319_864597.png"
REAL_OCR = PROJECT_DIR / "output/ocr/ocr_20260919_171420_361782.json"


class Week4SearchTests(unittest.TestCase):
    def test_existing_real_search_evidence_passes(self):
        result = verify_browser_search_observation(
            {"image": str(REAL_IMAGE), "ocr": str(REAL_OCR)}, "GUI Agent"
        )
        self.assertTrue(result["success"])
        self.assertTrue(result["evidence"]["result_evidence"])

    def test_missing_evidence_is_rejected(self):
        result = verify_browser_search_observation({}, "GUI Agent")
        self.assertFalse(result["success"])

    def test_post_action_requires_saved_files(self):
        with tempfile.TemporaryDirectory() as directory:
            result = verify_post_action_observation(
                {}, {"image": str(Path(directory) / "missing.png"), "ocr": "missing.json"},
                {}, {},
            )
        self.assertFalse(result["success"])

    def test_completion_factory_uses_query(self):
        verify_done = make_browser_search_completion("GUI Agent")
        result = verify_done({}, {"image": str(REAL_IMAGE), "ocr": str(REAL_OCR)})
        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()

