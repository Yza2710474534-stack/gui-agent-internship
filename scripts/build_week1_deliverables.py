from __future__ import annotations

from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "pdf"

NAVY = colors.HexColor("#1C3345")
TEAL = colors.HexColor("#2F7D7A")
TEAL_LIGHT = colors.HexColor("#E8F3F1")
BLUE_LIGHT = colors.HexColor("#EAF0F6")
INK = colors.HexColor("#26333D")
MUTED = colors.HexColor("#65737E")
LINE = colors.HexColor("#D8E0E5")
PAPER = colors.HexColor("#F7F8F9")
WHITE = colors.white
GREEN = colors.HexColor("#2C7A57")
AMBER = colors.HexColor("#A86A17")


def register_fonts() -> tuple[str, str]:
    regular_candidates = [
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    bold_candidates = [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]

    regular = "Helvetica"
    bold = "Helvetica-Bold"
    for candidate in regular_candidates:
        if Path(candidate).exists():
            try:
                pdfmetrics.registerFont(TTFont("CN-Regular", candidate, subfontIndex=0))
                regular = "CN-Regular"
                break
            except Exception:
                continue
    for candidate in bold_candidates:
        if Path(candidate).exists():
            try:
                pdfmetrics.registerFont(TTFont("CN-Bold", candidate, subfontIndex=0))
                bold = "CN-Bold"
                break
            except Exception:
                continue
    return regular, bold


FONT, FONT_BOLD = register_fonts()


def styles():
    base = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle(
            "cover_kicker",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=10,
            leading=15,
            textColor=TEAL,
            spaceAfter=10,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Title"],
            fontName=FONT_BOLD,
            fontSize=25,
            leading=34,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=16,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            parent=base["Normal"],
            fontName=FONT,
            fontSize=11,
            leading=18,
            textColor=MUTED,
            spaceAfter=24,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName=FONT_BOLD,
            fontSize=16,
            leading=23,
            textColor=NAVY,
            spaceBefore=7,
            spaceAfter=10,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName=FONT_BOLD,
            fontSize=11.5,
            leading=18,
            textColor=TEAL,
            spaceBefore=7,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=9.6,
            leading=16,
            textColor=INK,
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=8.2,
            leading=13,
            textColor=MUTED,
            spaceAfter=4,
        ),
        "table": ParagraphStyle(
            "table",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=8.3,
            leading=12.3,
            textColor=INK,
        ),
        "table_head": ParagraphStyle(
            "table_head",
            parent=base["BodyText"],
            fontName=FONT_BOLD,
            fontSize=8.3,
            leading=12,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),
        "callout": ParagraphStyle(
            "callout",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=9.3,
            leading=15,
            textColor=NAVY,
            leftIndent=8,
            rightIndent=8,
            spaceAfter=2,
        ),
        "code": ParagraphStyle(
            "code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.8,
            leading=11.8,
            textColor=INK,
            leftIndent=8,
            rightIndent=8,
            spaceAfter=0,
        ),
        "reference": ParagraphStyle(
            "reference",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=6.9,
            leading=9.8,
            textColor=MUTED,
            spaceAfter=2,
        ),
    }


S = styles()


def p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, S[style])


def section(title: str) -> list:
    return [p(title, "h1")]


def sub(title: str) -> list:
    return [p(title, "h2")]


def note(text: str, color=TEAL_LIGHT) -> Table:
    table = Table([[p(text, "callout")]], colWidths=[169 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def code_block(lines: list[str]) -> Table:
    content = "<br/>".join(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for line in lines)
    table = Table([[p(content, "code")]], colWidths=[169 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PAPER),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def data_table(headers: list[str], rows: list[list[str]], widths: list[float], font_size: float = 8.3) -> Table:
    head = [p(item, "table_head") for item in headers]
    body_style = ParagraphStyle("table_local", parent=S["table"], fontSize=font_size, leading=font_size + 4)
    body = [[Paragraph(cell, body_style) for cell in row] for row in rows]
    table = Table([head] + body, colWidths=[w * mm for w in widths], repeatRows=1)
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for row_index in range(1, len(body) + 1):
        if row_index % 2 == 0:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), PAPER))
    table.setStyle(TableStyle(commands))
    return table


def status_table(rows: list[list[str]]) -> Table:
    prepared = []
    for status, item, evidence in rows:
        status_color = GREEN if status == "通过" else AMBER
        status_cell = Paragraph(f'<font color="{status_color.hexval()}"><b>{status}</b></font>', S["table"])
        prepared.append([status_cell, p(item, "table"), p(evidence, "table")])
    table = Table(
        [[p("状态", "table_head"), p("检查项", "table_head"), p("实际记录", "table_head")]] + prepared,
        colWidths=[20 * mm, 46 * mm, 103 * mm],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 2), (-1, 2), PAPER),
                ("BACKGROUND", (0, 4), (-1, 4), PAPER),
            ]
        )
    )
    return table


def flow_diagram() -> Drawing:
    drawing = Drawing(480, 92)
    labels = ["用户任务", "屏幕感知", "任务规划", "动作执行", "结果反馈"]
    x_positions = [0, 98, 196, 294, 392]
    for i, (label, x) in enumerate(zip(labels, x_positions)):
        fill = TEAL_LIGHT if i in (1, 4) else BLUE_LIGHT
        drawing.add(Rect(x, 30, 82, 38, rx=6, ry=6, fillColor=fill, strokeColor=LINE, strokeWidth=0.8))
        drawing.add(String(x + 41, 45, label, fontName=FONT_BOLD, fontSize=8.5, fillColor=NAVY, textAnchor="middle"))
        if i < len(labels) - 1:
            x1 = x + 82
            x2 = x_positions[i + 1]
            drawing.add(Line(x1 + 3, 49, x2 - 5, 49, strokeColor=TEAL, strokeWidth=1.2))
            drawing.add(Polygon([x2 - 5, 53, x2, 49, x2 - 5, 45], fillColor=TEAL, strokeColor=TEAL))
    drawing.add(Line(433, 28, 433, 10, strokeColor=MUTED, strokeWidth=0.9))
    drawing.add(Line(433, 10, 41, 10, strokeColor=MUTED, strokeWidth=0.9))
    drawing.add(Line(41, 10, 41, 27, strokeColor=MUTED, strokeWidth=0.9))
    drawing.add(Polygon([37, 27, 41, 31, 45, 27], fillColor=MUTED, strokeColor=MUTED))
    drawing.add(String(237, 0, "未完成则进入下一轮", fontName=FONT, fontSize=7.5, fillColor=MUTED, textAnchor="middle"))
    return drawing


def architecture_diagram() -> Drawing:
    drawing = Drawing(480, 150)
    columns = [
        (8, "Mac 本地执行层", ["mss 截图", "PyAutoGUI / pynput", "权限与安全检查"]),
        (174, "Agent 编排层", ["任务状态机", "动作解析", "结果验证与日志"]),
        (340, "模型与算力层", ["多模态模型 / API", "Kaggle GPU", "离线训练与评测"]),
    ]
    for x, title, items in columns:
        drawing.add(Rect(x, 18, 132, 112, rx=7, ry=7, fillColor=PAPER, strokeColor=LINE, strokeWidth=0.9))
        drawing.add(Rect(x, 98, 132, 32, rx=7, ry=7, fillColor=NAVY, strokeColor=NAVY))
        drawing.add(String(x + 66, 109, title, fontName=FONT_BOLD, fontSize=9, fillColor=WHITE, textAnchor="middle"))
        for j, item in enumerate(items):
            drawing.add(String(x + 66, 78 - 22 * j, item, fontName=FONT, fontSize=8.2, fillColor=INK, textAnchor="middle"))
    for x1, x2 in [(140, 174), (306, 340)]:
        drawing.add(Line(x1 + 4, 73, x2 - 5, 73, strokeColor=TEAL, strokeWidth=1.2))
        drawing.add(Polygon([x2 - 5, 77, x2, 73, x2 - 5, 69], fillColor=TEAL, strokeColor=TEAL))
    drawing.add(String(240, 3, "重型训练不放在本地 GUI 进程中，降低资源竞争和误操作风险", fontName=FONT, fontSize=7.5, fillColor=MUTED, textAnchor="middle"))
    return drawing


def page_decorator(title: str):
    def draw(canvas, doc):
        canvas.saveState()
        width, height = A4
        if doc.page > 1:
            canvas.setStrokeColor(LINE)
            canvas.setLineWidth(0.5)
            canvas.line(20 * mm, height - 15 * mm, width - 20 * mm, height - 15 * mm)
            canvas.setFont(FONT, 7.5)
            canvas.setFillColor(MUTED)
            canvas.drawString(20 * mm, height - 11.5 * mm, title)
        canvas.setFont(FONT, 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(width - 20 * mm, 10 * mm, f"第 {doc.page} 页")
        canvas.restoreState()

    return draw


def cover(story: list, title: str, subtitle: str, summary: str) -> None:
    story.extend(
        [
            Spacer(1, 24 * mm),
            p("第 1 周阶段交付物", "cover_kicker"),
            p(title, "cover_title"),
            p(subtitle, "cover_subtitle"),
            Spacer(1, 12 * mm),
            note(summary, BLUE_LIGHT),
            Spacer(1, 58 * mm),
            data_table(
                ["项目", "内容"],
                [
                    ["项目名称", "基于多模态大模型的桌面 GUI 智能体开发与优化"],
                    ["阶段", "第 1 周：行业技术调研与开发环境搭建"],
                    ["形成日期", "2026 年 9 月 6 日"],
                    ["运行平台", "macOS / Apple Silicon；Kaggle 作为后续 GPU 实验环境"],
                ],
                [34, 135],
            ),
            PageBreak(),
        ]
    )


def build_research_report(path: Path) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        title="GUI 智能体技术调研报告",
        author="桌面 GUI 智能体实习项目",
        subject="第一周阶段交付物",
    )
    story: list = []
    cover(
        story,
        "GUI 智能体技术调研报告",
        "从 Agent 基础到桌面操作闭环：UI-TARS、Claude Computer Use 与 ScreenAgent 调研",
        "本周没有把目标定成“复现某个大模型”，而是先回答三个更实际的问题：GUI Agent 由哪些模块组成，三类代表性方案的差异在哪里，以及在一台 Apple Silicon Mac 上应该从哪条路线开始。",
    )

    story += section("1. 调研目标与判断")
    story.append(p("桌面 GUI 智能体的目标，是让模型在没有专用业务 API 的情况下，根据屏幕状态完成点击、输入、滚动和拖拽等操作。它与传统 RPA 的区别不在于是否能点击，而在于下一步动作是否由模型结合当前界面动态决定。"))
    story.append(flow_diagram())
    story.append(Spacer(1, 4 * mm))
    story.append(
        note(
            "本周形成的判断：先做可观测、可中断的单步闭环，比一开始追求长任务自治更重要。每次动作后重新截图，能够同时服务于成功判断、错误恢复和后续轨迹数据积累。"
        )
    )

    story += sub("1.1 Agent 与固定工作流")
    story.append(p("固定工作流按照预先写好的路径运行，适合步骤稳定的任务；Agent 则让模型根据环境反馈选择工具和调整计划。Anthropic 的工程经验强调从简单、可组合的模式起步，并在确实能提升结果时再增加复杂度。对本项目而言，第一版更适合采用“有限动作集 + 明确状态机”，而不是直接开放全部桌面权限。"))

    story += sub("1.2 共同技术栈")
    story.append(
        data_table(
            ["模块", "输入与输出", "本项目关注点"],
            [
                ["屏幕感知", "截图 -> 文字、图标、区域", "OCR 与视觉模型互补，小目标需要保留足够分辨率"],
                ["任务规划", "用户目标 + 历史 -> 下一步", "任务拆分、停止条件、失败后的重新规划"],
                ["动作执行", "结构化动作 -> 系统事件", "坐标换算、动作白名单、超时与异常返回"],
                ["结果反馈", "新截图/工具结果 -> 状态", "不依赖模型“猜测成功”，必须获取环境证据"],
                ["轨迹记录", "状态、动作、结果 -> 会话", "为调试、评测和后续微调保留数据"],
            ],
            [32, 58, 79],
        )
    )

    story += section("2. 三种代表性方案")
    story += sub("2.1 UI-TARS：端到端的原生 GUI 模型")
    story.append(p("UI-TARS 直接以截图作为主要视觉输入，输出键盘或鼠标动作。论文将能力拆为增强感知、统一动作建模、System-2 推理以及带反思的在线轨迹迭代训练。它的优势是把 GUI 定位和动作生成放进同一模型目标中；代价是模型部署、数据构建和坐标后处理更重。"))
    story.append(p("对当前项目最有价值的不是立即复现完整训练，而是两点：第一，动作格式要跨应用保持一致；第二，截图尺寸、模型输入尺寸和实际点击坐标必须记录在同一条轨迹里。", "small"))

    story += sub("2.2 Claude Computer Use：模型提出动作，应用负责执行")
    story.append(p("Claude Computer Use 把桌面控制定义为客户端工具集。模型返回 screenshot、left_click、type 等结构化工具调用，开发者自己的程序按顺序执行，再将 tool_result 和新截图送回模型。这个接口明确划分了“决策”和“执行”，也便于在中间加入权限检查、动作确认与错误返回。"))
    story.append(p("官方文档特别强调隔离环境、限制敏感数据与网络范围，以及对付款、同意条款等有现实后果的动作保留人工确认。该方案适合快速验证闭环，但需要持续考虑 API 成本、网络依赖和提示词注入风险。", "small"))

    story += sub("2.3 ScreenAgent：规划、执行、反思的显式状态机")
    story.append(p("ScreenAgent 使用 VLM 观察真实桌面截图，并通过控制器连接 VNC 环境。控制流程被明确拆成 Planning、Acting 和 Reflecting：先拆子任务，再输出鼠标键盘动作，最后查看执行结果并决定继续、重试或调整计划。其数据集保存日常电脑任务中的截图和动作序列。"))
    story.append(p("该方案与本项目的工程目标最接近，因为控制器职责清晰，替换模型并不会改变截图、执行和日志模块。Mac 原型可以先不用 VNC，直接以 mss 和 PyAutoGUI 实现同样的控制循环。", "small"))

    story += section("3. 方案对比与技术取舍")
    story.append(
        data_table(
            ["维度", "UI-TARS", "Claude Computer Use", "ScreenAgent"],
            [
                ["技术定位", "GUI 专用端到端模型", "通用模型的桌面工具能力", "VLM + 控制器研究框架"],
                ["动作来源", "模型直接生成统一动作", "模型返回客户端工具调用", "模型输出由控制器解析"],
                ["反馈方式", "新截图与历史轨迹", "tool_result 与新截图", "VNC 执行结果与新截图"],
                ["开发优势", "可研究定位和训练方法", "接入快，推理能力强", "模块边界清楚，方便调试"],
                ["主要成本", "模型和数据资源要求高", "API、网络与安全治理", "VNC、控制器和模型服务配置"],
                ["当前用途", "作为后续模型优化参照", "作为能力上限和接口参照", "作为第一版系统结构参照"],
            ],
            [25, 48, 48, 48],
            font_size=7.8,
        )
    )

    story += sub("3.1 仍未解决的五类问题")
    story.append(p("<b>感知误差。</b> 小图标、低对比文字、遮挡和相似按钮会造成错误识别；仅使用 OCR 无法覆盖纯图标，单独依赖 VLM 又增加延迟。"))
    story.append(p("<b>坐标误差。</b> 模型输入通常经过缩放或裁剪，Mac 还可能存在逻辑坐标与物理像素差异。坐标必须与截图尺寸绑定，不能只保存一个孤立的 (x, y)。"))
    story.append(p("<b>长程累积误差。</b> 前一步没有成功，后续计划仍按成功状态继续，就会快速偏离目标。解决方向是单步验证、重试上限和重新规划。"))
    story.append(p("<b>时延与成本。</b> 每轮需要截图、推理和执行；完整桌面控制应优先调用更窄的确定性工具，只在视觉判断不可替代时使用 VLM。"))
    story.append(p("<b>安全边界。</b> 网页中的恶意文字可能影响模型决策。测试环境要与个人数据隔离，删除、发送、付款和授权类动作默认不自动执行。"))

    story += section("4. 本项目第一版技术路线")
    story.append(architecture_diagram())
    story.append(Spacer(1, 3 * mm))
    story.append(p("结合本周调研和本机条件，第一版采用模块化路线：Mac 负责真实屏幕截图和鼠标键盘执行；Agent 控制器负责状态、动作解析、安全校验和日志；Kaggle 负责后续数据处理、GPU 推理实验与微调。这样既保留真实桌面测试，也避免把重型模型与 GUI 控制进程绑在一起。"))

    story += sub("4.1 最小可用版本范围")
    story.append(
        data_table(
            ["优先级", "能力", "验收方式"],
            [
                ["P0", "全屏截图与分辨率记录", "截图可打开，尺寸与屏幕读数一致"],
                ["P0", "click、type、scroll 三类动作", "在受控测试页面逐项验证"],
                ["P0", "动作后重新截图", "每条动作都有 before/after 证据"],
                ["P1", "OCR 与边界框绘制", "文字内容和坐标可视化"],
                ["P1", "失败重试与安全拦截", "越界坐标和敏感动作不会直接执行"],
            ],
            [20, 79, 70],
        )
    )
    story.append(note("下一周进入桌面感知与控制模块开发。先完成可重复的截图、OCR 和动作单元测试，再接入大模型规划；这条顺序能把“模型判断错”和“控制模块执行错”分开定位。", BLUE_LIGHT))

    story += section("5. 本周结论")
    story.append(p("经过对三类方案的对照，GUI Agent 的关键并不是让模型一次性给出完整操作脚本，而是建立可靠的环境反馈。当前项目已经具备本地截图、OCR 和鼠标控制基础，下一步应把这些能力包装成小而清晰的工具，并为每次调用保留可复查的日志。"))
    story.append(p("本周技术选择保持克制：不在 Mac 上强行走 CUDA，也不立即部署完整 UI-TARS；先用模块化控制器完成可测闭环，再根据定位准确率和任务成功率决定是否引入更重的模型与微调。"))

    story += sub("参考资料")
    references = [
        "[1] Anthropic, Building Effective Agents, 2024. https://www.anthropic.com/engineering/building-effective-agents",
        "[2] Qin et al., UI-TARS: Pioneering Automated GUI Interaction with Native Agents, 2025. https://arxiv.org/abs/2501.12326",
        "[3] Anthropic, Computer Use Tool Documentation. https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool",
        "[4] Niu et al., ScreenAgent: A Vision Language Model-driven Computer Control Agent, IJCAI 2024. https://arxiv.org/abs/2402.07945",
        "[5] ScreenAgent Official Repository. https://github.com/niuzaisheng/ScreenAgent",
    ]
    for item in references:
        story.append(p(item, "reference"))

    doc.build(story, onFirstPage=page_decorator("GUI 智能体技术调研报告"), onLaterPages=page_decorator("GUI 智能体技术调研报告"))


def build_environment_doc(path: Path) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        title="开发环境配置与验证文档",
        author="桌面 GUI 智能体实习项目",
        subject="第一周阶段交付物",
    )
    story: list = []
    cover(
        story,
        "开发环境配置与验证文档",
        "macOS 本地 GUI 执行环境与 Kaggle GPU 实验环境分工",
        "本文件记录的是已经实际完成的配置，而不是理想环境清单。本地部分已通过依赖导入、OCR、截图、坐标一致性和鼠标控制测试；CUDA 不适用于 Apple Silicon，因此后续重型训练转移到 Kaggle。",
    )

    story += section("1. 环境策略")
    story.append(p("项目大纲要求 Python 3.10+、PyTorch 2.2+，并建议在有 NVIDIA GPU 时配置 CUDA。本机为 Apple Silicon，无法使用 NVIDIA CUDA。为避免在不适用的路径上消耗时间，本项目把环境拆成两层：Mac 负责真实桌面交互，Kaggle 负责需要 GPU 的模型实验。"))
    story.append(
        data_table(
            ["环境", "主要职责", "本周状态"],
            [
                ["Mac 本地", "截图、OCR、鼠标键盘、权限控制、轨迹记录", "核心依赖和基础操作已验证"],
                ["Kaggle Notebook", "公开数据处理、模型推理、LoRA 微调、离线评测", "已登录，后续周次按任务接入"],
                ["云端模型 API", "用于比较多模态理解与规划效果", "可选，不作为第一周验收条件"],
            ],
            [36, 82, 51],
        )
    )

    story += sub("1.1 本机信息")
    story.append(
        data_table(
            ["项目", "实际值"],
            [
                ["操作系统", "macOS 26.6.2（Build 25G83）"],
                ["处理器架构", "arm64 / Apple Silicon"],
                ["Python", "3.12.14，项目内独立虚拟环境 .venv"],
                ["PyTorch", "2.13.0；MPS 已编译，当前自动化启动器不作为加速验收环境"],
                ["Git", "2.50.1（Apple Git-155）"],
                ["开发工具", "/Library/Developer/CommandLineTools"],
                ["桌面坐标", "截图 1470 × 956；PyAutoGUI 1470 × 956；比例 1:1"],
            ],
            [46, 123],
        )
    )

    story += section("2. 安装与复现步骤")
    story += sub("2.1 进入项目并启用虚拟环境")
    story.append(code_block([
        "cd '/Users/ziang/Documents/ChatGPT/New project'",
        "source .venv/bin/activate",
        "python --version",
    ]))
    story.append(Spacer(1, 3 * mm))
    story.append(p("虚拟环境隔离了项目依赖，避免覆盖 macOS 自带 Python。终端提示 command not found 时，优先确认当前目录和 .venv 是否存在；也可以直接使用 .venv/bin/python，减少 shell 环境差异。", "small"))

    story += sub("2.2 安装核心依赖和 OCR")
    story.append(code_block([
        "python -m pip install --upgrade pip",
        "python -m pip install -r requirements-mac.txt",
        "python -m pip install -r requirements-ocr.txt",
    ]))
    story.append(Spacer(1, 3 * mm))
    story.append(p("OCR 模型文件保存在项目内的 artifacts/easyocr 目录，便于重复运行并减少对用户缓存目录的依赖。"))

    story += sub("2.3 当前关键依赖版本")
    story.append(
        data_table(
            ["类别", "软件包", "已安装版本"],
            [
                ["视觉与数组", "numpy / Pillow / OpenCV", "2.5.2 / 12.3.0 / 5.0.0.93"],
                ["桌面截图", "mss", "10.2.0"],
                ["桌面控制", "PyAutoGUI / pynput", "0.9.54 / 1.8.2"],
                ["OCR", "EasyOCR", "1.7.2"],
                ["深度学习", "torch / torchvision", "2.13.0 / 0.28.0"],
                ["开发质量", "pytest / ruff", "9.1.1 / 0.16.5"],
            ],
            [35, 76, 58],
        )
    )

    story += section("3. macOS 权限设置")
    story.append(p("macOS 会把屏幕读取和输入控制权限绑定到启动 Python 的应用。如果从 Terminal、IDE 或其他启动器运行，可能需要分别授权。权限修改后应退出并重新打开对应应用。"))
    story.append(
        data_table(
            ["权限", "用途", "设置位置"],
            [
                ["屏幕与系统音频录制", "允许 mss / PyAutoGUI 获取桌面图像", "系统设置 -> 隐私与安全性"],
                ["辅助功能", "允许发送鼠标和键盘事件", "系统设置 -> 隐私与安全性"],
            ],
            [50, 64, 55],
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(note("安全设置：保留 PyAutoGUI 的左上角紧急停止功能。开发阶段只在测试页面执行动作；删除文件、提交表单、发送消息和付款操作不进入自动执行白名单。", BLUE_LIGHT))

    story += section("4. 验证记录")
    story.append(
        status_table(
            [
                ["通过", "核心依赖导入", "PyAutoGUI、mss、OpenCV、EasyOCR 均可导入，终端输出“环境正常”。"],
                ["通过", "OCR 冒烟测试", "合成图像文字识别结果为 HELLO GUI AGENT 123。"],
                ["通过", "屏幕截图", "已生成 screen_test.png，文件正常出现在项目目录。"],
                ["通过", "坐标一致性", "截图像素 1470 × 956，鼠标坐标 1470 × 956，当前无需 Retina 比例补偿。"],
                ["通过", "鼠标控制", "PyAutoGUI 可将指针移动到屏幕中央，辅助功能链路正常。"],
            ]
        )
    )

    story += sub("4.1 验证命令")
    story.append(code_block([
        "python scripts/check_mac_environment.py",
        "python scripts/check_easyocr.py",
        "python -c \"import mss; mss.mss().shot(output='screen_test.png')\"",
        "python -c \"import pyautogui as p; print(p.size())\"",
    ]))
    story.append(Spacer(1, 3 * mm))
    story.append(p("说明：如果检查脚本从未授权的启动器运行，可能显示 screen=0x0 或 Accessibility not granted。此时问题位置在启动应用的 macOS 权限，不是 Python 包；回到已授权的 Terminal 重新运行即可。", "small"))

    story += section("5. 坐标处理约定")
    story.append(p("当前原始截图和 PyAutoGUI 使用同一坐标空间，因此直接基于原图识别时可按 1:1 点击。模型推理前若缩放图片，则必须将模型坐标换回原始屏幕尺寸："))
    story.append(code_block([
        "screen_x = model_x * 1470 / model_image_width",
        "screen_y = model_y * 956  / model_image_height",
    ]))
    story.append(Spacer(1, 3 * mm))
    story.append(p("每条动作日志至少保存 original_size、model_input_size、predicted_coordinate 和 executed_coordinate。若后续加入裁剪或留白，还要记录 crop_offset 或 padding，防止坐标误差无法复现。"))

    story += section("6. 目录与维护约定")
    story.append(code_block([
        "New project/",
        "  .venv/                  # local Python environment",
        "  requirements-mac.txt    # core macOS dependencies",
        "  requirements-ocr.txt    # optional OCR stack",
        "  scripts/                # checks and utilities",
        "  artifacts/easyocr/      # OCR model files",
        "  output/pdf/             # stage deliverables",
    ]))
    story.append(Spacer(1, 3 * mm))
    story.append(p("依赖更新后应重新执行两份检查脚本，并把失败位置、原因和修复写进日志。不要用 sudo 向系统 Python 安装包，也不要把账号密钥写入 Notebook 或版本库。"))

    story += section("7. 当前可用能力与下一步")
    story.append(p("截至本周结束，本地已经可以稳定完成截图、英文 OCR 冒烟测试、屏幕尺寸读取和鼠标移动。这些结果满足第一周“测试基础工具库”的要求，也为第二周的实时截图、UI 识别、点击输入、滚动拖拽和边界框绘制提供了可复现起点。"))
    story.append(
        data_table(
            ["下一周任务", "完成判据"],
            [
                ["封装截图模块", "输出图像、时间戳和原始尺寸"],
                ["接入中英文 OCR", "输出文字、置信度和边界框"],
                ["封装基础动作", "click、type、scroll、drag 可单独测试"],
                ["绘制识别结果", "截图上可显示元素框和编号"],
                ["补充单元测试", "坐标越界和空识别结果不会触发动作"],
            ],
            [86, 83],
        )
    )

    story.append(
        p(
            "相关文件：MAC_SETUP.md；requirements-mac.txt；requirements-ocr.txt；"
            "scripts/check_mac_environment.py；scripts/check_easyocr.py。",
            "reference",
        )
    )

    doc.build(story, onFirstPage=page_decorator("开发环境配置与验证文档"), onLaterPages=page_decorator("开发环境配置与验证文档"))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    research_path = OUTPUT_DIR / "week1_gui_agent_research_report.pdf"
    environment_path = OUTPUT_DIR / "week1_environment_setup.pdf"
    build_research_report(research_path)
    build_environment_doc(environment_path)
    print(research_path)
    print(environment_path)


if __name__ == "__main__":
    main()
