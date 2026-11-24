"""第三周基础 Agent：任务拆解、步骤选择和反馈记录。

当前文件只做离线演示，不会控制鼠标、键盘，也不会发送网络请求。
"""

import argparse
import copy
import json
import os
from pathlib import Path

try:
    from .week3_model import call_model
except ImportError:
    from week3_model import call_model


def validate_task(data):
    """把字符串或字典整理为统一输入。"""
    if isinstance(data, str):
        task = data.strip()
    elif isinstance(data, dict):
        task = str(data.get("task", "")).strip()
    else:
        raise ValueError("任务必须是字符串或包含 task 的字典")

    if not task:
        raise ValueError("任务不能为空")
    return {"task": task}


def build_planner_prompt(data):
    """生成以后可直接交给大模型的提示词。"""
    task = data["task"]
    prompt = (
        "你是桌面 GUI 任务规划器。请把任务拆成 1 到 8 个可执行步骤，"
        "最后一步必须检查任务是否完成。只输出 JSON，格式为："
        '{"steps":["步骤1","步骤2"],"done_condition":"完成条件"}。'
        f"\n用户任务：{task}"
    )
    return {**data, "prompt": prompt}


def mock_model(data):
    """保留第4天的模拟模型入口。"""
    output = call_model(data["prompt"], provider="mock")
    return {**data, "model_output": output, "model_name": "mock"}


def parse_plan(data):
    """检查模型输出，并建立可跟踪的 Agent 状态。"""
    try:
        plan = json.loads(data["model_output"])
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("模型没有返回有效 JSON 计划") from exc

    steps = plan.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 8:
        raise ValueError("计划必须包含 1 到 8 个步骤")
    if any(not isinstance(step, str) or not step.strip() for step in steps):
        raise ValueError("每个步骤都必须是非空文字")

    return {
        "task": data["task"],
        "model_name": data.get("model_name", "unknown"),
        "status": "ready",
        "current_step": 0,
        "steps": [
            {"step_id": index, "description": text.strip(), "status": "pending"}
            for index, text in enumerate(steps, start=1)
        ],
        "done_condition": str(plan.get("done_condition", "")).strip(),
        "history": [],
    }


def build_agent(provider="mock", model="", base_url="", api_key="", image_path=None):
    """用 LangChain 连接任务输入、模型调用和计划解析。"""
    from langchain_core.runnables import RunnableLambda

    def run_model(data):
        output = call_model(
            data["prompt"],
            provider=provider,
            model=model,
            base_url=base_url,
            api_key=api_key,
            image_path=image_path,
        )
        return {**data, "model_output": output, "model_name": provider}

    return (
        RunnableLambda(validate_task)
        | RunnableLambda(build_planner_prompt)
        | RunnableLambda(run_model)
        | RunnableLambda(parse_plan)
    )


def build_offline_agent():
    """第4天兼容入口：始终使用模拟模型。"""
    return build_agent(provider="mock")


def get_current_action(state):
    """读取下一步动作，不修改原状态。"""
    index = state["current_step"]
    if state["status"] == "done" or index >= len(state["steps"]):
        return None
    return copy.deepcopy(state["steps"][index])


def record_feedback(state, success, message):
    """记录一步的执行反馈，并返回新的状态。"""
    new_state = copy.deepcopy(state)
    action = get_current_action(new_state)
    if action is None:
        raise ValueError("当前没有待执行步骤")

    index = new_state["current_step"]
    new_state["history"].append(
        {
            "step_id": action["step_id"],
            "success": bool(success),
            "feedback": str(message),
        }
    )

    if success:
        new_state["steps"][index]["status"] = "done"
        new_state["current_step"] += 1
        if new_state["current_step"] == len(new_state["steps"]):
            new_state["status"] = "done"
        else:
            new_state["status"] = "running"
    else:
        new_state["steps"][index]["status"] = "retry"
        new_state["status"] = "needs_retry"

    return new_state


def main():
    parser = argparse.ArgumentParser(description="第三周基础 Agent 离线演示")
    parser.add_argument("task", help="要拆解的 GUI 任务")
    parser.add_argument("--simulate", action="store_true", help="模拟每一步执行成功")
    parser.add_argument("--output", help="把结果保存为 JSON 文件")
    parser.add_argument("--provider", choices=["mock", "api", "ollama"], default="mock")
    parser.add_argument("--model", default="", help="API 或 Ollama 的模型名称")
    parser.add_argument("--base-url", default="", help="模型服务地址")
    parser.add_argument("--image", help="可选的界面截图")
    args = parser.parse_args()

    state = build_agent(
        provider=args.provider,
        model=args.model,
        base_url=args.base_url,
        api_key=(
            os.getenv("GUI_AGENT_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
            or ""
        ).strip(),
        image_path=args.image,
    ).invoke(args.task)
    print(f"模型方式：{args.provider}；本程序不操作鼠标和键盘")
    print(f"任务：{state['task']}")
    for step in state["steps"]:
        print(f"{step['step_id']}. {step['description']}")

    if args.simulate:
        while get_current_action(state):
            action = get_current_action(state)
            state = record_feedback(state, True, f"模拟完成：{action['description']}")
        print(f"最终状态：{state['status']}，完成 {len(state['history'])} 步")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"结果已保存：{output_path.resolve()}")


if __name__ == "__main__":
    main()
