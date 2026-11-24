"""单步实时点击的业务完成条件，独立于截图文件保存检查。"""

import json
import re
from pathlib import Path

from .week4_search import verify_post_action_observation


def extract_expected_text(task):
    match = re.search(r"确认出现\s*[“‘'\"]?([^，。；;\n]{1,80})", task)
    return match.group(1).strip(" ”’'\"") if match else None


def verify_click_outcome(observation, expected_text):
    evidence = verify_post_action_observation(None, observation, None, None)
    if not evidence["success"]:
        return evidence
    if not expected_text:
        return {**evidence, "message": "动作后证据已保存，未指定业务完成条件",
                "business_verified": False}
    try:
        ocr = json.loads(Path(observation["ocr"]).read_text(encoding="utf-8"))
        normalize = lambda value: "".join(value.split()).casefold()
        expected = normalize(expected_text)
        matches = [item["text"] for item in ocr.get("items", [])
                   if normalize(item.get("text", "")) == expected]
    except (OSError, ValueError, TypeError, AttributeError) as error:
        return {"success": False, "message": f"无法读取完成条件 OCR：{error}"}
    return {"success": bool(matches), "business_verified": bool(matches),
            "message": f"已确认出现“{expected_text}”" if matches else f"未观察到预期文字“{expected_text}”",
            "evidence": {**evidence["evidence"], "expected_text": expected_text,
                         "matched_text": matches}}


def verify_click_completion(state, observation, expected_text):
    history = state.get("history", [])
    if not history or not all(item.get("success") is True for item in history):
        return {"success": False, "message": "没有通过验证的点击动作"}
    return verify_click_outcome(observation, expected_text)
