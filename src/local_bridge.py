"""把云端控制台安全连接到本机 GUI Agent。

服务只监听回环地址。默认只允许预览；只有命令行显式传入
``--enable-live`` 后，网页的实时模式才可能调用鼠标控制模块。
"""

from __future__ import annotations

import argparse
import json
import re
import threading
import time
import uuid
from copy import deepcopy
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


PROJECT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_PATH = PROJECT_DIR / "gui-agent-console" / "dist" / "index.html"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_BODY_BYTES = 16_384
ALLOWED_ORIGINS = frozenset(
    {
        "https://gui-agent-console-2026.remusswift194.chatgpt.site",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
        "http://127.0.0.1:8765",
        "http://localhost:8765",
    }
)
TERMINAL_STATUSES = frozenset(
    {"preview_ready", "done", "stopped", "failed", "action_failed", "completion_failed",
     "timed_out", "cycle_limit_reached"}
)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _public_record(record: dict) -> dict:
    return {
        key: deepcopy(value)
        for key, value in record.items()
        if not key.startswith("_") and key != "artifact_path"
    }


def _compact_error(error: Exception) -> str:
    message = str(error).strip() or type(error).__name__
    lowered = message.lower()
    if "no displays visible" in lowered or "screen" in lowered and "0x0" in lowered:
        return "本地执行器看不到屏幕。请从已获得屏幕录制权限的终端启动。"
    if "accessibility" in lowered or "not trusted" in lowered:
        return "缺少辅助功能权限，无法控制鼠标或键盘。"
    if "download" in lowered and "model" in lowered:
        return "OCR 模型未安装完整，请先运行项目环境检查。"
    return message[:300]


def extract_click_target(task: str) -> str | None:
    """提取“点击 X”中的可见文字，避免让模型生成任意坐标。"""
    match = re.search(r"点击\s*[“‘'\"]?([^，。,.；;\n]{1,40})", task)
    if not match:
        return None
    target = match.group(1).strip(" ”’'\"")
    return target or None


def extract_search_query(task: str) -> str | None:
    match = re.search(r"搜索\s*[“‘'\"]?([^，。；;\n]{1,80})", task)
    if not match:
        return None
    query = match.group(1).strip(" ”’'\"")
    query = re.sub(r"\s*(并|然后|，).*$", "", query).strip()
    return query or None


class TaskStore:
    def __init__(self):
        self._lock = threading.RLock()
        self._records: dict[str, dict] = {}
        self._current_id: str | None = None

    def create(self, task: str, mode: str) -> dict:
        with self._lock:
            current = self._records.get(self._current_id or "")
            if current and current["status"] not in TERMINAL_STATUSES:
                raise RuntimeError("已有任务正在运行")
            task_id = uuid.uuid4().hex[:12]
            record = {
                "id": task_id,
                "task": task,
                "mode": mode,
                "status": "queued",
                "step": 0,
                "created_at": _now(),
                "updated_at": _now(),
                "logs": [],
                "metrics": {"ocr_items": None, "confidence": None, "safety": "检查中"},
                "result": None,
                "error": None,
                "screenshot_url": None,
                "artifact_path": None,
                "_cancel": threading.Event(),
                "_pause": threading.Event(),
            }
            self._records[task_id] = record
            self._current_id = task_id
            return _public_record(record)

    def get(self, task_id: str) -> dict | None:
        with self._lock:
            record = self._records.get(task_id)
            return _public_record(record) if record else None

    def get_internal(self, task_id: str) -> dict | None:
        with self._lock:
            return self._records.get(task_id)

    def current(self) -> dict | None:
        with self._lock:
            if not self._current_id:
                return None
            return self.get(self._current_id)

    def update(self, task_id: str, **changes) -> dict:
        with self._lock:
            record = self._records[task_id]
            record.update(deepcopy(changes))
            record["updated_at"] = _now()
            return _public_record(record)

    def add_log(self, task_id: str, message: str, status: str = "完成") -> None:
        with self._lock:
            record = self._records[task_id]
            record["logs"].append({"time": datetime.now().strftime("%H:%M:%S"),
                                   "message": message, "status": status})
            record["logs"] = record["logs"][-8:]
            record["updated_at"] = _now()

    def stop(self, task_id: str) -> dict:
        with self._lock:
            record = self._records[task_id]
            if record["status"] in TERMINAL_STATUSES:
                return _public_record(record)
            record["_cancel"].set()
            record["_pause"].clear()
            record["status"] = "stopping"
            record["updated_at"] = _now()
            return _public_record(record)

    def pause(self, task_id: str) -> dict:
        with self._lock:
            record = self._records[task_id]
            if record["status"] not in {"queued", "running", "observing", "planning"}:
                raise RuntimeError("当前任务不能暂停")
            record["_pause"].set()
            record["status"] = "paused"
            record["updated_at"] = _now()
            return _public_record(record)

    def resume(self, task_id: str) -> dict:
        with self._lock:
            record = self._records[task_id]
            if record["status"] != "paused":
                raise RuntimeError("当前任务未暂停")
            record["_pause"].clear()
            record["status"] = "running"
            record["updated_at"] = _now()
            return _public_record(record)


class LocalExecutor:
    """调用第四周实时循环；依赖在任务开始后才加载。"""

    def __init__(self, project_dir: Path = PROJECT_DIR, enable_live: bool = False):
        self.project_dir = Path(project_dir)
        self.enable_live = bool(enable_live)
        self._engine = None
        self._engine_lock = threading.Lock()

    def _get_engine(self):
        with self._engine_lock:
            if self._engine is None:
                from .ocr_engine import OCREngine

                self._engine = OCREngine(download_enabled=False)
            return self._engine

    @staticmethod
    def _wait_if_paused(record: dict):
        while record["_pause"].is_set() and not record["_cancel"].is_set():
            time.sleep(0.1)

    def run(self, record: dict, store: TaskStore) -> dict:
        from .coordinate import image_to_screen
        from .week4_observation import make_screen_observer
        from .week4_realtime import run_realtime_loop
        from .week8_verification import (
            extract_expected_text, verify_click_completion, verify_click_outcome,
        )

        task_id = record["id"]
        mode = record["mode"]
        expected_text = extract_expected_text(record["task"])
        output_dir = self.project_dir / "output" / "local_bridge" / task_id
        log_path = output_dir / "events.jsonl"
        store.update(task_id, status="running", step=1)
        store.add_log(task_id, "任务已由本地执行器接收", "已接收")

        store.update(task_id, status="observing", step=2)
        store.add_log(task_id, "正在加载 OCR 并读取当前屏幕", "进行中")
        engine = self._get_engine()
        base_observer = make_screen_observer(engine, output_dir, min_confidence=0.3, scale=2)

        def observe(state):
            self._wait_if_paused(record)
            if record["_cancel"].is_set():
                raise RuntimeError("任务已由用户停止")
            store.update(task_id, status="observing", step=2)
            observation = base_observer(state)
            metrics = store.get(task_id)["metrics"]
            metrics["ocr_items"] = observation.get("ocr_item_count")
            store.update(
                task_id,
                metrics=metrics,
                artifact_path=observation.get("image"),
                screenshot_url=f"/api/tasks/{task_id}/screenshot",
            )
            store.add_log(task_id, f"屏幕识别完成，共发现 {observation.get('ocr_item_count', 0)} 个文字区域")
            return observation

        def decide(state, observation):
            self._wait_if_paused(record)
            if record["_cancel"].is_set():
                return {"kind": "stop", "reason": "任务已由用户停止"}
            if state.get("history"):
                return {"kind": "done"}
            store.update(task_id, status="planning", step=3)
            ocr_path = Path(observation["ocr"])
            ocr = json.loads(ocr_path.read_text(encoding="utf-8"))
            click_target = extract_click_target(record["task"])
            if click_target:
                normalized = "".join(click_target.split()).lower()
                items = ocr.get("items", [])
                exact = [item for item in items if "".join(item.get("text", "").split()).lower() == normalized]
                matches = exact or [item for item in items if normalized in "".join(item.get("text", "").split()).lower()]
                if len(matches) != 1:
                    return {"kind": "stop", "reason": f"无法唯一定位“{click_target}”"}
                item = matches[0]
                x, y = image_to_screen(
                    *item["center"], tuple(observation["image_size"]), tuple(observation["screen_region"])
                )
                store.update(
                    task_id,
                    metrics={
                        "ocr_items": observation.get("ocr_item_count"),
                        "confidence": round(float(item.get("confidence", 0)) * 100, 1),
                        "safety": "通过",
                    },
                )
                store.add_log(task_id, f"已定位“{click_target}”，坐标 ({round(x)}, {round(y)})")
                return {"kind": "action", "action": {"type": "click", "x": round(x), "y": round(y)}}

            query = extract_search_query(record["task"])
            if query and mode == "preview":
                store.update(task_id, metrics={"ocr_items": observation.get("ocr_item_count"),
                                               "confidence": None, "safety": "通过"})
                store.add_log(task_id, f"已生成搜索词输入预览：{query}")
                return {"kind": "action", "action": {"type": "type_text", "text": query}}
            if query:
                return {"kind": "stop", "reason": "实时搜索需要专用浏览器流程，当前不会向未知焦点输入文字"}
            if mode == "preview":
                store.update(task_id, metrics={"ocr_items": observation.get("ocr_item_count"),
                                               "confidence": None, "safety": "通过"})
                return {"kind": "action", "action": {"type": "wait", "seconds": 1}}
            return {"kind": "stop", "reason": "实时模式目前只支持点击可见文字"}

        def execute(action):
            self._wait_if_paused(record)
            if record["_cancel"].is_set():
                raise RuntimeError("任务已由用户停止")
            if not self.enable_live:
                raise RuntimeError("本地服务未启用实时执行")
            from . import controller

            action_type = action["type"]
            if action_type == "click":
                controller.click(action["x"], action["y"], action.get("button", "left"))
            elif action_type == "scroll":
                controller.scroll(action["amount"])
            elif action_type == "wait":
                time.sleep(action.get("seconds", 0))
            else:
                raise RuntimeError("实时模式拒绝向未知焦点输入文字")
            store.add_log(task_id, f"已执行安全动作：{action_type}")
            return {"ok": True, "type": action_type}

        result = run_realtime_loop(
            record["task"], observe, decide, execute,
            lambda state, observation, action, execution:
                verify_click_outcome(observation, expected_text)
                if execution.get("ok") is True else
                {"success": False, "message": "执行器未确认动作成功"},
            lambda state, observation: verify_click_completion(state, observation, expected_text),
            log_path,
            mode=mode,
            max_cycles=2,
            max_actions=1,
            max_duration_seconds=90,
        )
        if record["_cancel"].is_set():
            result["status"] = "stopped"
        return result


class BridgeApplication:
    def __init__(self, executor: LocalExecutor | None = None):
        self.executor = executor or LocalExecutor()
        self.store = TaskStore()

    def start_task(self, task: str, mode: str) -> dict:
        if not isinstance(task, str) or not task.strip() or len(task.strip()) > 240:
            raise ValueError("任务内容必须为 1–240 个字符")
        if mode not in {"preview", "live"}:
            raise ValueError("运行模式必须是 preview 或 live")
        if mode == "live" and not self.executor.enable_live:
            raise PermissionError("本地执行器当前只允许预览；重新启动时加入 --enable-live 才能执行点击")
        created = self.store.create(task.strip(), mode)
        internal = self.store.get_internal(created["id"])
        thread = threading.Thread(target=self._run_task, args=(internal,), daemon=True)
        thread.start()
        return created

    def _run_task(self, record: dict):
        task_id = record["id"]
        try:
            result = self.executor.run(record, self.store)
            status = result.get("status", "failed")
            if status in {"preview_ready", "done"}:
                self.store.add_log(task_id, "动作方案已生成" if status == "preview_ready" else "任务执行完成")
            elif status == "stopped":
                self.store.add_log(task_id, result.get("stop_reason", "任务已停止"), "已停止")
            else:
                self.store.add_log(task_id, result.get("failure_reason", "任务未完成"), "失败")
            self.store.update(task_id, status=status, step=4, result=result,
                              error=result.get("failure_reason") or result.get("stop_reason"))
        except Exception as error:
            message = _compact_error(error)
            self.store.add_log(task_id, message, "失败")
            self.store.update(task_id, status="failed", step=4, error=message,
                              metrics={"ocr_items": None, "confidence": None, "safety": "未通过"})


class BridgeRequestHandler(BaseHTTPRequestHandler):
    server_version = "GUIAgentBridge/1.0"

    @property
    def app(self) -> BridgeApplication:
        return self.server.app  # type: ignore[attr-defined]

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

    def _origin_allowed(self) -> bool:
        origin = self.headers.get("Origin")
        return origin is None or origin in self.server.allowed_origins  # type: ignore[attr-defined]

    def _cors_headers(self):
        origin = self.headers.get("Origin")
        if origin in self.server.allowed_origins:  # type: ignore[attr-defined]
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")

    def _send_json(self, status: int, payload: dict):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("无效的请求长度") from error
        if size <= 0 or size > MAX_BODY_BYTES:
            raise ValueError("请求内容为空或过大")
        try:
            value = json.loads(self.rfile.read(size).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("请求内容不是有效 JSON") from error
        if not isinstance(value, dict):
            raise ValueError("请求内容必须是 JSON 对象")
        return value

    def do_OPTIONS(self):
        if not self._origin_allowed():
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin_not_allowed"})
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if not self._origin_allowed():
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin_not_allowed"})
            return
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            if not FRONTEND_PATH.is_file():
                self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "frontend_not_found"})
                return
            data = FRONTEND_PATH.read_bytes()
            self.send_response(HTTPStatus.OK)
            self._cors_headers()
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/api/health":
            self._send_json(HTTPStatus.OK, {
                "ok": True,
                "service": "GUI Agent Local Executor",
                "version": "1.0",
                "live_enabled": self.app.executor.enable_live,
            })
            return
        if path == "/api/tasks/current":
            self._send_json(HTTPStatus.OK, {"ok": True, "task": self.app.store.current()})
            return
        match = re.fullmatch(r"/api/tasks/([a-f0-9]{12})", path)
        if match:
            task = self.app.store.get(match.group(1))
            self._send_json(HTTPStatus.OK if task else HTTPStatus.NOT_FOUND,
                            {"ok": bool(task), "task": task})
            return
        screenshot = re.fullmatch(r"/api/tasks/([a-f0-9]{12})/screenshot", path)
        if screenshot:
            record = self.app.store.get_internal(screenshot.group(1))
            image_path = Path(record["artifact_path"]) if record and record.get("artifact_path") else None
            if not image_path or not image_path.is_file() or image_path.suffix.lower() != ".png":
                self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "screenshot_not_found"})
                return
            data = image_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self._cors_headers()
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})

    def do_POST(self):
        if not self._origin_allowed():
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": "origin_not_allowed"})
            return
        path = urlparse(self.path).path
        try:
            if path == "/api/tasks":
                body = self._read_json()
                task = self.app.start_task(body.get("task"), body.get("mode", "preview"))
                self._send_json(HTTPStatus.ACCEPTED, {"ok": True, "task": task})
                return
            action = re.fullmatch(r"/api/tasks/([a-f0-9]{12})/(pause|resume|stop)", path)
            if action:
                task_id, name = action.groups()
                if not self.app.store.get_internal(task_id):
                    self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "task_not_found"})
                    return
                operation = getattr(self.app.store, name)
                task = operation(task_id)
                self._send_json(HTTPStatus.OK, {"ok": True, "task": task})
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})
        except PermissionError as error:
            self._send_json(HTTPStatus.FORBIDDEN, {"ok": False, "error": str(error)})
        except (ValueError, RuntimeError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(error)})


class BridgeServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, app: BridgeApplication, allowed_origins=ALLOWED_ORIGINS):
        super().__init__(address, BridgeRequestHandler)
        self.app = app
        self.allowed_origins = frozenset(allowed_origins)


def build_server(host=DEFAULT_HOST, port=DEFAULT_PORT, *, enable_live=False, executor=None):
    app = BridgeApplication(executor or LocalExecutor(enable_live=enable_live))
    return BridgeServer((host, port), app)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST, choices=[DEFAULT_HOST],
                        help="安全限制：只允许监听 127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--enable-live", action="store_true",
                        help="允许网页执行一次经过 OCR 定位的文字点击")
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("端口必须在 1024 到 65535 之间")
    server = build_server(args.host, args.port, enable_live=args.enable_live)
    mode = "预览 + 实时点击" if args.enable_live else "仅预览"
    print(f"GUI Agent 本地执行器已启动：http://{args.host}:{args.port}（{mode}）", flush=True)
    print("按 Control-C 停止。", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("\n本地执行器已停止。")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
