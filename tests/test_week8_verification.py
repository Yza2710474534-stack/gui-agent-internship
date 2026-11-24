import json
import tempfile
import unittest
from pathlib import Path

from src.local_bridge import TaskStore
from src.week8_verification import (
    extract_expected_text, verify_click_completion, verify_click_outcome,
)


class ClickVerificationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.image = root / "after.png"
        self.image.write_bytes(b"test evidence placeholder")
        self.ocr = root / "after.ocr.json"
        self.ocr.write_text(json.dumps({"items": [{"text": "VERIFIED"}]}))
        self.observation = {"image": str(self.image), "ocr": str(self.ocr)}

    def test_task_extracts_explicit_completion(self):
        self.assertEqual(extract_expected_text("点击 VERIFY，确认出现 VERIFIED"), "VERIFIED")
        self.assertIsNone(extract_expected_text("点击 VERIFY"))

    def test_expected_text_required_when_requested(self):
        self.assertTrue(verify_click_outcome(self.observation, "VERIFIED")["success"])
        self.assertFalse(verify_click_outcome(self.observation, "MISSING")["success"])
        self.assertFalse(verify_click_outcome(self.observation, "VERIFY")["success"])

    def test_missing_and_corrupt_evidence_fail_closed(self):
        self.assertFalse(verify_click_outcome({}, "VERIFIED")["success"])
        self.ocr.write_text("broken json")
        self.assertFalse(verify_click_outcome(self.observation, "VERIFIED")["success"])

    def test_completion_requires_successful_history(self):
        for history in ([], [{"success": False}]):
            self.assertFalse(verify_click_completion({"history": history}, self.observation, "VERIFIED")["success"])
        self.assertTrue(verify_click_completion({"history": [{"success": True}]}, self.observation, "VERIFIED")["success"])

    def test_without_business_condition_is_explicitly_labelled(self):
        result = verify_click_outcome(self.observation, None)
        self.assertTrue(result["success"])
        self.assertFalse(result["business_verified"])

    def test_limits_release_task_slot(self):
        for status in ("timed_out", "cycle_limit_reached"):
            store = TaskStore()
            first = store.create("first", "preview")
            store.update(first["id"], status=status)
            self.assertNotEqual(store.create("next", "preview")["id"], first["id"])
