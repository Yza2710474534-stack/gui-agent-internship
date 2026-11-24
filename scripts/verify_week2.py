"""第二周检查入口：默认只跑单元测试，不操作鼠标键盘。"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ocr', action='store_true', help='用已有模型识别随包图片，不下载模型')
    parser.add_argument('--live', action='store_true', help='额外截取当前主屏幕，不点击、不输入')
    args = parser.parse_args()
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    directory = ROOT / 'reports' / ('acceptance_' + stamp)
    directory.mkdir(parents=True)
    summary = {'date': datetime.now().isoformat(), 'platform': platform.platform(),
               'python': platform.python_version(), 'checks': {}}
    print('正在运行单元测试（模拟鼠标，不操作桌面）……', flush=True)
    result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                            cwd=ROOT, capture_output=True, text=True)
    log = result.stdout + result.stderr
    (directory / 'unittest.txt').write_text(log, encoding='utf-8')
    print(log, flush=True)
    summary['checks']['unit_tests'] = {'passed': result.returncode == 0, 'log': 'unittest.txt',
                                      'method': '构造图片和模拟接口；不发送鼠标键盘事件'}

    if args.ocr:
        print('正在用已有模型识别菜单图片……', flush=True)
        try:
            import cv2
            from src.ocr_engine import OCREngine, DEFAULT_IMAGE
            from src.visualizer import draw_target, save_png
            from src.element_locator import find_icon
            start = time.monotonic()
            data = OCREngine(download_enabled=False).recognize(DEFAULT_IMAGE)
            (directory / 'ocr.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            image = cv2.imread(str(DEFAULT_IMAGE))
            marked, matches = draw_target(image, data['items'], '编辑')
            save_png(directory / 'ocr_marked.png', marked)
            summary['checks']['real_ocr'] = {'passed': len(matches) == 1, 'target': '编辑',
                'matches': matches, 'seconds': round(time.monotonic()-start, 3),
                'method': '已有菜单截图，真实 EasyOCR 推理；不代表整体准确率'}
            # 示例苹果图标在左上角；只验证同一截图上的外观匹配。
            template = image[4:28, 17:38].copy()
            save_png(directory / 'icon_template.png', template)
            icon = find_icon(image, template)
            summary['checks']['icon_template'] = {'passed': icon is not None, 'match': icon,
                'method': '同图裁出的模板匹配；非跨主题、跨应用泛化测试'}
            if icon:
                marked, _ = draw_target(image, [icon], '模板图标')
                save_png(directory / 'icon_marked.png', marked)
        except Exception as error:
            summary['checks']['ocr_or_icon_error'] = {'passed': False, 'error': str(error)}
            print(f'OCR或模板检查失败：{error}', flush=True)

    if args.live:
        print('正在连续截图，不操作鼠标键盘……', flush=True)
        try:
            from src.screen_capture import capture_sequence
            images = ROOT / 'output' / 'acceptance' / stamp
            records = capture_sequence(3, .3, output_dir=images)
            width, height = records[0]['image_size']
            scaled = capture_sequence(1, 0, output_size=(width//2, height//2), output_dir=images / 'scaled')
            summary['checks']['live_capture'] = {'passed': True, 'frames': records, 'scaled': scaled,
                'method': '当前主屏幕实拍和半尺寸输出；未更改系统分辨率'}
        except Exception as error:
            summary['checks']['live_capture'] = {'passed': False, 'error': str(error)}
            print(f'实时截图失败：{error}', flush=True)

    summary['limitations'] = ['Windows/Linux及不同物理显示器未实测',
        '控制接口仅操作主屏幕；英文输入前需手动切换ABC',
        '真实点击与拖选的历史记录应与模拟测试分开判断']
    output = directory / 'summary.json'
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'检查记录：{output}')
    raise SystemExit(0 if all(v['passed'] for v in summary['checks'].values()) else 1)


if __name__ == '__main__':
    main()
