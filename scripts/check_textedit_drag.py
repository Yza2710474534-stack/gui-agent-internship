"""文本编辑拖选的 macOS 原生事件对照实验。

默认只检查事件，不操作鼠标；使用 --run 才会执行一次拖选。
"""

import argparse
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.controller import drag_to, make_mouse_event

import Quartz as Q
from AppKit import NSWorkspace
import pyautogui as p


def make_event(source, kind, point):
    return make_mouse_event(source, kind, point)


def textedit_is_frontmost():
    app = NSWorkspace.sharedWorkspace().frontmostApplication()
    return app is not None and app.bundleIdentifier() == "com.apple.TextEdit"


def check_events():
    source = Q.CGEventSourceCreate(Q.kCGEventSourceStateHIDSystemState)
    if source is None:
        raise RuntimeError("无法创建事件源")
    for name, kind in (
        ("按下", Q.kCGEventLeftMouseDown),
        ("拖动", Q.kCGEventLeftMouseDragged),
        ("松开", Q.kCGEventLeftMouseUp),
    ):
        event = make_event(source, kind, (100, 100))
        assert Q.CGEventGetType(event) == kind
        assert Q.CGEventGetIntegerValueField(event, Q.kCGMouseEventClickState) == 1
        assert Q.CGEventGetFlags(event) == 0
        expected_pressure = 0 if kind == Q.kCGEventLeftMouseUp else 1
        assert Q.CGEventGetDoubleValueField(event, Q.kCGMouseEventPressure) == expected_pressure
        print(f"{name}事件检查通过")
    print("未向系统发送事件，尚未验证文字选中效果。")


def run_drag():
    p.FAILSAFE = True
    print("10秒内切回文本编辑，取消旧选区，把鼠标放在 H 左侧的文字行上，然后松手。", flush=True)
    time.sleep(10)
    if not textedit_is_frontmost():
        raise RuntimeError("当前前台不是文本编辑，未执行拖拽")
    p.failSafeCheck()
    width, height = p.size()
    start_x, start_y = p.position()
    end_x, end_y = start_x + 120, start_y
    if not (0 <= start_x < end_x < width and 0 <= start_y < height):
        raise RuntimeError("起点或终点超出主屏幕，请将文档放在主屏幕中间")
    print(f"前台：文本编辑；拖拽：({start_x}, {start_y}) → ({end_x}, {end_y})", flush=True)
    drag_to(end_x, end_y, textedit_only=True)
    print("原生拖拽事件已发送完毕。请查看文字是否高亮；这条输出不代表选区已验证。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="执行一次原生拖选")
    args = parser.parse_args()
    try:
        run_drag() if args.run else check_events()
    except (RuntimeError, p.FailSafeException) as error:
        parser.exit(1, f"停止：{error}\n")
