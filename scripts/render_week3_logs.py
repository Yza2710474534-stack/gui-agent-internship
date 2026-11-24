"""把第三周真实日志排版为报告用运行结果图片。"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/week3/screenshots"
FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"


def wrap_line(text, width=62):
    if len(text) <= width:
        return [text]
    return [text[index:index + width] for index in range(0, len(text), width)]


def render_terminal(title, lines, output_path):
    font = ImageFont.truetype(FONT_PATH, 25)
    small = ImageFont.truetype(FONT_PATH, 20)
    wrapped = []
    for line in lines:
        wrapped.extend(wrap_line(line))

    width = 1400
    height = 110 + len(wrapped) * 39 + 40
    image = Image.new("RGB", (width, height), "#15181d")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((12, 12, width - 12, height - 12), radius=18,
                           fill="#15181d", outline="#333842", width=2)
    for x, color in ((38, "#ff5f57"), (70, "#febc2e"), (102, "#28c840")):
        draw.ellipse((x - 9, 34, x + 9, 52), fill=color)
    draw.text((132, 31), title, font=small, fill="#c9cdd4")
    draw.line((24, 75, width - 24, 75), fill="#333842", width=2)

    y = 94
    for line in wrapped:
        color = "#77d18b" if line.startswith(("OK", "Final status", "Completed")) else "#edf1f5"
        draw.text((38, y), line, font=font, fill=color)
        y += 39
    image.save(output_path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data_lines = (ROOT / "reports/week3/kaggle_full_summary.txt").read_text(encoding="utf-8").splitlines()
    test_log = (ROOT / "reports/week3/unittest.txt").read_text(encoding="utf-8")
    data_lines += ["", "WEEK 3 UNIT TESTS", "Ran 39 tests in 0.238s", "OK"]
    if "Ran 39 tests" not in test_log or "OK" not in test_log:
        raise RuntimeError("测试日志与截图文字不一致")
    render_terminal("第三周数据处理与测试结果", data_lines, OUT / "data_and_tests.png")

    api_lines = (ROOT / "reports/week3/deepseek_summary.txt").read_text(encoding="utf-8").splitlines()
    api_lines += [""] + (ROOT / "reports/week3/trajectory_summary.txt").read_text(encoding="utf-8").splitlines()
    render_terminal("DeepSeek 任务规划与数据闭环", api_lines, OUT / "agent_and_api.png")
    print(OUT / "data_and_tests.png")
    print(OUT / "agent_and_api.png")


if __name__ == "__main__":
    main()
