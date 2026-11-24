"""第六天模块集成：默认定位预览，--click 执行一次编辑菜单点击并截图反馈。"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

if __package__:
    from .coordinate import image_to_screen
    from .controller import click_edit_menu, require_textedit
    from .ocr_engine import OCREngine
    from .screen_capture import capture_region
    from .visualizer import draw_target, save_png
else:
    from coordinate import image_to_screen
    from controller import click_edit_menu, require_textedit
    from ocr_engine import OCREngine
    from screen_capture import capture_region
    from visualizer import draw_target, save_png


PROJECT_DIR = Path(__file__).resolve().parents[1]


def feedback_summary(before_image, after_image, before_ocr, after_ocr):
    """画面变化加新增菜单文字只作初步判断，保留图片供人工复核。"""
    labels = ("撤销", "重做", "剪切", "拷贝", "复制", "粘贴", "全选",
              "Undo", "Redo", "Cut", "Copy", "Paste", "SelectAll")

    def found_labels(result):
        texts = ["".join(item["text"].split()) for item in result["items"]]
        return {label for label in labels if any(text.startswith(label) for text in texts)}

    new_labels = sorted(found_labels(after_ocr) - found_labels(before_ocr))
    if before_image.shape != after_image.shape:
        return {"status": "needs_visual_check", "reason": "截图尺寸变化", "new_menu_labels": new_labels}
    difference = np.max(cv2.absdiff(before_image, after_image), axis=2)
    change_ratio = float(np.mean(difference > 20))
    return {
        "status": "menu_likely_open" if change_ratio > 0.005 and len(new_labels) >= 2 else "needs_visual_check",
        "changed_pixel_ratio": change_ratio,
        "new_menu_labels": new_labels,
    }


def execute_with_feedback(engine, frame, result, plan, region, run_dir, captured_at, report):
    import pyautogui as p
    require_textedit()
    if time.monotonic() - captured_at > 15:
        raise RuntimeError("定位截图已超过15秒，请重新运行定位")
    fresh = capture_region(*region)
    if fresh.shape != frame.shape:
        raise RuntimeError("截图尺寸发生变化，停止点击")
    target = next(item for item in result["items"] if "".join(item["text"].split()) == "编辑")
    box = np.asarray(target["bbox"])
    h, w = frame.shape[:2]
    x1, y1 = max(0, int(box[:, 0].min()) - 4), max(0, int(box[:, 1].min()) - 4)
    x2, y2 = min(w, int(np.ceil(box[:, 0].max())) + 5), min(h, int(np.ceil(box[:, 1].max())) + 5)
    if x2 <= x1 or y2 <= y1:
        raise RuntimeError("目标框无效，停止点击")
    patch_change = cv2.absdiff(frame[y1:y2, x1:x2], fresh[y1:y2, x1:x2])
    if float(np.mean(np.max(patch_change, axis=2) > 20)) > 0.05:
        raise RuntimeError("目标附近画面发生变化，停止点击，请重新定位")

    screen_width, screen_height = p.size()
    feedback_region = (0, 0, min(1000, screen_width), min(600, screen_height))
    before = capture_region(*feedback_region)
    before_path = run_dir / "before_action.png"
    save_png(before_path, before)
    action = plan["proposed_action"]
    # 执行器再次检查前台应用和坐标；仅点击一次，不选择下拉菜单项。
    report["execution_attempted"] = True
    click_edit_menu(action["x"], action["y"])
    report["executed"] = True
    print("已点击编辑菜单，正在获取操作后截图……", flush=True)
    time.sleep(0.8)
    require_textedit()
    after = capture_region(*feedback_region)
    after_path = run_dir / "after_action.png"
    save_png(after_path, after)
    print("正在对比操作前后的菜单文字，请保持界面不变……", flush=True)
    before_ocr = engine.recognize(before_path)
    after_ocr = engine.recognize(after_path)
    report["feedback"] = feedback_summary(before, after, before_ocr, after_ocr)
    report["feedback"]["before_ocr"] = before_ocr
    report["feedback"]["after_ocr"] = after_ocr
    report["status"] = report["feedback"]["status"]
    if report["status"] == "menu_likely_open":
        print("反馈：检测到新增菜单文字，初步判断编辑菜单已展开。")
    else:
        print("反馈：暂不能自动确认菜单展开，请查看操作后截图。")
    print(f"操作后截图：{after_path}")


def make_plan(result, target, region):
    """只为唯一匹配生成坐标预览；缺失和重名目标不生成动作。"""
    matches = [
        item for item in result["items"]
        if "".join(item["text"].split()) == "".join(target.split())
    ]
    if len(matches) != 1:
        return {
            "status": "target_missing" if not matches else "target_ambiguous",
            "match_count": len(matches),
            "proposed_action": None,
            "executed": False,
        }
    match = matches[0]
    x, y = image_to_screen(*match["center"], tuple(result["image_size"]), region)
    return {
        "status": "preview_ready",
        "match_count": 1,
        "confidence": match["confidence"],
        "image_center": match["center"],
        "screen_center": [x, y],
        "proposed_action": {"type": "click", "x": round(x), "y": round(y)},
        "executed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="编辑")
    parser.add_argument("--click", action="store_true", help="定位后点击文本编辑的编辑菜单并截图反馈")
    parser.add_argument("--image", type=Path, help="使用已有图片进行离线测试")
    parser.add_argument("--region", nargs=4, type=int, default=[0, 0, 1000, 80],
                        metavar=("LEFT", "TOP", "WIDTH", "HEIGHT"),
                        help="截图区域的屏幕坐标，默认左上角菜单栏")
    args = parser.parse_args()
    if args.click and (args.image or args.target != "编辑"):
        parser.error("点击练习只支持当前屏幕的‘编辑’菜单，不能使用旧图片或其他目标")
    left, top, width, height = args.region
    if width <= 0 or height <= 0 or not args.target.strip():
        parser.error("区域宽高必须大于0，目标文字不能为空")
    if args.image and not args.image.is_file():
        parser.error(f"图片不存在：{args.image}")

    print("正在加载 OCR 模型……", flush=True)
    engine = OCREngine()
    run_dir = PROJECT_DIR / "output" / "demo" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    if args.image:
        frame = cv2.imread(str(args.image))
        if frame is None:
            parser.error(f"无法读取图片：{args.image}")
        print("离线预览：屏幕坐标以 --region 参数为依据，不代表当前界面位置。")
    else:
        import pyautogui as p
        screen_width, screen_height = p.size()
        if not (0 <= left < left + width <= screen_width and
                0 <= top < top + height <= screen_height):
            parser.error("截图区域超出主屏幕，或当前终端未检测到屏幕")
        mode_text = "本次会点击一次编辑菜单，请保持界面不变。" if args.click else "本次只预览，不点击。"
        print(f"8秒内切到文本编辑，让顶部的‘编辑’菜单可见；{mode_text}", flush=True)
        time.sleep(8)
        if args.click:
            require_textedit()
        frame = capture_region(left, top, width, height)
    captured_at = time.monotonic()
    observed_at = datetime.now().isoformat(timespec="seconds")

    run_dir.mkdir(parents=True, exist_ok=False)
    screenshot_path = run_dir / "screenshot.png"
    save_png(screenshot_path, frame)
    print("截图已保存，正在识别……", flush=True)
    result = engine.recognize(screenshot_path, min_confidence=0.3)
    plan = make_plan(result, args.target, tuple(args.region))
    report = {
        "mode": "live_click" if args.click else ("offline_preview" if args.image else "live_preview"),
        "observed_at": observed_at,
        "target": args.target,
        "screen_region": args.region,
        "ocr": result,
        **plan,
    }
    if args.image:
        report["source_image"] = str(args.image.resolve())
    (run_dir / "result.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if plan["status"] == "preview_ready":
        marked, _ = draw_target(frame, result["items"], args.target)
        save_png(run_dir / "marked.png", marked)
        action = plan["proposed_action"]
        print(f"找到唯一目标：{args.target} | 置信度：{plan['confidence']:.3f}")
        print(f"准备点击的屏幕坐标：({action['x']}, {action['y']})")
        print(f"标注截图：{run_dir / 'marked.png'}")
    else:
        print(f"目标匹配数量：{plan['match_count']}，无法确定唯一位置，未生成点击动作。")
    if args.click and plan["status"] == "preview_ready":
        try:
            execute_with_feedback(engine, frame, result, plan, tuple(args.region), run_dir, captured_at, report)
        except Exception as error:
            report["status"] = "feedback_error" if report["executed"] else "action_stopped_or_uncertain"
            report["error"] = str(error)
            print(f"本次操作停止或反馈未完成：{error}")
        finally:
            (run_dir / "result.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
    print(f"本次结果目录：{run_dir}")
    if not args.click:
        print("预览结束，没有执行鼠标动作。后续实际点击前需重新截图定位。")


if __name__ == "__main__":
    main()
