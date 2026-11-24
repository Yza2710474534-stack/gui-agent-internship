from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "docx"
OUTPUT_PATH = OUTPUT_DIR / "第一周周报.docx"


def set_run_font(run, size: float = 10.5, bold: bool = False, color: str = "000000") -> None:
    run.font.name = "Arial Unicode MS"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)
    run._element.get_or_add_rPr()
    for key in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        run._element.rPr.rFonts.set(qn(key), "Arial Unicode MS")


def set_style_font(style, size: float, bold: bool = False) -> None:
    style.font.name = "Arial Unicode MS"
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor(0, 0, 0)
    style._element.get_or_add_rPr()
    for key in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        style._element.rPr.rFonts.set(qn(key), "Arial Unicode MS")


def remove_paragraph_borders(style) -> None:
    p_pr = style._element.get_or_add_pPr()
    border = p_pr.find(qn("w:pBdr"))
    if border is not None:
        p_pr.remove(border)


def set_cell_fill(cell, color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), color)


def set_cell_borders(cell, color: str = "D9D9D9", size: str = "6") -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:color"), color)


def set_cell_margins(cell, top: int = 55, start: int = 85, bottom: int = 55, end: int = 85) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    margins = tc_pr.find(qn("w:tcMar"))
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_cell_text(cell, text: str, size: float = 8.8, bold: bool = False, align=WD_ALIGN_PARAGRAPH.LEFT) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = align
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.05
    run = paragraph.add_run(text)
    set_run_font(run, size=size, bold=bold)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_cell_margins(cell)
    set_cell_borders(cell)


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    set_run_font(run, size=9, color="666666")
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


def add_heading(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph(style="Heading 1")
    paragraph.add_run(text)


def add_body(doc: Document, text: str, bold_lead: str | None = None) -> None:
    paragraph = doc.add_paragraph(style="Normal")
    paragraph.paragraph_format.first_line_indent = None
    if bold_lead:
        run = paragraph.add_run(bold_lead)
        set_run_font(run, bold=True)
    run = paragraph.add_run(text)
    set_run_font(run)


def add_numbered_item(doc: Document, number: int, text: str) -> None:
    paragraph = doc.add_paragraph(style="Normal")
    paragraph.paragraph_format.left_indent = Inches(0.22)
    paragraph.paragraph_format.first_line_indent = Inches(-0.22)
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run(f"{number}. {text}")
    set_run_font(run)


def configure_document(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.45)
    section.bottom_margin = Inches(0.42)
    section.left_margin = Inches(0.68)
    section.right_margin = Inches(0.68)
    section.header_distance = Inches(0.2)
    section.footer_distance = Inches(0.2)

    styles = doc.styles
    set_style_font(styles["Normal"], 10)
    styles["Normal"].paragraph_format.line_spacing = 1.1
    styles["Normal"].paragraph_format.space_after = Pt(3)

    set_style_font(styles["Title"], 18, bold=True)
    styles["Title"].paragraph_format.space_after = Pt(4)
    remove_paragraph_borders(styles["Title"])

    set_style_font(styles["Heading 1"], 12, bold=True)
    styles["Heading 1"].paragraph_format.space_before = Pt(6)
    styles["Heading 1"].paragraph_format.space_after = Pt(3)
    styles["Heading 1"].paragraph_format.keep_with_next = True

    add_page_number(section.footer.paragraphs[0])


def build_document() -> None:
    doc = Document()
    configure_document(doc)
    doc.core_properties.title = "第一周项目周报"
    doc.core_properties.subject = "桌面 GUI 智能体项目进度跟踪与汇报"
    doc.core_properties.author = "项目成员"

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("第一周项目周报")

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(3)
    run = subtitle.add_run("基于多模态大模型的桌面 GUI 智能体开发与优化")
    set_run_font(run, size=10.5)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.paragraph_format.space_after = Pt(6)
    run = meta.add_run("项目周期  第 1 周     填报日期  2026 年 9 月 8 日     姓名  __________")
    set_run_font(run, size=9.5, color="555555")

    add_body(
        doc,
        "本周完成 GUI 智能体基础学习、Mac 环境配置和桌面控制验证。计划内任务均已完成，可以进入截图、OCR 和控制模块开发。",
        bold_lead="本周结论  ",
    )

    add_heading(doc, "一 本周任务完成情况")

    rows = [
        (
            "技术资料学习",
            "学习 GUI Agent、UI-TARS、Claude Computer Use 等资料。",
            "理解感知 推理 动作 反馈闭环。",
            "是",
        ),
        (
            "核心概念学习",
            "学习 GUI 动作、坐标映射、点击偏移和轨迹训练方法。",
            "能够说明模型如何借助工具操作电脑。",
            "是",
        ),
        (
            "开发环境配置",
            "完成 Python 环境及 PyAutoGUI、MSS、OpenCV、EasyOCR 安装。",
            "环境检查输出正常。",
            "是",
        ),
        (
            "桌面功能验证",
            "测试截图、尺寸读取、坐标一致性和鼠标移动。",
            "截图与坐标均为 1470 × 956，映射比例为 1 比 1。",
            "是",
        ),
        (
            "阶段材料整理",
            "整理技术调研和 Mac 环境配置说明。",
            "已形成第一周阶段材料。",
            "是",
        ),
    ]

    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    widths = [Inches(1.18), Inches(3.25), Inches(2.0), Inches(0.65)]
    headers = ["本周任务", "完成情况", "验证结果", "达标"]
    for index, (cell, header) in enumerate(zip(table.rows[0].cells, headers)):
        cell.width = widths[index]
        set_cell_fill(cell, "D9EAF7")
        set_cell_text(cell, header, size=9, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)

    for row_index, row_data in enumerate(rows):
        cells = table.add_row().cells
        for index, (cell, value) in enumerate(zip(cells, row_data)):
            cell.width = widths[index]
            if row_index % 2 == 1:
                set_cell_fill(cell, "F7FAFC")
            align = WD_ALIGN_PARAGRAPH.CENTER if index in (0, 3) else WD_ALIGN_PARAGRAPH.LEFT
            set_cell_text(cell, value, align=align)

    add_heading(doc, "二 目标达成情况")
    add_body(
        doc,
        "本周总体达到预期。Mac 已具备截图和鼠标控制能力。本机为 Apple Silicon，不配置 NVIDIA CUDA；后续 GPU 实验放在 Kaggle 完成，不影响当前进度。",
    )

    add_heading(doc, "三 下周工作计划")
    next_week = [
        "封装全屏截图和区域截图功能，记录原始分辨率。",
        "接入 EasyOCR，输出中英文文字、置信度和边界框。",
        "实现点击、输入、滚动和拖拽，并加入越界检查与紧急停止。",
        "完成坐标定位、边界框绘制和基础单元测试报告。",
    ]
    for index, item in enumerate(next_week, start=1):
        add_numbered_item(doc, index, item)

    add_body(
        doc,
        "预计交付桌面感知与控制模块代码，以及一份简洁的单元测试报告。",
        bold_lead="下周交付物  ",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT_PATH)
    print(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
