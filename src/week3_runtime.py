"""可测试的长任务运行器。

默认不控制鼠标和键盘。真实执行器、单步判定和完成判定都由调用方传入，
这样可以先安全测试重试、失败停止和日志逻辑。
"""

import copy
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

import cv2

try:
    from .demo import feedback_summary, make_plan
except ImportError:
    from demo import feedback_summary, make_plan


def _timestamp():
    return datetime.now().isoformat(timespec="milliseconds")


def _write_log(path, event, **details):
    """追加一行结构化 JSON 日志。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"time": _timestamp(), "event": event, **details}
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def _verdict(value, default_message):
    """把判定函数的结果整理成统一格式。"""
    if isinstance(value, bool):
        return {"success": value, "message": default_message}
    if not isinstance(value, dict) or not isinstance(value.get("success"), bool):
        raise ValueError("判定结果必须是布尔值，或包含 success 布尔字段的字典")
    return {
        "success": value["success"],
        "message": str(value.get("message", default_message)),
        "evidence": value.get("evidence", {}),
    }


def run_long_task(state, execute_step, verify_step, verify_task, log_path,
                  max_retries=2, max_actions=30):
    """运行多步任务；每步都必须执行并验证，最后还要单独验证任务完成。

    max_retries=2 表示一次首次执行加两次重试。函数不会自行控制桌面，
    调用方必须明确提供 execute_step、verify_step 和 verify_task。
    """
    if not isinstance(max_retries, int) or not 0 <= max_retries <= 10:
        raise ValueError("max_retries 必须是 0 到 10 的整数")
    if not isinstance(max_actions, int) or max_actions < 1:
        raise ValueError("max_actions 必须是正整数")
    if not all(callable(item) for item in (execute_step, verify_step, verify_task)):
        raise ValueError("执行、单步判定和完成判定都必须是可调用函数")

    current = copy.deepcopy(state)
    current.setdefault("history", [])
    current["status"] = "running"
    attempts = {}
    action_count = 0
    started = time.monotonic()
    _write_log(log_path, "task_started", task=current.get("task", ""),
               step_count=len(current.get("steps", [])))

    while current.get("current_step", 0) < len(current.get("steps", [])):
        if action_count >= max_actions:
            current["status"] = "failed"
            current["failure_reason"] = "超过最大动作次数"
            _write_log(log_path, "task_failed", reason=current["failure_reason"],
                       action_count=action_count)
            return current

        index = current["current_step"]
        step = current["steps"][index]
        step_id = step["step_id"]
        attempts[step_id] = attempts.get(step_id, 0) + 1
        attempt = attempts[step_id]
        action_count += 1
        step_started = time.monotonic()
        _write_log(log_path, "step_started", step_id=step_id, attempt=attempt,
                   description=step.get("description", ""))

        try:
            execution = execute_step(copy.deepcopy(step))
            verdict = _verdict(
                verify_step(copy.deepcopy(step), execution),
                "单步验证完成",
            )
        except Exception as error:
            verdict = {"success": False, "message": f"执行或验证异常：{error}",
                       "evidence": {"error_type": type(error).__name__}}

        history_item = {
            "step_id": step_id,
            "attempt": attempt,
            "success": verdict["success"],
            "feedback": verdict["message"],
            "evidence": verdict.get("evidence", {}),
        }
        current["history"].append(history_item)
        _write_log(log_path, "step_finished", **history_item,
                   duration_seconds=round(time.monotonic() - step_started, 4))

        if verdict["success"]:
            current["steps"][index]["status"] = "done"
            current["current_step"] += 1
            continue

        current["steps"][index]["status"] = "retry"
        if attempt <= max_retries:
            current["status"] = "needs_retry"
            _write_log(log_path, "retry_scheduled", step_id=step_id,
                       next_attempt=attempt + 1, reason=verdict["message"])
            continue

        current["steps"][index]["status"] = "failed"
        current["status"] = "failed"
        current["failure_reason"] = verdict["message"]
        _write_log(log_path, "task_failed", step_id=step_id,
                   reason=verdict["message"], action_count=action_count)
        return current

    try:
        completion = _verdict(verify_task(copy.deepcopy(current)), "任务完成条件已满足")
    except Exception as error:
        completion = {"success": False, "message": f"完成判定异常：{error}",
                      "evidence": {"error_type": type(error).__name__}}

    current["completion_check"] = completion
    current["action_count"] = action_count
    current["duration_seconds"] = round(time.monotonic() - started, 4)
    if completion["success"]:
        current["status"] = "done"
        _write_log(log_path, "task_completed", action_count=action_count,
                   duration_seconds=current["duration_seconds"],
                   evidence=completion.get("evidence", {}))
    else:
        current["status"] = "completion_failed"
        current["failure_reason"] = completion["message"]
        _write_log(log_path, "task_failed", reason=completion["message"],
                   action_count=action_count)
    return current


def verify_screenshot_target(image_path, ocr_result, target, screen_region,
                             min_confidence=0.3):
    """用真实图片和 OCR 结果验证一个定位步骤，只生成动作，不点击。"""
    path = Path(image_path)
    image = cv2.imread(str(path))
    if image is None:
        return {"success": False, "message": f"无法读取截图：{path}"}
    height, width = image.shape[:2]
    if list(ocr_result.get("image_size", [])) != [width, height]:
        return {"success": False, "message": "OCR 尺寸与真实截图不一致"}
    plan = make_plan(ocr_result, target, tuple(screen_region))
    if plan["status"] != "preview_ready":
        return {"success": False, "message": f"目标无法唯一定位：{plan['status']}"}
    if plan["confidence"] < min_confidence:
        return {"success": False, "message": "目标置信度低于阈值"}
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "success": True,
        "message": "真实截图中找到唯一目标，已生成安全预览动作",
        "evidence": {
            "image": str(path.resolve()),
            "image_sha256": digest,
            "confidence": plan["confidence"],
            "proposed_action": plan["proposed_action"],
        },
    }


def verify_saved_desktop_step(run_dir):
    """复核一次已经保存的真实桌面单步操作及其前后截图。"""
    run_dir = Path(run_dir)
    report_path = run_dir / "result.json"
    if not report_path.is_file():
        return {"success": False, "message": "缺少 result.json"}
    report = json.loads(report_path.read_text(encoding="utf-8"))
    location = verify_screenshot_target(
        run_dir / "screenshot.png", report.get("ocr", {}), report.get("target", ""),
        report.get("screen_region", []),
    )
    if not location["success"]:
        return location
    if not report.get("executed"):
        return {"success": False, "message": "日志显示动作没有执行"}

    before = cv2.imread(str(run_dir / "before_action.png"))
    after = cv2.imread(str(run_dir / "after_action.png"))
    saved_feedback = report.get("feedback", {})
    if before is None or after is None:
        return {"success": False, "message": "缺少操作前或操作后截图"}
    if "before_ocr" not in saved_feedback or "after_ocr" not in saved_feedback:
        return {"success": False, "message": "缺少操作前后的 OCR 证据"}
    checked = feedback_summary(
        before, after, saved_feedback["before_ocr"], saved_feedback["after_ocr"]
    )
    success = checked["status"] == "menu_likely_open"
    return {
        "success": success,
        "message": "真实桌面单步操作验证通过" if success else "真实截图不足以确认动作成功",
        "evidence": {**location.get("evidence", {}), "visual_feedback": checked},
    }


def verify_search_results_ocr(image_path, ocr_path, query):
    """用真实搜索页截图和 OCR 结果判断搜索任务是否完成。"""
    image_path = Path(image_path)
    ocr_path = Path(ocr_path)
    image = cv2.imread(str(image_path))
    if image is None:
        return {"success": False, "message": f"无法读取截图：{image_path}"}
    if not ocr_path.is_file():
        return {"success": False, "message": f"无法读取 OCR：{ocr_path}"}
    ocr_result = json.loads(ocr_path.read_text(encoding="utf-8"))
    height, width = image.shape[:2]
    if ocr_result.get("image_size") != [width, height]:
        return {"success": False, "message": "OCR 尺寸与搜索页截图不一致"}

    wanted = "".join(str(query).lower().split())
    if not wanted:
        return {"success": False, "message": "搜索关键词不能为空"}

    query_evidence = []
    result_evidence = []
    browser_detected = False
    for item in ocr_result.get("items", []):
        text = str(item.get("text", ""))
        compact = "".join(text.lower().split())
        center = item.get("center", [0, 0])
        y = center[1] if isinstance(center, list) and len(center) == 2 else 0
        browser_detected = browser_detected or compact == "chrome"
        if wanted in compact and y < 300:
            query_evidence.append(text)
        if y >= 280 and (
            wanted in compact
            or "gui-agents" in compact
            or "gui-agent" in compact
            or "github" in compact
            or "topics" in compact
        ):
            result_evidence.append(text)

    success = browser_detected and bool(query_evidence) and len(result_evidence) >= 2
    return {
        "success": success,
        "message": "真实搜索截图完成条件通过" if success else "真实搜索截图完成条件未满足",
        "evidence": {
            "image": str(image_path.resolve()),
            "image_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
            "ocr": str(ocr_path.resolve()),
            "browser_detected": browser_detected,
            "query_evidence": query_evidence,
            "result_evidence": result_evidence,
        },
    }
