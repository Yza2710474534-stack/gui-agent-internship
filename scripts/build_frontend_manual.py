"""Generate the GUI Agent UI and UX review manual from captured frontend states."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "output" / "frontend_manual" / "screenshots"
OUTPUT = ROOT / "output" / "pdf" / "GUI_Agent_前端_UI_UX_评估说明书.pdf"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

PAGE_W, PAGE_H = 1190, 842
BLUE = colors.HexColor("#1B6EF3")
DARK = colors.HexColor("#172033")
MUTED = colors.HexColor("#617088")
LINE = colors.HexColor("#DDE4EE")
SOFT = colors.HexColor("#F4F7FB")
RED = colors.HexColor("#CB4056")
GREEN = colors.HexColor("#11865F")
WHITE = colors.white

pdfmetrics.registerFont(TTFont("ArialUnicode", "/Library/Fonts/Arial Unicode.ttf"))
FONT = "ArialUnicode"


def text(c, x, y, value, size=12, color=DARK):
    c.setFont(FONT, size)
    c.setFillColor(color)
    c.drawString(x, y, value)


def wrap(value, width, size):
    lines = []
    line = ""
    for char in value:
        if char == "\n":
            lines.append(line)
            line = ""
            continue
        proposed = line + char
        if pdfmetrics.stringWidth(proposed, FONT, size) > width and line:
            lines.append(line)
            line = char
        else:
            line = proposed
    if line:
        lines.append(line)
    return lines


def paragraph(c, x, y, value, width, size=12, leading=19, color=DARK):
    for line in wrap(value, width, size):
        text(c, x, y, line, size, color)
        y -= leading
    return y


def rounded(c, x, y, w, h, fill=WHITE, stroke=LINE, radius=12):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def footer(c, page, label="GUI Agent 前端 UI UX 评估说明书"):
    c.setStrokeColor(LINE)
    c.line(38, 43, PAGE_W - 38, 43)
    text(c, 40, 25, label, 9, MUTED)
    c.setFont(FONT, 9)
    c.setFillColor(MUTED)
    c.drawRightString(PAGE_W - 40, 25, f"{page:02d} / 09")


def page_title(c, kicker, title, subtitle):
    text(c, 40, 796, kicker, 10, BLUE)
    text(c, 40, 756, title, 25, DARK)
    paragraph(c, 40, 727, subtitle, 1090, 11, 17, MUTED)


def arrow(c, x1, y1, x2, y2, color=BLUE):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.5)
    c.line(x1, y1, x2, y2)
    if abs(x2 - x1) >= abs(y2 - y1):
        direction = 1 if x2 > x1 else -1
        points = [(x2, y2), (x2 - 7 * direction, y2 + 4), (x2 - 7 * direction, y2 - 4)]
    else:
        direction = 1 if y2 > y1 else -1
        points = [(x2, y2), (x2 - 4, y2 - 7 * direction), (x2 + 4, y2 - 7 * direction)]
    p = c.beginPath()
    p.moveTo(*points[0])
    for point in points[1:]:
        p.lineTo(*point)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def node(c, x, y, w, h, title, caption="", fill=WHITE, stroke=LINE, title_color=DARK):
    rounded(c, x, y, w, h, fill=fill, stroke=stroke, radius=10)
    text(c, x + 12, y + h - 23, title, 13, title_color)
    if caption:
        paragraph(c, x + 12, y + h - 44, caption, w - 24, 10, 15, MUTED)


def label_section(c, x, y, title, items, width, color=BLUE):
    c.setFillColor(color)
    c.roundRect(x, y - 2, 5, 19, 2.5, fill=1, stroke=0)
    text(c, x + 13, y, title, 14, DARK)
    y -= 28
    for item in items:
        c.setFillColor(color)
        c.circle(x + 5, y + 4, 2.5, fill=1, stroke=0)
        y = paragraph(c, x + 17, y, item, width - 18, 11, 17, DARK) - 9
    return y


steps = [
    {
        "file": "01_connection_offline.png",
        "title": "01 打开页面与连接检查",
        "subtitle": "用户打开控制台后，页面向本地 127.0.0.1:8765 查询服务状态。",
        "ui": ["右上角显示“本地执行器未连接”。", "任务输入仍可见，主按钮仍可点击。", "屏幕观察区域显示占位图。"],
        "ux": ["用户能知道当前没有本地服务。", "点击开始后会再次检查连接，并提示启动执行器。", "缺少直接可见的启动说明，首次使用路径仍不够明确。"],
        "assessment": "可识别异常，但修复动作需要用户回忆启动脚本的位置。",
        "tag": "需改进",
    },
    {
        "file": "02_connected_idle.png",
        "title": "02 连接成功与待机",
        "subtitle": "本地服务返回健康状态后，页面显示当前仅支持预览。",
        "ui": ["连接状态转为绿色，文字为“已连接 · 仅预览”。", "当前状态改为“等待新任务”。", "预览模式默认选中，运行区仍为空。"],
        "ux": ["用户可以立即开始安全预览。", "模式范围在顶部可见，有助于避免误以为会控制桌面。", "导航中的任务记录、数据集和设置目前只有提示，没有实际页面。"],
        "assessment": "主任务入口清晰；未开放导航不应看起来像已完成的功能。",
        "tag": "基本合理",
    },
    {
        "file": "03_task_configured.png",
        "title": "03 填写任务与选择模式",
        "subtitle": "用户输入自然语言任务，并选择预览或实时模式。截图使用“点击编辑”示例。",
        "ui": ["任务文本框限制为 240 字。", "预览与实时为互斥模式。", "下方说明预览不会发送鼠标或键盘动作。"],
        "ux": ["预览模式适合先判断 OCR 能否唯一找到目标。", "实时模式需本地服务用 --enable-live 显式开启。", "默认示例是浏览器搜索，但当前真实模式并不支持完整搜索闭环，容易造成期待落差。"],
        "assessment": "输入方式简单；示例内容需要与已实现能力一致。",
        "tag": "需改进",
    },
    {
        "file": "04_observing.png",
        "title": "04 提交任务与观察屏幕",
        "subtitle": "网页提交任务后轮询状态，本地服务加载 OCR 并截图。",
        "ui": ["开始按钮和输入框暂时禁用。", "执行进度、运行标记和动作日志同步更新。", "右侧仍为占位图，直到截图 URL 返回并加载。"],
        "ux": ["用户能看见系统正在工作，并可请求暂停或停止。", "状态每 900 毫秒轮询一次。", "进度节点有映射偏差：观察中时界面可能把“观察屏幕”标为完成。"],
        "assessment": "状态反馈完整，但进度节点需要与服务阶段严格对齐。",
        "tag": "需修正",
    },
    {
        "file": "05_planning.png",
        "title": "05 识别结果与动作规划",
        "subtitle": "本地服务读取 OCR 文字，为“点击可见文字”寻找唯一匹配并换算屏幕坐标。",
        "ui": ["识别文字数量和目标置信度出现。", "日志显示目标文字及坐标。", "安全检查状态显示为检查中。"],
        "ux": ["用户能据此判断定位是否可信。", "找不到唯一目标时服务会停止。", "规划中进度节点可能提前显示“返回结果”进行中，影响判断。"],
        "assessment": "单步文字点击路径可解释；阶段显示存在错位。",
        "tag": "需修正",
    },
    {
        "file": "06_preview_result.png",
        "title": "06 预览动作与查看结果",
        "subtitle": "预览返回结构化动作、识别指标和日志，且不会执行鼠标或键盘动作。",
        "ui": ["顶部显示“动作方案已生成”。", "四个进度节点完成，日志列出定位过程。", "目标区域框出现在屏幕观察区。"],
        "ux": ["用户可核对 OCR 数量、置信度和动作意图。", "当前页面没有直接展示结构化动作详情，主要依赖日志。", "目标框的位置由固定 CSS 绘制，不按 OCR 坐标定位，不能作为真实定位证据。"],
        "assessment": "预览安全边界正确；目标高亮目前具有误导风险。",
        "tag": "高优先级",
    },
    {
        "file": "07_paused.png",
        "title": "07 暂停与继续",
        "subtitle": "用户可在任务运行时请求暂停，继续后恢复本地服务的下一阶段。",
        "ui": ["暂停状态显示在顶部、进度区和屏幕观察区。", "暂停按钮会改成继续任务。", "停止按钮仍可用。"],
        "ux": ["用户能区分正在运行与已暂停。", "当前暂停是阶段边界暂停，长时间 OCR 调用不能立即中断。", "页面未说明“本阶段完成后暂停”，容易被理解为即时冻结。"],
        "assessment": "控制入口具备，但响应时机需要更准确地说明。",
        "tag": "需改进",
    },
    {
        "file": "08_permission_error.png",
        "title": "08 权限失败与恢复",
        "subtitle": "如果本地进程无法获取屏幕，任务结束并返回可读的错误信息。",
        "ui": ["当前状态为“任务未完成”。", "进度区和日志显示屏幕录制权限错误。", "开始按钮重新可用。"],
        "ux": ["错误位置和原因能够被看到。", "页面提示从有屏幕录制权限的终端启动。", "缺少明确的系统设置路径、重新检查入口与诊断步骤。"],
        "assessment": "失败后能恢复操作，但错误解决指引不够具体。",
        "tag": "需改进",
    },
]


def overview(c):
    page_title(c, "总览", "从打开页面到得到结果", "实线是当前主路径；下方分支对应本地服务断开、暂停、实时权限与运行失败。")
    widths = [145, 145, 145, 145, 145, 145]
    xs = [40, 226, 412, 598, 784, 970]
    titles = ["打开控制台", "检查本地连接", "填写任务与模式", "提交任务", "截图与 OCR", "规划并返回"]
    captions = ["加载页面", "健康检查", "预览为默认", "创建任务 ID", "保存观察证据", "动作或停止"]
    for i, (x, w, title, caption) in enumerate(zip(xs, widths, titles, captions)):
        node(c, x, 524, w, 94, title, caption, fill=WHITE, stroke=BLUE if i in {1, 5} else LINE)
        if i < len(xs) - 1:
            arrow(c, x + w + 6, 571, xs[i + 1] - 7, 571)
    text(c, 40, 465, "关键分支", 15, DARK)
    node(c, 40, 325, 320, 100, "未连接", "提示用户启动本地执行器", fill=SOFT)
    node(c, 435, 325, 320, 100, "暂停或停止", "在阶段边界生效并更新状态", fill=SOFT)
    node(c, 830, 325, 320, 100, "运行失败", "显示错误并保留日志", fill=SOFT)
    arrow(c, 298, 524, 210, 427, color=MUTED)
    arrow(c, 675, 524, 595, 427, color=MUTED)
    arrow(c, 1060, 524, 990, 427, color=MUTED)
    rounded(c, 40, 117, 1110, 158, fill=WHITE, stroke=LINE)
    text(c, 60, 240, "当前功能边界", 14, BLUE)
    paragraph(c, 60, 213, "预览模式：截图、OCR、结构化动作提案，不发送桌面输入。实时模式：只有本地服务显式开启后才可使用，目前仅对 OCR 唯一匹配的可见文字做一次点击；搜索任务不会在未知焦点下输入。", 1070, 13, 21)
    paragraph(c, 60, 156, "页面刷新后仅能看到新任务入口；任务记录导航尚未实现。现有运行日志既在页面展示，也由本地服务写入 JSONL 文件，但前端没有历史浏览入口。", 1070, 12, 19, MUTED)
    footer(c, 1)
    c.showPage()


def step_page(c, page_number, item):
    page_title(c, f"步骤 {page_number - 1:02d} / 08", item["title"], item["subtitle"])
    image_path = IMAGES / item["file"]
    image = ImageReader(str(image_path))
    iw, ih = image.getSize()
    x, top = 40, 687
    w = min(744, 520 * iw / ih)
    h = w * ih / iw
    y = top - h
    rounded(c, x - 3, y - 3, w + 6, h + 6, fill=WHITE, stroke=LINE, radius=8)
    c.drawImage(image, x, y, width=w, height=h, preserveAspectRatio=True, mask="auto")

    sx, sw = 820, 330
    y_text = 681
    y_text = label_section(c, sx, y_text, "UI 画面与控件", item["ui"], sw)
    y_text -= 2
    label_section(c, sx, y_text, "UX 操作与反馈", item["ux"], sw, color=GREEN)

    footer(c, page_number)
    c.showPage()


c = canvas.Canvas(str(OUTPUT), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
c.setTitle("GUI Agent 前端 UI UX 分步说明与合理性评估")
c.setAuthor("Codex")
overview(c)
for number, step in enumerate(steps, start=2):
    step_page(c, number, step)
c.save()
print(OUTPUT)
