"""第四周第二天：把一次截图和 OCR 结果整理成实时循环的观察数据。"""

import json
from pathlib import Path

try:
    from .ocr_engine import OCREngine
    from .screen_capture import capture_with_metadata, save_image
except ImportError:
    from ocr_engine import OCREngine
    from screen_capture import capture_with_metadata, save_image


def capture_observation(
    engine,
    output_dir,
    *,
    monitor_index=None,
    output_size=None,
    min_confidence=0.3,
    scale=3,
    capture=capture_with_metadata,
    save=save_image,
):
    """截图、保存图片和 OCR JSON，并返回循环可消费的观察字典。

    ``capture`` 和 ``save`` 可注入测试替身；默认实现只读取屏幕，不发送
    鼠标键盘事件。OCR 结果必须与保存截图尺寸一致，避免坐标空间错配。
    """
    if not hasattr(engine, "recognize") or not callable(engine.recognize):
        raise ValueError("engine 必须提供可调用的 recognize 方法")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    image, metadata = capture(monitor_index, output_size)
    image_path = Path(save(image, prefix="realtime", output_dir=output_dir))
    ocr = engine.recognize(image_path, min_confidence=min_confidence, scale=scale)
    expected_size = metadata.get("image_size")
    if ocr.get("image_size") != expected_size:
        raise ValueError("OCR 尺寸与截图元数据不一致，拒绝生成观察结果")

    ocr_path = image_path.with_suffix(".ocr.json")
    ocr_path.write_text(json.dumps(ocr, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "image": str(image_path.resolve()),
        "ocr": str(ocr_path.resolve()),
        "image_size": list(expected_size),
        "screen_region": list(metadata["screen_region"]),
        "scale_to_screen": list(metadata["scale_to_screen"]),
        "ocr_item_count": len(ocr.get("items", [])),
        "low_confidence_item_count": len(ocr.get("low_confidence_items", [])),
    }


def make_screen_observer(engine, output_dir, **options):
    """返回可直接传给 run_realtime_loop 的 observe 函数。"""
    def observe(_state):
        return capture_observation(engine, output_dir, **options)

    return observe

