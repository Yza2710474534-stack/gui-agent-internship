"""用小图模板定位非文字图标，不依赖 OCR，也不执行点击。"""

import math

import cv2
import numpy as np


def find_icon(image, template, threshold=0.9, scales=(1.0,)):
    """返回最佳匹配的框、中心和相似度；找不到则返回 None。

    image、template 均为 OpenCV BGR 图片。模板应只包含图标及少量背景。
    这是外观匹配，不是通用图标理解；同样图标有多处时只返回最佳的一处。
    """
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("匹配阈值必须在0到1之间")
    if image is None or template is None or image.size == 0 or template.size == 0:
        raise ValueError("图片和模板不能为空")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    small = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    if float(np.std(small)) < 1:
        raise ValueError("模板接近纯色，不能可靠定位")
    if not scales or any(not math.isfinite(s) or s <= 0 for s in scales):
        raise ValueError("缩放比例必须是大于0的有限数值")
    best = None
    for scale in scales:
        width = max(1, round(small.shape[1] * scale))
        height = max(1, round(small.shape[0] * scale))
        if width > gray.shape[1] or height > gray.shape[0]:
            continue
        resized = cv2.resize(small, (width, height))
        if float(np.std(resized)) < 1:
            continue
        scores = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
        _, score, _, (x, y) = cv2.minMaxLoc(scores)
        if score < threshold or (best and score <= best["confidence"]):
            continue
        best = {
            "text": "模板图标",
            "confidence": float(score),
            "bbox": [[x, y], [x + width - 1, y],
                     [x + width - 1, y + height - 1], [x, y + height - 1]],
            "center": [x + (width - 1) / 2, y + (height - 1) / 2],
            "template_scale": scale,
        }
    return best
