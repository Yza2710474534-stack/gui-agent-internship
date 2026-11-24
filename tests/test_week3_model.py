import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.week3_model import (
    ModelCallError,
    call_mock,
    call_model,
    call_ollama,
    call_openai_compatible,
    encode_image,
)


class FakeResponse:
    def __init__(self, data):
        self.data = json.dumps(data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.data


class Week3ModelTests(unittest.TestCase):
    def test_mock_returns_valid_plan_json(self):
        result = json.loads(call_mock("用户任务：点击编辑菜单"))
        self.assertEqual(len(result["steps"]), 4)
        self.assertIn("编辑菜单", result["done_condition"])

    def test_unknown_provider_is_rejected(self):
        with self.assertRaises(ModelCallError):
            call_model("测试", provider="unknown")

    def test_image_is_encoded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "screen.png"
            path.write_bytes(b"fake-png")
            mime_type, content = encode_image(path)
        self.assertEqual(mime_type, "image/png")
        self.assertEqual(base64.b64decode(content), b"fake-png")

    def test_missing_image_is_rejected(self):
        with self.assertRaises(ModelCallError):
            encode_image("missing-screen.png")

    @patch("src.week3_model.urllib.request.urlopen")
    def test_openai_compatible_request(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse(
            {"choices": [{"message": {"content": "model answer"}}]}
        )
        result = call_openai_compatible(
            "hello", "vision-model", "https://example.com/v1", "secret"
        )
        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(result, "model answer")
        self.assertEqual(request.full_url, "https://example.com/v1/chat/completions")
        self.assertEqual(payload["model"], "vision-model")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")

    @patch("src.week3_model._post_json")
    def test_deepseek_official_address_bypasses_proxy(self, mocked_post):
        mocked_post.return_value = {
            "choices": [{"message": {"content": "model answer"}}]
        }
        result = call_openai_compatible(
            "hello", "deepseek-flash", "https://api.deepseek.com", "secret"
        )
        self.assertEqual(result, "model answer")
        self.assertTrue(mocked_post.call_args.kwargs["bypass_proxy"])

    @patch("src.week3_model.urllib.request.urlopen")
    def test_ollama_multimodal_request(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeResponse(
            {"message": {"content": '{"steps":["观察"]}'}}
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "screen.png"
            path.write_bytes(b"image")
            result = call_ollama("观察图片", "local-vlm", image_path=path)
        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertIn("images", payload["messages"][0])
        self.assertEqual(payload["stream"], False)
        self.assertIn("steps", result)

    def test_api_requires_model_and_address(self):
        with self.assertRaises(ModelCallError):
            call_openai_compatible("hello", "", "https://example.com/v1")
        with self.assertRaises(ModelCallError):
            call_openai_compatible("hello", "model", "")

    def test_deepseek_requires_api_key(self):
        with self.assertRaisesRegex(ModelCallError, "API Key"):
            call_openai_compatible(
                "hello", "deepseek-flash", "https://api.deepseek.com", ""
            )


if __name__ == "__main__":
    unittest.main()
