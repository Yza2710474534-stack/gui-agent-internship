"""读取 OCR 结果，用 OpenCV 绘制指定文字的边界框和中心点。"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


PROJECT_DIR = Path(__file__).resolve().parents[1]


def draw_target(image: np.ndarray, items: list[dict], target: str):
    """返回标注图片和匹配记录，不修改输入图像。"""
    normalized_target = "".join(target.split())
    matches = [
        item for item in items
        if "".join(item["text"].split()) == normalized_target
    ]
    if not matches:
        raise ValueError(f"OCR 结果中没有识别成功的目标：{target}")

    marked = image.copy()
    for item in matches:
        points = np.asarray(item["bbox"], dtype=float)
        center = np.asarray(item["center"], dtype=float)
        if points.shape != (4, 2) or center.shape != (2,):
            raise ValueError("边界框应有四个角，中心点应有两个坐标")
        if not np.isfinite(points).all() or not np.isfinite(center).all():
            raise ValueError("坐标必须是有限数值")

        # OpenCV 颜色顺序是 BGR。绿色框标范围，红点标中心。
        polygon = np.rint(points).astype(np.int32).reshape((-1, 1, 2))
        cv2.polylines(marked, [polygon], True, (0, 255, 0), 1)
        center_pixel = tuple(int(round(value)) for value in center)
        cv2.circle(marked, center_pixel, 2, (0, 0, 255), -1)
    return marked, matches


def save_png(path: Path, image: np.ndarray):
    if not cv2.imwrite(str(path), image):
        raise RuntimeError(f"图片保存失败：{path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", nargs="?", type=Path, help="OCR JSON 文件，默认最新一份")
    parser.add_argument("--target", default="编辑")
    args = parser.parse_args()
    result_path = args.result
    if result_path is None:
        candidates = sorted((PROJECT_DIR / "output" / "ocr").glob("ocr_*.json"))
        if not candidates:
            parser.error("没有 OCR 结果，请先运行 ocr_engine.py")
        result_path = candidates[-1]

    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("coordinate_space") != "original_input_image":
        parser.error("此模块要求 OCR 坐标已还原到原始输入图片")
    image_path = Path(result["image"])
    image = cv2.imread(str(image_path))
    if image is None:
        parser.error(f"无法读取对应截图：{image_path}")
    height, width = image.shape[:2]
    if result["image_size"] != [width, height]:
        parser.error("当前图片尺寸与 OCR 记录不一致，请重新识别")
    try:
        marked, matches = draw_target(image, result["items"], args.target)
    except ValueError as error:
        parser.error(str(error))

    output_dir = PROJECT_DIR / "output" / "visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    marked_path = output_dir / f"marked_{stamp}.png"
    save_png(marked_path, marked)
    print(f"读取结果：{result_path}")
    print(f"标注截图：{marked_path}")

    for index, item in enumerate(matches, 1):
        points = np.asarray(item["bbox"])
        left = max(0, int(np.floor(points[:, 0].min())) - 12)
        top = max(0, int(np.floor(points[:, 1].min())) - 12)
        right = min(width, int(np.ceil(points[:, 0].max())) + 13)
        bottom = min(height, int(np.ceil(points[:, 1].max())) + 13)
        crop = marked[top:bottom, left:right]
        if crop.size == 0:
            raise ValueError("目标框位于图片之外，无法生成局部预览")
        # 放大图只用于观看；坐标仍以原始图片为准。
        zoom = cv2.resize(crop, None, fx=6, fy=6, interpolation=cv2.INTER_NEAREST)
        zoom_path = output_dir / f"target_zoom_{stamp}_{index}.png"
        save_png(zoom_path, zoom)
        x, y = item["center"]
        print(f"目标：{item['text']} | 原图中心：({x:.2f}, {y:.2f})")
        print(f"局部放大图：{zoom_path}")
    print("绿色框表示文字范围，红点表示中心。原始截图未修改。")


if __name__ == "__main__":
    main()
