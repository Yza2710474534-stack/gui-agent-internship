from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "docx"
OUTPUT_PATH = OUTPUT_DIR / "第一周阶段交付物.docx"


def set_font(run, latin: str, east_asia: str, size: float, bold: bool = False) -> None:
    run.font.name = east_asia
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = None
    for key in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        run._element.rPr.rFonts.set(qn(key), east_asia)


def set_style_font(style, latin: str, east_asia: str, size: float, bold: bool = False) -> None:
    style.font.name = east_asia
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = None
    for key in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        style._element.rPr.rFonts.set(qn(key), east_asia)


def remove_paragraph_borders(style) -> None:
    p_pr = style._element.get_or_add_pPr()
    border = p_pr.find(qn("w:pBdr"))
    if border is not None:
        p_pr.remove(border)


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    set_font(run, "Arial", "Arial Unicode MS", 9)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, separate, text, end])


def add_body(doc: Document, text: str, first_line: bool = True):
    paragraph = doc.add_paragraph(style="Normal")
    paragraph.paragraph_format.first_line_indent = Pt(22) if first_line else None
    paragraph.paragraph_format.keep_together = False
    paragraph.add_run(text)
    return paragraph


def add_bold_lead(doc: Document, lead: str, text: str):
    paragraph = doc.add_paragraph(style="Normal")
    paragraph.paragraph_format.first_line_indent = None
    run = paragraph.add_run(lead)
    run.bold = True
    paragraph.add_run(text)
    return paragraph


def add_bullet(doc: Document, text: str):
    paragraph = doc.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.left_indent = Inches(0.28)
    paragraph.paragraph_format.first_line_indent = Inches(-0.16)
    paragraph.paragraph_format.space_after = Pt(3)
    paragraph.add_run(text)
    return paragraph


def configure_document(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)
    section.header_distance = Inches(0.3)
    section.footer_distance = Inches(0.32)

    styles = doc.styles
    set_style_font(styles["Normal"], "Arial", "Arial Unicode MS", 11)
    styles["Normal"].paragraph_format.line_spacing = 1.25
    styles["Normal"].paragraph_format.space_after = Pt(6)

    set_style_font(styles["Title"], "Arial", "Heiti SC", 20, bold=True)
    styles["Title"].paragraph_format.space_after = Pt(12)
    remove_paragraph_borders(styles["Title"])

    set_style_font(styles["Heading 1"], "Arial", "Heiti SC", 14, bold=True)
    styles["Heading 1"].paragraph_format.space_before = Pt(14)
    styles["Heading 1"].paragraph_format.space_after = Pt(6)
    styles["Heading 1"].paragraph_format.keep_with_next = True

    set_style_font(styles["Heading 2"], "Arial", "Heiti SC", 12, bold=True)
    styles["Heading 2"].paragraph_format.space_before = Pt(10)
    styles["Heading 2"].paragraph_format.space_after = Pt(4)
    styles["Heading 2"].paragraph_format.keep_with_next = True

    set_style_font(styles["List Bullet"], "Arial", "Arial Unicode MS", 11)
    styles["List Bullet"].paragraph_format.line_spacing = 1.2

    for section in doc.sections:
        add_page_number(section.footer.paragraphs[0])


def build_document() -> None:
    doc = Document()
    configure_document(doc)
    doc.core_properties.title = "第一周阶段交付物"
    doc.core_properties.subject = "GUI 智能体技术调研与开发环境配置"
    doc.core_properties.author = "桌面 GUI 智能体实习项目"

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("第一周阶段交付物")

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(14)
    run = subtitle.add_run("基于多模态大模型的桌面 GUI 智能体开发与优化")
    set_font(run, "Arial", "Arial Unicode MS", 11)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.paragraph_format.space_after = Pt(18)
    run = meta.add_run("阶段：第 1 周    日期：2026 年 9 月 6 日")
    set_font(run, "Arial", "Arial Unicode MS", 10)

    add_body(
        doc,
        "本周完成了 GUI 智能体基础调研和 Mac 开发环境搭建。调研范围包括 UI-TARS、Claude Computer Use 和 ScreenAgent。本地环境已经通过依赖导入、OCR、截图、坐标一致性和鼠标控制测试。考虑到本机使用 Apple Silicon，后续将由 Mac 负责桌面交互，Kaggle 负责需要 GPU 的模型实验。",
    )

    doc.add_heading("一 技术调研报告", level=1)

    doc.add_heading("GUI 智能体的基本结构", level=2)
    add_body(
        doc,
        "GUI 智能体接收用户任务，通过截图了解当前界面，再决定下一步鼠标或键盘操作。动作执行后，系统需要重新截图并检查结果。如果任务没有完成，模型会继续规划或调整操作。完整过程可以概括为：用户任务、屏幕感知、任务规划、动作执行和结果反馈。",
    )
    add_body(
        doc,
        "与传统 RPA 相比，GUI 智能体不完全依赖预先写好的固定步骤。它可以根据界面的实际变化选择下一步动作，但也会带来识别错误、点击偏移和长任务错误累积等问题。因此，第一版系统应限制动作范围，并在每次操作后检查结果。",
    )

    doc.add_heading("代表性方案", level=2)
    add_bold_lead(
        doc,
        "UI-TARS。",
        "该模型直接读取屏幕截图并生成鼠标或键盘动作，重点研究界面感知、坐标定位、统一动作表示和多步骤推理。它适合作为后续模型训练和定位优化的参考，但本地部署和训练对算力要求较高。",
    )
    add_bold_lead(
        doc,
        "Claude Computer Use。",
        "模型负责提出点击、输入和截图等工具调用，开发者编写的程序负责真正执行动作并返回结果。这种方式容易加入权限检查和人工确认，适合快速验证系统闭环。",
    )
    add_bold_lead(
        doc,
        "ScreenAgent。",
        "该项目把桌面控制分为规划、执行和反思三个阶段。控制器负责截图、解析动作、执行操作和维护状态。它的结构清楚，适合作为本项目第一版系统的参考。",
    )

    doc.add_heading("本周技术结论", level=2)
    add_body(
        doc,
        "本项目暂不复现完整的 UI-TARS 训练流程，而是先搭建模块化原型。Mac 负责截图和鼠标键盘操作，控制器负责任务状态、安全检查和日志，模型负责界面理解与动作规划。这样可以分别判断问题来自模型还是执行模块。",
    )
    for item in [
        "界面中的小图标、遮挡和相似按钮会影响识别准确率。",
        "模型输入图片经过缩放后，必须把坐标换回原始屏幕尺寸。",
        "每次动作后都要重新截图，不能直接假设操作已经成功。",
        "长任务需要设置最大步数、失败重试和重新规划。",
        "删除、发送、付款和授权等操作必须保留人工确认。",
    ]:
        add_bullet(doc, item)

    doc.add_heading("二 开发环境配置文档", level=1)

    doc.add_heading("本机环境", level=2)
    add_body(
        doc,
        "本机系统为 macOS 26.6.2，处理器架构为 arm64。项目使用 Python 3.12.14 和独立虚拟环境 .venv。Git 版本为 2.50.1，Apple Command Line Tools 已安装。",
    )
    add_body(
        doc,
        "目前安装的主要工具包括 PyTorch、OpenCV、MSS、PyAutoGUI、pynput 和 EasyOCR。MSS 用于截图，EasyOCR 用于文字识别，OpenCV 用于图像处理，PyAutoGUI 和 pynput 用于鼠标键盘控制。依赖清单保存在 requirements-mac.txt 和 requirements-ocr.txt。",
    )

    doc.add_heading("配置方式", level=2)
    add_body(
        doc,
        "项目目录位于 /Users/ziang/Documents/ChatGPT/New project。进入目录后启用 .venv，再根据两份 requirements 文件安装依赖。为避免终端出现 command not found，也可以直接使用项目中的 .venv/bin/python。详细操作保存在 MAC_SETUP.md。",
    )
    add_body(
        doc,
        "macOS 需要为启动 Python 的终端开启屏幕录制和辅助功能权限。权限修改后要重新打开终端。测试阶段保留 PyAutoGUI 的左上角紧急停止功能，并只在受控页面执行自动操作。",
    )

    doc.add_heading("实际验证结果", level=2)
    for item in [
        "PyAutoGUI、MSS、OpenCV 和 EasyOCR 均可正常导入。",
        "EasyOCR 已识别测试文字 HELLO GUI AGENT 123。",
        "MSS 已成功生成 screen_test.png。",
        "截图与鼠标坐标均为 1470 × 956，当前映射比例为 1 比 1。",
        "PyAutoGUI 可以正常移动鼠标，辅助功能权限有效。",
    ]:
        add_bullet(doc, item)
    add_body(
        doc,
        "本机不使用 NVIDIA CUDA。后续需要较大算力的数据处理、模型推理和 LoRA 微调放在 Kaggle 上完成，本地只保留真实桌面感知与执行功能。",
    )

    doc.add_heading("三 下一周工作", level=1)
    add_body(
        doc,
        "第二周将开始开发桌面感知和控制模块。为了便于定位问题，先分别测试每个模块，再接入大模型。计划完成以下内容：",
    )
    for item in [
        "封装截图功能，并保存时间和原始分辨率。",
        "接入中英文 OCR，输出文字、置信度和边界框。",
        "封装点击、输入、滚动和拖拽操作。",
        "在截图上绘制识别结果，并补充基础单元测试。",
    ]:
        add_bullet(doc, item)

    doc.add_heading("参考资料", level=1)
    references = [
        "1. Anthropic. Building Effective Agents. https://www.anthropic.com/engineering/building-effective-agents",
        "2. Qin 等. UI-TARS: Pioneering Automated GUI Interaction with Native Agents. https://arxiv.org/abs/2501.12326",
        "3. Anthropic. Computer Use Tool Documentation. https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool",
        "4. Niu 等. ScreenAgent: A Vision Language Model-driven Computer Control Agent. https://arxiv.org/abs/2402.07945",
    ]
    for item in references:
        paragraph = doc.add_paragraph(style="Normal")
        paragraph.paragraph_format.first_line_indent = None
        paragraph.paragraph_format.space_after = Pt(4)
        run = paragraph.add_run(item)
        set_font(run, "Arial", "Arial Unicode MS", 9)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT_PATH)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
