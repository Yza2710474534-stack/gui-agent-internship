"""第五周第一天：检查项目是否能读取并保存真实屏幕截图。

该探针只读取屏幕，不发送鼠标键盘事件。即使截图失败，也会写出结果摘要，
方便把 macOS 屏幕录制权限问题和代码问题区分开。
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_DIR / "output" / "week5" / "capture_probe"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.screen_capture import capture_with_metadata, save_image


def run_probe(output_dir, *, monitor_index=None, output_size=None,
              capture=capture_with_metadata, save=save_image):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "status": "capture_failed",
        "project_mss": "not_checked",
        "mouse_keyboard_actions": 0,
    }
    try:
        image, metadata = capture(monitor_index, output_size)
        image_path = Path(save(image, prefix="week5_probe", output_dir=output_dir))
        result.update(
            status="capture_ready",
            project_mss="available",
            image=str(image_path.resolve()),
            image_size=metadata["image_size"],
            screen_region=metadata["screen_region"],
            scale_to_screen=metadata["scale_to_screen"],
        )
    except Exception as error:
        result.update(
            project_mss="unavailable",
            error_type=type(error).__name__,
            error=str(error),
        )
    result_path = output_dir / "result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description="检查项目 MSS 屏幕采集能力")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--monitor", type=int)
    parser.add_argument("--size", type=int, nargs=2, metavar=("WIDTH", "HEIGHT"))
    args = parser.parse_args()
    result = run_probe(args.output_dir, monitor_index=args.monitor, output_size=args.size)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "capture_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
