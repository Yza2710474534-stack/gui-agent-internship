"""把识别图片中的坐标转换为屏幕坐标，仅计算，不操作鼠标。"""

from math import isfinite


def image_to_screen(
    x: float,
    y: float,
    image_size: tuple[int, int],
    screen_region: tuple[int, int, int, int],
) -> tuple[float, float]:
    """image_size 为图片宽高；screen_region 为屏幕区域左、上、宽、高。

    图片必须对应整个指定区域，可以缩放，但不能额外裁剪或补边。
    区域尺寸使用鼠标坐标单位；返回浮点坐标，供后续执行动作时取整。
    """
    image_width, image_height = image_size
    left, top, region_width, region_height = screen_region

    if not all(isfinite(value) for value in (x, y, *image_size, *screen_region)):
        raise ValueError("坐标和尺寸必须是有限数值")
    if min(image_width, image_height, region_width, region_height) <= 0:
        raise ValueError("图片和屏幕区域的宽高必须大于 0")
    if not (0 <= x < image_width and 0 <= y < image_height):
        raise ValueError("目标坐标必须位于图片内")

    scale_x = region_width / image_width
    scale_y = region_height / image_height
    screen_x = x * scale_x + left
    screen_y = y * scale_y + top
    return screen_x, screen_y


if __name__ == "__main__":
    examples = [
        ("只加起点", (80, 40), (500, 300), (200, 100, 500, 300)),
        ("只还原缩放", (150, 10), (500, 40), (0, 0, 1000, 80)),
        ("缩放加起点", (100, 10), (500, 40), (50, 100, 1000, 80)),
    ]
    for name, point, image_size, region in examples:
        sx, sy = image_to_screen(*point, image_size, region)
        print(f"{name}：({sx:g}, {sy:g})")
