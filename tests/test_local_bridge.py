import json
import threading
import time
import unittest
import urllib.error
import urllib.request

from src.local_bridge import (
    ALLOWED_ORIGINS,
    BridgeApplication,
    BridgeServer,
    extract_click_target,
    extract_search_query,
)


class FakeExecutor:
    enable_live = False

    def run(self, record, store):
        store.update(record["id"], status="observing", step=2)
        store.add_log(record["id"], "测试观察完成")
        return {"status": "preview_ready", "proposed_action": {"type": "wait", "seconds": 1}}


class LocalBridgeTest(unittest.TestCase):
    def setUp(self):
        self.server = BridgeServer(("127.0.0.1", 0), BridgeApplication(FakeExecutor()))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def request(self, path, *, method="GET", payload=None, origin=None):
        headers = {}
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if origin:
            headers["Origin"] = origin
        request = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, dict(response.headers), json.loads(response.read())

    def test_extracts_supported_tasks(self):
        self.assertEqual(extract_click_target("请点击 编辑 菜单"), "编辑 菜单")
        self.assertEqual(extract_search_query("搜索 GUI Agent，并确认结果"), "GUI Agent")

    def test_health_allows_published_origin(self):
        status, headers, body = self.request("/api/health", origin=next(iter(ALLOWED_ORIGINS)))
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertIn("Access-Control-Allow-Origin", headers)

    def test_serves_local_frontend(self):
        with urllib.request.urlopen(self.base + "/", timeout=2) as response:
            html = response.read().decode("utf-8")
        self.assertIn("GUI Agent 控制台", html)
        self.assertIn("taskForm", html)
        self.assertIn("requestMeta", html)
        self.assertIn("最近接口：", html)
        self.assertIn("网络错误", html)
        self.assertIn("本地执行器响应超时", html)
        self.assertIn("captureNote", html)
        self.assertIn("截图已加载", html)
        self.assertIn("!state.taskId", html)

    def test_rejects_untrusted_origin(self):
        request = urllib.request.Request(self.base + "/api/health", headers={"Origin": "https://example.com"})
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(request, timeout=2)
        self.assertEqual(raised.exception.code, 403)

    def test_starts_and_reports_preview_task(self):
        _, _, body = self.request(
            "/api/tasks", method="POST", payload={"task": "测试任务", "mode": "preview"},
            origin="https://gui-agent-console-2026.remusswift194.chatgpt.site",
        )
        task_id = body["task"]["id"]
        for _ in range(20):
            _, _, current = self.request(f"/api/tasks/{task_id}")
            if current["task"]["status"] == "preview_ready":
                break
            time.sleep(0.01)
        self.assertEqual(current["task"]["status"], "preview_ready")
        self.assertEqual(current["task"]["result"]["proposed_action"]["type"], "wait")


if __name__ == "__main__":
    unittest.main()
