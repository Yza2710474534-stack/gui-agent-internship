"""识别截图中的中英文文字，输出原始图片坐标。"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import cv2
import easyocr


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_DIR / "artifacts" / "easyocr"
DEFAULT_IMAGE = PROJECT_DIR / "output" / "screenshots" / "orc测试图像.png"


class OCREngine:
    def __init__(self, download_enabled=True):
        self.reader = easyocr.Reader(
            ["ch_sim", "en"],
            gpu=False,
            model_storage_directory=str(MODEL_DIR / "models"),
            user_network_directory=str(MODEL_DIR / "user_network"),
            download_enabled=download_enabled,
            verbose=False,
        )

    def recognize(self, image_path: Path, min_confidence: float = 0.3, scale: int = 3) -> dict:
        image_path = Path(image_path)
        if not 0 <= min_confidence <= 1:
            raise ValueError("置信度阈值必须在 0 到 1 之间")
        if not isinstance(scale, int) or not 1 <= scale <= 6:
            raise ValueError("识别放大倍数必须是1到6之间的整数")
        if not image_path.is_file():
            raise ValueError(f"图片不存在：{image_path}")
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"无法读取图片：{image_path}")
        height, width = image.shape[:2]

        # 菜单文字较小，放大三倍识别，再将坐标还原到输入图片。
        enlarged = cv2.resize(
            image, (width * scale, height * scale), interpolation=cv2.INTER_CUBIC
        )
        results = self.reader.readtext(
            enlarged, detail=1, paragraph=False, width_ths=0.1
        )
        items = []
        low_confidence_items = []
        for box, text, confidence in results:
            original_box = [[float(x) / scale, float(y) / scale] for x, y in box]
            center = [
                sum(point[0] for point in original_box) / 4,
                sum(point[1] for point in original_box) / 4,
            ]
            item = {
                "text": text,
                "confidence": float(confidence),
                "bbox": original_box,
                "center": center,
            }
            if confidence < min_confidence:
                low_confidence_items.append(item)
            else:
                items.append(item)
        return {
            "image": str(image_path.resolve()),
            "recognition_scale": scale,
            "image_size": [width, height],
            "coordinate_space": "original_input_image",
            "min_confidence": min_confidence,
            "items": items,
            "low_confidence_items": low_confidence_items,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", nargs="?", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--target", default="窗口")
    parser.add_argument("--min-confidence", type=float, default=0.3)
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error(f"图片不存在：{args.image}")

    print("正在加载中英文 OCR，首次运行可能需要下载模型……", flush=True)
    engine = OCREngine()
    result = engine.recognize(args.image, args.min_confidence)
    print(f"图片尺寸：{result['image_size'][0]} × {result['image_size'][1]}")
    for item in result["items"]:
        x, y = item["center"]
        print(f"文字：{item['text']} | 置信度：{item['confidence']:.3f} | 图内中心：({x:g}, {y:g})")
    for item in result["low_confidence_items"]:
        print(f"低置信度，未采用：{item['text']} | 置信度：{item['confidence']:.3f}")

    target = "".join(args.target.split())
    matches = [item for item in result["items"] if "".join(item["text"].split()) == target]
    result["target"] = args.target
    result["target_matches"] = matches
    if matches:
        print(f"找到目标：{args.target}（{len(matches)} 处）")
    else:
        print(f"未找到完全匹配的目标：{args.target}；请检查识别文字及置信度。")

    output_dir = PROJECT_DIR / "output" / "ocr"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"ocr_{datetime.now():%Y%m%d_%H%M%S_%f}.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"识别结果已保存：{output}")
    print("以上坐标相对于输入图片左上角，本程序没有执行鼠标操作。")


if __name__ == "__main__":
    main()
