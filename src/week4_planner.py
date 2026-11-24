"""第四周第三天：把模型输出限制为可审查的结构化决策。"""

import copy
import json

try:
    from .week4_realtime import validate_action
except ImportError:
    from week4_realtime import validate_action


DECISION_KINDS = frozenset({"action", "done", "stop"})


def build_structured_planner_prompt(task, observation):
    """生成要求模型只返回 JSON 决策的提示词。"""
    if not isinstance(task, str) or not task.strip():
        raise ValueError("task 不能为空")
    safe_observation = {
        key: value for key, value in observation.items()
        if key in {"image", "ocr", "image_size", "screen_region", "ocr_item_count",
                   "low_confidence_item_count"}
    } if isinstance(observation, dict) else {}
    return (
        "你是 GUI 任务规划器。只返回一个 JSON 对象，不要 Markdown、解释、代码或 shell 命令。\n"
        f"任务：{task.strip()}\n"
        f"当前观察：{json.dumps(safe_observation, ensure_ascii=False, default=str)}\n"
        "允许的输出格式只有：\n"
        '{"kind":"action","action":{"type":"click","x":100,"y":100}}\n'
        '{"kind":"action","action":{"type":"type_text","text":"GUI Agent"}}\n'
        '{"kind":"action","action":{"type":"scroll","amount":-3}}\n'
        '{"kind":"action","action":{"type":"wait","seconds":1}}\n'
        '{"kind":"done"}\n'
        '{"kind":"stop","reason":"需要人工确认"}\n'
        "动作类型只能是 click、type_text、scroll、wait；禁止任意代码、文件删除和命令执行。"
    )


def parse_structured_decision(model_output):
    """解析并严格校验模型返回的单个决策。"""
    if isinstance(model_output, bytes):
        model_output = model_output.decode("utf-8")
    if isinstance(model_output, str):
        try:
            decision = json.loads(model_output)
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError("模型输出不是有效 JSON") from error
    elif isinstance(model_output, dict):
        decision = copy.deepcopy(model_output)
    else:
        raise ValueError("模型输出必须是 JSON 字符串或字典")

    if not isinstance(decision, dict) or decision.get("kind") not in DECISION_KINDS:
        raise ValueError("决策 kind 必须是 action、done 或 stop")
    kind = decision["kind"]
    if kind == "action":
        if set(decision) != {"kind", "action"}:
            raise ValueError("action 决策只能包含 kind 和 action")
        decision["action"] = validate_action(decision.get("action"))
    elif kind == "done":
        if set(decision) != {"kind"}:
            raise ValueError("done 决策不能附带其他字段")
    else:
        if set(decision) != {"kind", "reason"}:
            raise ValueError("stop 决策必须只包含 kind 和 reason")
        reason = decision.get("reason")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 200:
            raise ValueError("stop reason 必须是 1 到 200 个字符")
        decision["reason"] = reason.strip()
    return decision


def make_model_decider(task, call_model):
    """将第三周模型调用函数包装为 run_realtime_loop 所需的 decide。"""
    if not callable(call_model):
        raise ValueError("call_model 必须可调用")

    def decide(_state, observation):
        prompt = build_structured_planner_prompt(task, observation)
        return parse_structured_decision(call_model(prompt))

    return decide

