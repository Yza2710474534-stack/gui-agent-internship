"""简单鼠标键盘控制：移动、点击、输入、滚动和拖拽。"""

import math
import sys
import time


def _mouse():
    import pyautogui as p
    p.FAILSAFE = True
    return p


def _check_point(x, y, p):
    width, height = p.size()
    if not all(math.isfinite(v) for v in (x, y)):
        raise ValueError("坐标必须是有限数值")
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError("坐标超出主屏幕")


def _check_seconds(value):
    if not math.isfinite(value) or value < 0:
        raise ValueError("时间必须是大于等于0的有限数值")


def move_to(x, y, duration=0.5):
    """移动到主屏幕上的指定位置。"""
    _check_seconds(duration)
    p = _mouse()
    _check_point(x, y, p)
    p.moveTo(x, y, duration=duration)


def click(x, y, button="left"):
    """在指定位置单击。"""
    if button not in ("left", "right", "middle"):
        raise ValueError("鼠标键必须为 left、right 或 middle")
    p = _mouse()
    _check_point(x, y, p)
    p.click(x, y, button=button)


def type_text(text, interval=0.1):
    """逐键输入英文、数字、换行和制表符；运行前切换 ABC 输入法。"""
    _check_seconds(interval)
    if not isinstance(text, str) or any(not (32 <= ord(c) <= 126 or c in "\n\t") for c in text):
        raise ValueError("逐键输入仅支持英文、数字及常用标点，请勿直接传入中文")
    _mouse().write(text, interval=interval)


def scroll(amount):
    """正数向上滚动，负数向下滚动；鼠标需位于目标页面上。"""
    if not isinstance(amount, int) or isinstance(amount, bool):
        raise ValueError("滚动量必须是整数")
    _mouse().scroll(amount)


def make_mouse_event(source, kind, point):
    """Mac 原生事件的小工具，只在 Mac 拖拽时使用。"""
    import Quartz as Q
    event = Q.CGEventCreateMouseEvent(source, kind, point, Q.kCGMouseButtonLeft)
    if event is None:
        raise RuntimeError("无法创建鼠标事件")
    Q.CGEventSetFlags(event, 0)
    Q.CGEventSetIntegerValueField(event, Q.kCGMouseEventClickState, 1)
    Q.CGEventSetIntegerValueField(event, Q.kCGMouseEventNumber, 1)
    Q.CGEventSetDoubleValueField(event, Q.kCGMouseEventPressure,
                               0 if kind == Q.kCGEventLeftMouseUp else 1)
    return event


def drag_to(x, y, duration=2.0, textedit_only=False):
    """从鼠标当前位置按住左键拖到目标点；Mac 使用已验证的原生事件。"""
    _check_seconds(duration)
    if duration <= 0:
        raise ValueError("拖拽时间必须大于0")
    p = _mouse()
    if textedit_only:
        require_textedit()
    _check_point(x, y, p)
    start_x, start_y = p.position()
    _check_point(start_x, start_y, p)
    if sys.platform != "darwin":
        try:
            p.dragTo(x, y, duration=duration, button="left")
        finally:
            # 直接调用底层松开，避免紧急停止阻止鼠标松开。
            up_x, up_y = p.position()
            p.platformModule._mouseUp(up_x, up_y, "left")
        return

    import Quartz as Q
    source = Q.CGEventSourceCreate(Q.kCGEventSourceStateHIDSystemState)
    if source is None:
        raise RuntimeError("无法创建事件源")
    event = make_mouse_event(source, Q.kCGEventLeftMouseDown, (start_x, start_y))
    last_point = (start_x, start_y)
    p.failSafeCheck()
    try:
        Q.CGEventPost(Q.kCGHIDEventTap, event)
        time.sleep(0.3)
        for step in range(1, 61):
            p.failSafeCheck()
            if textedit_only:
                require_textedit()
            last_point = (start_x + (x - start_x) * step / 60,
                          start_y + (y - start_y) * step / 60)
            Q.CGEventSetType(event, Q.kCGEventLeftMouseDragged)
            Q.CGEventSetLocation(event, last_point)
            Q.CGEventSetTimestamp(event, 0)
            Q.CGEventPost(Q.kCGHIDEventTap, event)
            time.sleep(duration / 60)
    finally:
        Q.CGEventSetType(event, Q.kCGEventLeftMouseUp)
        Q.CGEventSetLocation(event, last_point)
        Q.CGEventSetDoubleValueField(event, Q.kCGMouseEventPressure, 0)
        Q.CGEventSetTimestamp(event, 0)
        Q.CGEventPost(Q.kCGHIDEventTap, event)


def require_textedit():
    if sys.platform != "darwin":
        raise RuntimeError("文本编辑菜单演示仅适用于 macOS；基础控制函数可在其他平台使用")
    from AppKit import NSWorkspace
    app = NSWorkspace.sharedWorkspace().frontmostApplication()
    if app is None or app.bundleIdentifier() != "com.apple.TextEdit":
        raise RuntimeError("当前前台不是文本编辑，停止本次点击")


def click_edit_menu(x, y):
    """只用于主屏幕顶部菜单栏，坐标必须来自本次 OCR。"""
    import pyautogui as p
    p.FAILSAFE = True
    require_textedit()
    width, height = p.size()
    if not all(math.isfinite(value) for value in (x, y)):
        raise ValueError("点击坐标必须是有限数值")
    if not (0 <= x < width and 0 <= y < min(40, height)):
        raise ValueError("本次练习只允许点击主屏幕顶部菜单栏")
    click(x, y)
