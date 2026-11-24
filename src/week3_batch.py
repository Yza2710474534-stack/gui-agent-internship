"""批量检查统一轨迹，稳定划分训练集和验证集，并输出统计。"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def validate(record):
    """检查一条统一轨迹；返回错误文字，空字符串表示正常。"""
    if not isinstance(record, dict):
        return "记录不是JSON对象"
    for name in ("source_dataset", "task_id", "instruction", "environment", "steps", "evaluation"):
        if name not in record:
            return f"缺少字段：{name}"
    if not str(record["task_id"]).strip() or not str(record["instruction"]).strip():
        return "任务编号或指令为空"
    if not isinstance(record["steps"], list):
        return "steps不是列表"
    for index, step in enumerate(record["steps"], start=1):
        if not isinstance(step, dict) or step.get("step_id") != index:
            return f"第{index}步格式错误"
    return ""


def action_name(step):
    """优先读取标准动作类型；WebArena文本动作使用简单关键词归类。"""
    name = str(step.get("action_type", "")).upper()
    if name and name != "UNKNOWN":
        return name
    text = str(step.get("action_text", "")).lower()
    for keyword, label in (("click", "CLICK"), ("fill", "TYPE"), ("type", "TYPE"),
                           ("select", "SELECT"), ("stop", "STOP")):
        if keyword in text:
            return label
    return "OTHER"


def choose_split(task_id, validation_percent=10):
    """同一个task_id每次运行都会进入相同分组。"""
    if not isinstance(validation_percent, int) or not 1 <= validation_percent <= 50:
        raise ValueError("验证集比例必须是1到50之间的整数")
    number = int(hashlib.sha256(str(task_id).encode("utf-8")).hexdigest()[:8], 16) % 100
    return "validation" if number < validation_percent else "train"


def split_and_report(input_paths, output_dir, validation_percent=10):
    """逐行处理JSONL，避免一次把大数据全部放入内存。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {name: (output_dir / f"{name}.jsonl").open("w", encoding="utf-8")
             for name in ("train", "validation")}
    source_counts, action_counts, split_counts = Counter(), Counter(), Counter()
    errors, seen = [], set()
    total = valid = 0
    try:
        for input_path in input_paths:
            path = Path(input_path)
            if not path.is_file():
                raise ValueError(f"输入文件不存在：{path}")
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                total += 1
                try:
                    record = json.loads(line)
                    error = validate(record)
                except json.JSONDecodeError:
                    record, error = None, "JSON格式错误"
                if not error and record["task_id"] in seen:
                    error = "任务编号重复"
                if error:
                    errors.append({"file": str(path), "line": line_number, "error": error})
                    continue
                seen.add(record["task_id"])
                valid += 1
                split = choose_split(record["task_id"], validation_percent)
                files[split].write(json.dumps(record, ensure_ascii=False) + "\n")
                split_counts[split] += 1
                source_counts[record["source_dataset"]] += 1
                action_counts.update(action_name(step) for step in record["steps"])
    finally:
        for file in files.values():
            file.close()
    report = {
        "total_records": total,
        "valid_records": valid,
        "invalid_records": total - valid,
        "validation_percent_rule": validation_percent,
        "split_counts": dict(split_counts),
        "source_counts": dict(source_counts),
        "action_counts": dict(action_counts),
        "errors": errors[:100],
    }
    (output_dir / "statistics.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="一个或多个统一JSONL")
    parser.add_argument("--output-dir", type=Path, default=Path("data/week3/splits"))
    parser.add_argument("--validation-percent", type=int, default=10)
    args = parser.parse_args()
    try:
        report = split_and_report(args.inputs, args.output_dir, args.validation_percent)
    except ValueError as error:
        parser.exit(1, f"处理失败：{error}\n")
    print(f"读取：{report['total_records']} 条")
    print(f"有效：{report['valid_records']} 条；无效：{report['invalid_records']} 条")
    print(f"训练集：{report['split_counts'].get('train', 0)} 条")
    print(f"验证集：{report['split_counts'].get('validation', 0)} 条")
    print(f"统计文件：{(args.output_dir / 'statistics.json').resolve()}")


if __name__ == "__main__":
    main()
