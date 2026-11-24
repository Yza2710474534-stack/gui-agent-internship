"""第四周：截图—规划—动作—验证的可暂停实时循环。

本模块不主动导入截图、OCR 或鼠标控制库。调用方通过依赖注入提供
observe、decide、execute 和 verify 函数，因此默认测试不会碰真实桌面。
mode="preview" 只生成一次待执行动作；只有明确使用 mode="live" 才调用
execute，且动作类型和动作次数仍受安全边界限制。
"""

import copy
import json
import math
import time
from datetime import datetime
from pathlib import Path


ACTION_TYPES = frozenset({"click", "type_text", "scroll", "wait"})


def _timestamp():
    return datetime.now().isoformat(timespec="milliseconds")


def _write_log(path, event, **details):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"time": _timestamp(), "event": event, **details}
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def _verdict(value, default_message):
    if isinstance(value, bool):
        return {"success": value, "message": default_message, "evidence": {}}
    if not isinstance(value, dict) or not isinstance(value.get("success"), bool):
        raise ValueError("验证结果必须是布尔值，或包含 success 布尔字段的字典")
    return {
        "success": value["success"],
        "message": str(value.get("message", default_message)),
        "evidence": value.get("evidence", {}),
    }


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"动作参数 {label} 必须是有限数值")


def validate_action(action, allowed_action_types=ACTION_TYPES):
    """验证可执行动作，不检查界面语义，也不执行动作。"""
    if not isinstance(action, dict):
        raise ValueError("动作必须是字典")
    action_type = action.get("type")
    if action_type not in allowed_action_types:
        raise ValueError(f"动作类型不在允许列表中：{action_type}")

    if action_type == "click":
        _finite_number(action.get("x"), "x")
        _finite_number(action.get("y"), "y")
        if action.get("button", "left") not in {"left", "right", "middle"}:
            raise ValueError("点击按键必须是 left、right 或 middle")
    elif action_type == "type_text":
        text = action.get("text")
        if not isinstance(text, str) or not text:
            raise ValueError("输入动作必须包含非空 text")
        if any(not (32 <= ord(char) <= 126 or char in "\n\t") for char in text):
            raise ValueError("实时循环只允许输入英文、数字及常用标点")
    elif action_type == "scroll":
        amount = action.get("amount")
        if not isinstance(amount, int) or isinstance(amount, bool):
            raise ValueError("滚动量必须是整数")
    elif action_type == "wait":
        seconds = action.get("seconds", 0)
        _finite_number(seconds, "seconds")
        if seconds < 0 or seconds > 30:
            raise ValueError("等待时间必须在 0 到 30 秒之间")
    return copy.deepcopy(action)


def run_realtime_loop(
    task,
    observe,
    decide,
    execute,
    verify,
    verify_done,
    log_path,
    *,
    mode="preview",
    max_cycles=20,
    max_actions=10,
    max_action_retries=0,
    max_duration_seconds=None,
    allowed_action_types=ACTION_TYPES,
):
    """运行一轮可暂停的实时循环。

    ``observe`` 返回截图/OCR等当前观察；``decide`` 返回以下之一：
    ``{"kind": "action", "action": {...}}``、
    ``{"kind": "done"}`` 或 ``{"kind": "stop", "reason": "..."}``。
    live 模式下执行动作并用 ``verify`` 检查结果；preview 模式遇到首个
    动作就停止，避免预览阶段重复生成或误执行动作。
    """
    if not isinstance(task, str) or not task.strip():
        raise ValueError("task 不能为空")
    if mode not in {"preview", "live"}:
        raise ValueError("mode 必须是 preview 或 live")
    if not isinstance(max_cycles, int) or not 1 <= max_cycles <= 100:
        raise ValueError("max_cycles 必须是 1 到 100 的整数")
    if not isinstance(max_actions, int) or not 1 <= max_actions <= 100:
        raise ValueError("max_actions 必须是 1 到 100 的整数")
    if not isinstance(max_action_retries, int) or not 0 <= max_action_retries <= 10:
        raise ValueError("max_action_retries 必须是 0 到 10 的整数")
    if max_duration_seconds is not None:
        _finite_number(max_duration_seconds, "max_duration_seconds")
        if max_duration_seconds < 0:
            raise ValueError("max_duration_seconds 必须大于等于 0")
    if not all(callable(item) for item in (observe, decide, execute, verify, verify_done)):
        raise ValueError("observe、decide、execute、verify 和 verify_done 都必须可调用")
    allowed_action_types = frozenset(allowed_action_types)
    if not allowed_action_types or not allowed_action_types <= ACTION_TYPES:
        raise ValueError("allowed_action_types 含有不支持的动作类型")

    state = {
        "task": task,
        "mode": mode,
        "status": "running",
        "cycle": 0,
        "action_count": 0,
        "history": [],
    }
    started = time.monotonic()
    _write_log(log_path, "loop_started", task=task, mode=mode,
               max_cycles=max_cycles, max_actions=max_actions,
               max_action_retries=max_action_retries,
               max_duration_seconds=max_duration_seconds)

    for cycle in range(1, max_cycles + 1):
        state["cycle"] = cycle
        if (max_duration_seconds is not None and
                time.monotonic() - started >= max_duration_seconds):
            state.update(status="timed_out", failure_reason="超过最大运行时间")
            _write_log(log_path, "loop_timed_out", cycle=cycle,
                       reason=state["failure_reason"])
            return _finish(state, started)
        try:
            observation = observe(copy.deepcopy(state))
        except Exception as error:
            state.update(status="failed", failure_reason=f"观察异常：{error}")
            _write_log(log_path, "loop_failed", cycle=cycle, reason=state["failure_reason"])
            return _finish(state, started)
        _write_log(log_path, "observation_ready", cycle=cycle,
                   observation=_safe_summary(observation))

        try:
            decision = decide(copy.deepcopy(state), copy.deepcopy(observation))
            if not isinstance(decision, dict):
                raise ValueError("规划结果必须是字典")
            kind = decision.get("kind")
        except Exception as error:
            state.update(status="failed", failure_reason=f"规划异常：{error}")
            _write_log(log_path, "loop_failed", cycle=cycle, reason=state["failure_reason"])
            return _finish(state, started)

        if kind == "stop":
            state.update(status="stopped", stop_reason=str(decision.get("reason", "规划器停止")))
            _write_log(log_path, "loop_stopped", cycle=cycle, reason=state["stop_reason"])
            return _finish(state, started)

        if kind == "done":
            try:
                verdict = _verdict(verify_done(copy.deepcopy(state), copy.deepcopy(observation)),
                                   "任务完成条件已满足")
            except Exception as error:
                verdict = {"success": False, "message": f"完成验证异常：{error}",
                           "evidence": {"error_type": type(error).__name__}}
            state["completion_check"] = verdict
            if verdict["success"]:
                state["status"] = "done"
                _write_log(log_path, "loop_completed", cycle=cycle,
                           evidence=verdict.get("evidence", {}))
            else:
                state.update(status="completion_failed", failure_reason=verdict["message"])
                _write_log(log_path, "loop_failed", cycle=cycle,
                           reason=verdict["message"])
            return _finish(state, started)

        if kind != "action":
            state.update(status="failed", failure_reason=f"未知规划结果类型：{kind}")
            _write_log(log_path, "loop_failed", cycle=cycle, reason=state["failure_reason"])
            return _finish(state, started)

        try:
            action = validate_action(decision.get("action"), allowed_action_types)
        except Exception as error:
            state.update(status="failed", failure_reason=f"动作安全检查失败：{error}")
            _write_log(log_path, "loop_failed", cycle=cycle, reason=state["failure_reason"])
            return _finish(state, started)

        if mode == "preview":
            state["status"] = "preview_ready"
            state["proposed_action"] = action
            state["observation"] = _safe_summary(observation)
            _write_log(log_path, "action_proposed", cycle=cycle, action=action)
            return _finish(state, started)

        if state["action_count"] >= max_actions:
            state.update(status="failed", failure_reason="超过最大动作次数")
            _write_log(log_path, "loop_failed", cycle=cycle, reason=state["failure_reason"])
            return _finish(state, started)

        action_attempt = 0
        while True:
            if state["action_count"] >= max_actions:
                state.update(status="failed", failure_reason="超过最大动作次数")
                _write_log(log_path, "loop_failed", cycle=cycle, reason=state["failure_reason"])
                return _finish(state, started)
            state["action_count"] += 1
            action_attempt += 1
            action_record = {"cycle": cycle, "action": action,
                             "attempt": state["action_count"],
                             "action_attempt": action_attempt}
            _write_log(log_path, "action_started", **action_record)
            try:
                execution = execute(copy.deepcopy(action))
                post_observation = observe(copy.deepcopy(state))
                _write_log(log_path, "post_action_observation_ready", cycle=cycle,
                           observation=_safe_summary(post_observation))
                verdict = _verdict(
                    verify(copy.deepcopy(state), copy.deepcopy(post_observation),
                           copy.deepcopy(action), copy.deepcopy(execution)),
                    "动作验证完成",
                )
            except Exception as error:
                verdict = {"success": False, "message": f"执行或验证异常：{error}",
                           "evidence": {"error_type": type(error).__name__}}
            history_item = {**action_record, "success": verdict["success"],
                            "feedback": verdict["message"],
                            "evidence": verdict.get("evidence", {})}
            state["history"].append(history_item)
            _write_log(log_path, "action_finished", **history_item)
            if verdict["success"]:
                break
            if action_attempt <= max_action_retries:
                state["status"] = "needs_retry"
                _write_log(log_path, "action_retry_scheduled", cycle=cycle,
                           next_attempt=state["action_count"] + 1,
                           reason=verdict["message"])
                continue
            state.update(status="action_failed", failure_reason=verdict["message"])
            _write_log(log_path, "loop_failed", cycle=cycle, reason=state["failure_reason"])
            return _finish(state, started)

    state.update(status="cycle_limit_reached", failure_reason="超过最大循环次数")
    _write_log(log_path, "loop_failed", cycle=max_cycles, reason=state["failure_reason"])
    return _finish(state, started)


def _safe_summary(value):
    """日志只保留可序列化的摘要，避免把整张截图写进 JSONL。"""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in {"image", "image_path", "ocr_path", "items", "low_confidence_items"}:
                result[key] = str(item) if key != "items" else f"{len(item)} items"
            elif isinstance(item, (str, int, float, bool)) or item is None:
                result[key] = item
        return result
    return str(value)


def _finish(state, started):
    state["duration_seconds"] = round(time.monotonic() - started, 4)
    return state
