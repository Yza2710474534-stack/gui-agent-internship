"""把公开 GUI 数据样例送入 Agent，生成离线闭环轨迹。"""

import argparse
import json
import os
from collections import Counter
from pathlib import Path

try:
    from .week3_agent import build_agent, get_current_action, record_feedback
    from .week3_batch import validate
except ImportError:
    from week3_agent import build_agent, get_current_action, record_feedback
    from week3_batch import validate


def read_tasks(input_paths, max_records=3):
    """逐行读取统一 JSONL，最多返回指定数量。"""
    if max_records < 1:
        raise ValueError("max_records 必须大于 0")

    tasks = []
    for input_path in input_paths:
        path = Path(input_path)
        if not path.is_file():
            raise ValueError(f"输入文件不存在：{path}")
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path} 第 {line_number} 行不是有效 JSON") from exc
            error = validate(record)
            if error:
                raise ValueError(f"{path} 第 {line_number} 行：{error}")
            tasks.append(record)
            if len(tasks) == max_records:
                return tasks
    return tasks


def simulate_task(record, provider="mock", model="", base_url="", api_key=""):
    """规划并模拟反馈；不执行数据集中的真实动作。"""
    state = build_agent(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
    ).invoke(record["instruction"])

    while get_current_action(state):
        action = get_current_action(state)
        feedback = f"离线模拟完成第 {action['step_id']} 步，未操作真实界面"
        state = record_feedback(state, True, feedback)

    return {
        "source_dataset": record["source_dataset"],
        "task_id": record["task_id"],
        "instruction": record["instruction"],
        "execution_mode": "offline_simulation",
        "reference_step_count": len(record["steps"]),
        "agent_state": state,
    }


def run_demo(input_paths, output_path, max_records=3, provider="mock", model="",
             base_url="", api_key=""):
    """处理若干任务并保存轨迹及汇总。"""
    records = read_tasks(input_paths, max_records)
    trajectories = [
        simulate_task(record, provider, model, base_url, api_key)
        for record in records
    ]
    source_counts = Counter(item["source_dataset"] for item in trajectories)
    completed = sum(item["agent_state"]["status"] == "done" for item in trajectories)
    result = {
        "summary": {
            "provider": provider,
            "total_tasks": len(trajectories),
            "completed_tasks": completed,
            "source_counts": dict(source_counts),
            "real_desktop_actions": 0,
        },
        "trajectories": trajectories,
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="统一格式的 JSONL 文件")
    parser.add_argument("--output", type=Path, default=Path("output/week3/day6_trajectories.json"))
    parser.add_argument("--max-records", type=int, default=3)
    parser.add_argument("--provider", choices=["mock", "api", "ollama"], default="mock")
    parser.add_argument("--model", default="")
    parser.add_argument("--base-url", default="")
    args = parser.parse_args()

    api_key = (
        os.getenv("GUI_AGENT_API_KEY")
        or os.getenv("DEEPSEEK_API_KEY")
        or ""
    ).strip()
    try:
        result = run_demo(
            args.inputs,
            args.output,
            args.max_records,
            args.provider,
            args.model,
            args.base_url,
            api_key,
        )
    except (ValueError, RuntimeError) as error:
        parser.exit(1, f"运行失败：{error}\n")

    summary = result["summary"]
    print(f"读取任务：{summary['total_tasks']} 条")
    print(f"完成轨迹：{summary['completed_tasks']} 条")
    print(f"数据来源：{summary['source_counts']}")
    print("真实桌面操作：0 次")
    print(f"结果文件：{args.output.resolve()}")


if __name__ == "__main__":
    main()
