from datetime import datetime
from pathlib import Path
import argparse
import json
import math
import time

import cv2
import mss
import numpy as np


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "output" / "screenshots"


def select_monitor(monitors, monitor_index=None):
    """默认取第一块真实显示器；0号是全部显示器的合并区域。"""
    valid = [i for i, m in enumerate(monitors) if m["width"] > 0 and m["height"] > 0]
    if not valid:
        raise RuntimeError("未检测到可用屏幕，请在本地终端运行并检查屏幕录制权限")
    if monitor_index is None:
        monitor_index = next((i for i in valid if i != 0), valid[0])
    if monitor_index not in valid:
        raise ValueError(f"显示器编号不可用：{monitor_index}")
    return dict(monitors[monitor_index])


def prepare_frame(image, region, output_size=None):
    """可选缩放，并保留原始屏幕区域用于还原坐标。尺寸顺序为宽、高。"""
    if image is None or image.size == 0:
        raise ValueError("截图不能为空")
    if output_size is not None:
        if len(output_size) != 2 or any(not isinstance(n, int) or n <= 0 for n in output_size):
            raise ValueError("输出宽高必须是正整数")
        image = cv2.resize(image, tuple(output_size), interpolation=cv2.INTER_AREA)
    height, width = image.shape[:2]
    metadata = {
        "captured_at": datetime.now().isoformat(timespec="microseconds"),
        "screen_region": [region[k] for k in ("left", "top", "width", "height")],
        "image_size": [width, height],
        "scale_to_screen": [region["width"] / width, region["height"] / height],
    }
    return image, metadata


def capture_with_metadata(monitor_index=None, output_size=None):
    """使用 MSS 跨平台截图，并返回图片及坐标换算信息。"""
    with mss.MSS() as tool:
        region = select_monitor(tool.monitors, monitor_index)
        image = cv2.cvtColor(np.array(tool.grab(region)), cv2.COLOR_BGRA2BGR)
    return prepare_frame(image, region, output_size)


def capture_full_screen(monitor_index: int | None = None) -> np.ndarray:
    """保留原来的简单调用方式。"""
    image, _ = capture_with_metadata(monitor_index)
    return image


def capture_region(left: int, top: int, width: int, height: int) -> np.ndarray:
    """截取屏幕中的指定矩形区域。"""
    if any(not isinstance(v, int) for v in (left, top, width, height)) or width <= 0 or height <= 0:
        raise ValueError("截图区域的宽度和高度必须大于 0")

    region = {
        "left": left,
        "top": top,
        "width": width,
        "height": height,
    }

    with mss.MSS() as screenshot_tool:
        monitors = screenshot_tool.monitors
        actual = monitors[1:] if len(monitors) > 1 else monitors
        if not any(m["left"] <= left and m["top"] <= top
                   and left + width <= m["left"] + m["width"]
                   and top + height <= m["top"] + m["height"] for m in actual):
            raise ValueError("截图区域不在一块有效显示器内")
        screenshot = screenshot_tool.grab(region)

    image = np.array(screenshot)
    return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)


def save_image(image: np.ndarray, prefix: str = "screen", output_dir=None) -> Path:
    """保存截图，并返回生成的图片路径。"""
    if image is None or image.size == 0:
        raise ValueError("不能保存空图片")
    if not prefix or any(c in prefix for c in ("/", "\\")):
        raise ValueError("文件名前缀不能包含路径分隔符")
    directory = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_path = directory / f"{prefix}_{timestamp}.png"

    if not cv2.imwrite(str(output_path), image):
        raise RuntimeError(f"截图保存失败：{output_path}")

    return output_path


def capture_sequence(count=3, interval=0.5, output_size=None, monitor_index=None, output_dir=None):
    """连续截图，逐张保存图片和同名 JSON；不承诺固定帧率。"""
    if not isinstance(count, int) or not 1 <= count <= 1000:
        raise ValueError("截图数量必须是1到1000之间的整数")
    if not math.isfinite(interval) or interval < 0:
        raise ValueError("截图间隔必须是大于等于0的有限数值")
    records = []
    for i in range(count):
        if i:
            time.sleep(interval)
        start = time.monotonic()
        image, metadata = capture_with_metadata(monitor_index, output_size)
        metadata["capture_seconds"] = time.monotonic() - start
        path = save_image(image, f"screen_{i + 1}", output_dir)
        metadata["image"] = path.name
        path.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        records.append({**metadata, "path": str(path)})
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="截图并记录分辨率；可连续截图")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--size", type=int, nargs=2, help="输出图片宽高；省略则保留原始大小")
    parser.add_argument("--monitor", type=int, help="显示器编号；默认第一块真实显示器")
    args = parser.parse_args()
    try:
        records = capture_sequence(args.count, args.interval, args.size, args.monitor)
        for record in records:
            print(f"截图成功：{record['path']}")
            print(f"截图尺寸：{record['image_size'][0]} × {record['image_size'][1]}")
            print(f"还原比例：{record['scale_to_screen']}")
    except (ValueError, RuntimeError) as error:
        parser.exit(1, f"截图失败：{error}\n")
