"""生成第三周补充测试报告 PDF，并把本地截图直接嵌入文档。"""

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "第三周补充测试报告.pdf"


def register_fonts():
    font_path = "/System/Library/Fonts/STHeiti Medium.ttc"
    light_path = "/System/Library/Fonts/STHeiti Light.ttc"
    pdfmetrics.registerFont(TTFont("Heiti", font_path, subfontIndex=0))
    pdfmetrics.registerFont(TTFont("HeitiLight", light_path, subfontIndex=0))


def image(path, width):
    path = ROOT / path
    if not path.is_file():
        raise FileNotFoundError(path)
    item = Image(str(path))
    ratio = item.imageHeight / float(item.imageWidth)
    item.drawWidth = width
    item.drawHeight = width * ratio
    return item


def footer(canvas, document):
    canvas.saveState()
    canvas.setFont("HeitiLight", 8)
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawString(18 * mm, 10 * mm, "桌面 GUI 智能体 | 第三周补充测试报告")
    canvas.drawRightString(192 * mm, 10 * mm, f"第 {document.page} 页")
    canvas.restoreState()


def build():
    register_fonts()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        rightMargin=17 * mm, leftMargin=17 * mm,
        topMargin=16 * mm, bottomMargin=17 * mm,
        title="第三周补充测试报告",
        author="GUI Agent 项目",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleCN", parent=styles["Title"], fontName="Heiti", fontSize=20,
        leading=27, alignment=TA_CENTER, textColor=colors.HexColor("#16324F"),
        spaceAfter=6 * mm,
    )
    subtitle = ParagraphStyle(
        "SubtitleCN", parent=styles["Normal"], fontName="HeitiLight", fontSize=10,
        leading=16, alignment=TA_CENTER, textColor=colors.HexColor("#667085"),
        spaceAfter=8 * mm,
    )
    h1 = ParagraphStyle(
        "H1CN", parent=styles["Heading1"], fontName="Heiti", fontSize=14,
        leading=20, textColor=colors.HexColor("#16324F"), spaceBefore=4 * mm,
        spaceAfter=3 * mm,
    )
    h2 = ParagraphStyle(
        "H2CN", parent=styles["Heading2"], fontName="Heiti", fontSize=11,
        leading=16, textColor=colors.HexColor("#2364AA"), spaceBefore=3 * mm,
        spaceAfter=2 * mm,
    )
    body = ParagraphStyle(
        "BodyCN", parent=styles["BodyText"], fontName="HeitiLight", fontSize=9.5,
        leading=16, textColor=colors.HexColor("#253858"), spaceAfter=2.5 * mm,
    )
    small = ParagraphStyle(
        "SmallCN", parent=body, fontSize=8.2, leading=12, textColor=colors.HexColor("#475467"),
    )
    caption = ParagraphStyle(
        "CaptionCN", parent=small, alignment=TA_CENTER, textColor=colors.HexColor("#667085"),
        spaceBefore=1.5 * mm, spaceAfter=4 * mm,
    )
    cell = ParagraphStyle("CellCN", parent=small, fontSize=8.1, leading=12)
    cell_center = ParagraphStyle("CellCenterCN", parent=cell, alignment=TA_CENTER)
    cell_header = ParagraphStyle("CellHeaderCN", parent=cell, textColor=colors.white)
    cell_header_center = ParagraphStyle("CellHeaderCenterCN", parent=cell_header, alignment=TA_CENTER)

    story = []
    story.append(Paragraph("第三周补充测试报告", title))
    story.append(Paragraph(
        f"项目：基于多模态大模型的桌面 GUI 智能体开发与优化　　日期：{date.today().isoformat()}",
        subtitle,
    ))
    story.append(Paragraph("一、补充背景", h1))
    story.append(Paragraph(
        "原有第三周轨迹演示主要使用模拟反馈，状态变为 done 只能说明状态机走完步骤，不能证明真实桌面任务成功。本次补充围绕反馈中提出的长任务、异常恢复、日志收集、真实截图单步验证、完成判定和 Edge Case 进行测试。",
        body,
    ))
    story.append(Paragraph("二、补充实现", h1))
    story.append(Paragraph(
        "新增长任务运行器，要求每一步执行后先通过单步验证，再进入下一步；所有步骤通过后还要单独检查最终完成条件。运行器支持失败重试、执行异常捕获、重试耗尽停止、最大动作次数保护和 JSONL 事件日志。",
        body,
    ))
    story.append(Paragraph(
        "新增真实截图完成判断：读取终端获得的 Chrome 搜索截图和 EasyOCR JSON，检查图片尺寸、搜索框关键词、浏览器标识和搜索结果证据，避免仅因为页面中出现关键词就误判任务完成。",
        body,
    ))

    story.append(Paragraph("三、测试用例与结果", h1))
    rows = [
        [Paragraph("测试模块", cell_header_center), Paragraph("用例设计", cell_header), Paragraph("数量", cell_header_center), Paragraph("结果", cell_header_center)],
        [Paragraph("长任务闭环", cell), Paragraph("连续执行 6 个步骤，每步验证后再进入下一步，最后检查完成条件。", cell), Paragraph("1", cell_center), Paragraph("通过", cell_center)],
        [Paragraph("异常恢复", cell), Paragraph("单步失败后重试成功；执行抛出异常后恢复；重试耗尽后停止。", cell), Paragraph("3", cell_center), Paragraph("通过", cell_center)],
        [Paragraph("安全边界", cell), Paragraph("最大动作次数保护；步骤全部通过但最终条件失败时不能标记 done。", cell), Paragraph("2", cell_center), Paragraph("通过", cell_center)],
        [Paragraph("真实截图验证", cell), Paragraph("复核真实编辑菜单截图；验证真实 Chrome 搜索截图和结果条件。", cell), Paragraph("2", cell_center), Paragraph("通过", cell_center)],
        [Paragraph("截图与完成条件异常", cell), Paragraph("OCR 尺寸不一致；只有关键词但没有搜索结果。", cell), Paragraph("2", cell_center), Paragraph("通过", cell_center)],
    ]
    table = Table(rows, colWidths=[28 * mm, 103 * mm, 16 * mm, 18 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2364AA")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "HeitiLight"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D0D5DD")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "新增测试 15 项，全部通过；第三周测试共 54 项，通过 54 项；项目全量回归测试共 91 项，通过 91 项。",
        body,
    ))

    story.append(PageBreak())
    story.append(Paragraph("四、真实 Chrome 搜索任务", h1))
    story.append(Paragraph(
        "在 Chrome 新标签页中执行真实搜索任务：定位地址栏，输入并提交 GUI Agent，检查搜索页标题、搜索框内容、搜索结果标题和相关结果。浏览器控制通道完成了真实输入和提交，终端获得的截图随后由项目 OCR 和完成判断代码复核。",
        body,
    ))
    story.append(image("output/screenshots/screen_1_20260919_171319_864597.png", 170 * mm))
    story.append(Paragraph("图 1　真实 Chrome 搜索结果截图（1470 × 956，坐标比例 1:1）", caption))
    story.append(Paragraph(
        "OCR 识别到搜索框中的 gui agent，并识别到 gui-agents、GitHub、Topics 和中文 GUI Agent 文章等结果证据。自动完成判断结果为 success=true。",
        body,
    ))
    story.append(Paragraph("五、真实桌面单步操作前后对比", h1))
    before = image("output/demo/20260910_201203_070856/before_action.png", 81 * mm)
    after = image("output/demo/20260910_201203_070856/after_action.png", 81 * mm)
    pair = Table([[before, after]], colWidths=[86 * mm, 86 * mm])
    pair.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(pair)
    story.append(Paragraph("图 2　文本编辑“编辑”菜单操作前（左）与操作后（右），使用前后截图和 OCR 新增文字判断菜单展开。", caption))

    story.append(PageBreak())
    story.append(Paragraph("六、任务类型覆盖", h1))
    story.append(Paragraph(
        "长任务按照日常办公流程拆分，避免只用浏览器搜索代表所有任务。每类任务都有自己的步骤和完成条件。",
        body,
    ))
    scenario_rows = [
        [Paragraph("类别", cell_header_center), Paragraph("典型流程", cell_header), Paragraph("当前证据", cell_header)],
        [Paragraph("浏览器搜索", cell), Paragraph("打开浏览器、输入关键词、检查结果", cell), Paragraph("真实 Chrome 单次任务和截图 OCR 已通过", cell)],
        [Paragraph("打开文件", cell), Paragraph("定位文件、打开、检查内容", cell), Paragraph("状态机模拟测试已通过", cell)],
        [Paragraph("文本编辑", cell), Paragraph("定位编辑区、输入、检查文档", cell), Paragraph("已有真实菜单单步证据，长任务为模拟", cell)],
        [Paragraph("消息草稿", cell), Paragraph("定位草稿区、输入、检查内容", cell), Paragraph("状态机模拟测试已通过，不自动发送", cell)],
        [Paragraph("应用关闭", cell), Paragraph("确认保存、关闭、检查窗口消失", cell), Paragraph("状态机模拟测试已通过", cell)],
    ]
    scenario_table = Table(scenario_rows, colWidths=[28 * mm, 70 * mm, 69 * mm], repeatRows=1)
    scenario_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2364AA")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D0D5DD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(scenario_table)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("七、长任务日志与异常恢复", h1))
    story.append(Paragraph(
        "示例长任务共 6 步。第 3 步第一次验证失败，运行器记录失败原因并安排重试，第二次验证成功后继续执行，最终完成条件通过。该示例不操作真实桌面，用于验证运行器的控制逻辑。",
        body,
    ))
    log_rows = [
        [Paragraph("事件", cell_header_center), Paragraph("结果", cell_header_center), Paragraph("说明", cell_header)],
        [Paragraph("step_finished", cell), Paragraph("失败", cell_center), Paragraph("第 3 步第一次未找到地址栏，记录失败证据。", cell)],
        [Paragraph("retry_scheduled", cell), Paragraph("已安排", cell_center), Paragraph("进入第 3 步第二次尝试。", cell)],
        [Paragraph("step_finished", cell), Paragraph("成功", cell_center), Paragraph("第 3 步第二次验证通过。", cell)],
        [Paragraph("task_completed", cell), Paragraph("成功", cell_center), Paragraph("6 步完成，最终完成条件通过。", cell)],
    ]
    log_table = Table(log_rows, colWidths=[38 * mm, 24 * mm, 105 * mm], repeatRows=1)
    log_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2364AA")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D0D5DD")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFF8F0"), colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(log_table)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("八、当前结论与边界", h1))
    story.append(Paragraph(
        "本次补充已经覆盖长任务控制逻辑、重试、失败判定、完成判断、日志和 Edge Case，并完成了一次真实 Chrome 搜索及真实截图 OCR 复核。需要保留的边界是：真实浏览器操作目前通过授权的浏览器控制通道完成，项目自己的截图、OCR 和控制模块还没有在同一个程序中自动串联完成；真实任务本次首次成功，因此真实桌面重试仍由自动化测试覆盖。",
        body,
    ))
    story.append(Paragraph("报告对应文件", h1))
    story.append(Paragraph(
        "src/week3_runtime.py　|　tests/test_week3_runtime.py　|　scripts/verify_live_search.py　|　reports/week3/integration_test_report.md",
        small,
    ))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"PDF 已生成：{OUTPUT}")


if __name__ == "__main__":
    build()
