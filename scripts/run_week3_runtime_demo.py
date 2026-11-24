"""生成一份长任务、失败重试和日志收集示例；不会操作真实桌面。"""

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from src.week3_runtime import run_long_task


def main():
    steps = [
        "确认浏览器入口",
        "打开浏览器",
        "定位地址栏",
        "输入 GUI Agent",
        "提交搜索",
        "检查搜索结果",
    ]
    state = {
        "task": "打开浏览器并搜索 GUI Agent",
        "status": "ready",
        "current_step": 0,
        "steps": [
            {"step_id": number, "description": text, "status": "pending"}
            for number, text in enumerate(steps, 1)
        ],
        "done_condition": "结果页包含 GUI Agent",
        "history": [],
    }

    attempts = {}

    def execute_step(step):
        step_id = step["step_id"]
        attempts[step_id] = attempts.get(step_id, 0) + 1
        return {"step_id": step_id, "attempt": attempts[step_id]}

    def verify_step(step, output):
        # 第 3 步第一次故意返回失败，用于展示重试和日志。
        success = not (step["step_id"] == 3 and output["attempt"] == 1)
        return {
            "success": success,
            "message": "模拟画面符合预期" if success else "模拟地址栏暂未出现",
            "evidence": {"mode": "simulation", **output},
        }

    def verify_task(final_state):
        success = all(step["status"] == "done" for step in final_state["steps"])
        return {
            "success": success,
            "message": "模拟结果页包含 GUI Agent" if success else "模拟完成条件未满足",
            "evidence": {"mode": "simulation"},
        }

    run_dir = PROJECT_DIR / "output" / "week3" / "runtime_demo" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir.mkdir(parents=True, exist_ok=False)
    log_path = run_dir / "events.jsonl"
    result = run_long_task(
        state, execute_step, verify_step, verify_task, log_path,
        max_retries=2, max_actions=20,
    )
    result_path = run_dir / "result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("运行模式：模拟执行，不操作鼠标和键盘")
    print(f"最终状态：{result['status']}")
    print(f"执行次数：{result['action_count']}（包含 1 次重试）")
    print(f"事件日志：{log_path}")
    print(f"结果文件：{result_path}")


if __name__ == "__main__":
    main()
