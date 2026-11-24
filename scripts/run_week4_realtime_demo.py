"""生成第四周实时循环的离线预览记录，不操作真实桌面。"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.week4_realtime import run_realtime_loop


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_DIR / "output" / "week4")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.output_dir / "realtime_preview_events.jsonl"
    result = run_realtime_loop(
        "打开浏览器并搜索 GUI Agent",
        observe=lambda state: {
            "image_path": "offline/screen.png",
            "ocr_path": "offline/ocr.json",
            "image_size": [1470, 956],
            "cycle": state["cycle"],
        },
        decide=lambda state, observation: {
            "kind": "action",
            "action": {"type": "click", "x": 400, "y": 65},
        },
        execute=lambda action: (_ for _ in ()).throw(
            RuntimeError("preview 模式不应调用 execute")
        ),
        verify=lambda *args: True,
        verify_done=lambda *args: True,
        log_path=log_path,
        mode="preview",
    )
    result_path = args.output_dir / "realtime_preview.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"离线预览完成：{result_path}")
    print(f"状态：{result['status']}；建议动作：{result['proposed_action']}")
    print(f"事件日志：{log_path}")


if __name__ == "__main__":
    main()
