"""第三周数据处理：把三种公开GUI任务转换成简单统一格式。"""

import argparse
import json
from pathlib import Path


def normalize_webarena(record):
    """转换一条 WebArena 任务，不修改原始字典。"""
    if not isinstance(record, dict):
        raise ValueError("一条任务必须是JSON对象")
    for name in ("task_id", "intent", "sites"):
        if name not in record:
            raise ValueError(f"WebArena任务缺少字段：{name}")
    if not str(record["intent"]).strip():
        raise ValueError("任务指令不能为空")
    if not isinstance(record["sites"], list):
        raise ValueError("sites必须是列表")

    reference = record.get("reference_action_sequence") or {}
    raw_steps = reference.get("action_sequence") or []
    if not isinstance(raw_steps, list):
        raise ValueError("action_sequence必须是列表")
    steps = [
        {"step_id": index, "action_text": str(action)}
        for index, action in enumerate(raw_steps, start=1)
    ]
    evaluation = record.get("eval") or {}
    return {
        "source_dataset": "webarena",
        "task_id": f"webarena_{record['task_id']}",
        "instruction": str(record["intent"]).strip(),
        "environment": {
            "sites": list(record["sites"]),
            "start_url": record.get("start_url", ""),
            "require_login": bool(record.get("require_login", False)),
        },
        "steps": steps,
        "evaluation": {
            "types": list(evaluation.get("eval_types") or []),
            "reference_url": evaluation.get("reference_url"),
        },
    }


def normalize_screenagent(record):
    """转换一条 ScreenAgent 记录，只保留任务、截图信息和动作。"""
    if not isinstance(record, dict):
        raise ValueError("一条任务必须是JSON对象")
    for name in ("session_id", "task_prompt", "actions"):
        if name not in record:
            raise ValueError(f"ScreenAgent任务缺少字段：{name}")
    if not str(record["task_prompt"]).strip() or not isinstance(record["actions"], list):
        raise ValueError("ScreenAgent任务或动作格式错误")
    steps = []
    for index, action in enumerate(record["actions"], start=1):
        if not isinstance(action, dict):
            raise ValueError("ScreenAgent动作必须是JSON对象")
        steps.append({
            "step_id": index,
            "action_type": str(action.get("action_type", "UNKNOWN")),
            "action_text": str(action.get("element", "")),
        })
    return {
        "source_dataset": "screenagent",
        "task_id": f"screenagent_{record['session_id']}",
        "instruction": str(record["task_prompt"]).strip(),
        "environment": {
            "image": record.get("saved_image_name"),
            "image_size": [record.get("video_width"), record.get("video_height")],
        },
        "steps": steps,
        "evaluation": {"types": [], "reference_url": None},
    }


def normalize_mind2web(record):
    """转换一条 Mind2Web 记录，不保留体积很大的网页HTML。"""
    if not isinstance(record, dict):
        raise ValueError("一条任务必须是JSON对象")
    for name in ("annotation_id", "confirmed_task", "actions"):
        if name not in record:
            raise ValueError(f"Mind2Web任务缺少字段：{name}")
    actions = record["actions"]
    descriptions = record.get("action_reprs") or []
    if not isinstance(actions, list) or not isinstance(descriptions, list):
        raise ValueError("Mind2Web动作格式错误")
    steps = []
    for index, action in enumerate(actions, start=1):
        if not isinstance(action, dict):
            raise ValueError("Mind2Web动作必须是JSON对象")
        operation = action.get("operation") or {}
        steps.append({
            "step_id": index,
            "action_id": action.get("action_uid"),
            "action_type": str(operation.get("op", "UNKNOWN")),
            "action_value": operation.get("value"),
            "action_text": descriptions[index - 1] if index <= len(descriptions) else "",
        })
    return {
        "source_dataset": "mind2web",
        "task_id": f"mind2web_{record['annotation_id']}",
        "instruction": str(record["confirmed_task"]).strip(),
        "environment": {
            "website": record.get("website"),
            "domain": record.get("domain"),
            "subdomain": record.get("subdomain"),
        },
        "steps": steps,
        "evaluation": {"types": [], "reference_url": None},
    }


def detect_source(record):
    """根据有代表性的字段判断数据来源。"""
    if "confirmed_task" in record and "annotation_id" in record:
        return "mind2web"
    if "task_prompt" in record and "session_id" in record:
        return "screenagent"
    if "intent" in record and "task_id" in record:
        return "webarena"
    raise ValueError("无法判断数据来源，请检查字段")


def normalize_record(record, source="auto"):
    source = detect_source(record) if source == "auto" else source.lower()
    functions = {
        "webarena": normalize_webarena,
        "screenagent": normalize_screenagent,
        "mind2web": normalize_mind2web,
    }
    if source not in functions:
        raise ValueError(f"不支持的数据来源：{source}")
    return functions[source](record)


def load_records(path):
    """读取单条JSON或JSON数组。"""
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"输入文件不存在：{path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON格式错误：第{error.lineno}行") from error
    # Hugging Face rows接口外层含rows，每一项的row才是数据。
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        return [item["row"] for item in data["rows"] if isinstance(item, dict) and "row" in item]
    return data if isinstance(data, list) else [data]


def preprocess(input_path, output_path, source="auto"):
    """转换并保存JSONL；每一行是一条任务。"""
    records = [normalize_record(item, source) for item in load_records(input_path)]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(json.dumps(item, ensure_ascii=False) for item in records) + "\n"
    output_path.write_text(content, encoding="utf-8")
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="原始JSON文件")
    parser.add_argument("output", type=Path, help="输出JSONL文件")
    parser.add_argument("--source", choices=("auto", "webarena", "screenagent", "mind2web"),
                        default="auto", help="默认根据字段自动判断")
    args = parser.parse_args()
    try:
        records = preprocess(args.input, args.output, args.source)
    except ValueError as error:
        parser.exit(1, f"处理失败：{error}\n")
    print(f"处理完成：{len(records)} 条")
    print(f"输出文件：{args.output.resolve()}")


if __name__ == "__main__":
    main()
