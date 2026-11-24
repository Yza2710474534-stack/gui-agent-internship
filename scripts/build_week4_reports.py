"""按第二周交付格式生成第四周周报和验收测试报告。"""

import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
QA_DIR = ROOT / "tmp" / "week4_docs"
OUTPUT_DIR = ROOT / "output" / "docx"
FONT = os.environ.get("WEEK4_DOC_FONT", "Hiragino Sans GB")
SOURCES = {
    "weekly": (ROOT / "output/docx/第二周周报.docx",
               "1e75aa8e6bc7878db0d9b6acf519372dddf40c92060a285a9847348a91310ebf"),
    "acceptance": (ROOT / "output/docx/第二周验收测试报告.docx",
                   "2240f189c93cf49b4172757d69cac11f0c502f4699dd3ea04b48b06f90a93529"),
}


def check_reference(path, digest):
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != digest:
        raise RuntimeError(f"第二周模板已变化，请重新核对：{path}")


def set_font(run, size=None, bold=None):
    run.font.name = FONT
    run.font.color.rgb = RGBColor(0, 0, 0)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    rfonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
        rfonts.set(qn("w:" + key), FONT)


def fix_styles(doc):
    for name, size in (("Normal", 11), ("Title", 18), ("Heading 1", 12)):
        style = doc.styles[name]
        style.font.name = FONT
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = name != "Normal"
        rfonts = style._element.get_or_add_rPr().get_or_add_rFonts()
        for key in ("ascii", "hAnsi", "eastAsia", "cs"):
            rfonts.set(qn("w:" + key), FONT)


def replace_paragraph(paragraph, text, size=None):
    paragraph.text = text
    if text:
        set_font(paragraph.runs[0], size=size)


def add_record_image(path, title, rows):
    """将真实保存的记录排版为图；不是屏幕截图。"""
    width, height = 1500, 80 + len(rows) * 70
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    font_path = "/System/Library/Fonts/Menlo.ttc"
    title_font = ImageFont.truetype(font_path, 31)
    body_font = ImageFont.truetype(font_path, 28)
    draw.rectangle((3, 3, width - 4, height - 4), outline="#C9D1D9", width=3)
    draw.rectangle((4, 4, width - 5, 68), fill="#EEF4F8")
    draw.text((28, 20), title, font=title_font, fill="#152A3B")
    for index, row in enumerate(rows):
        draw.text((30, 85 + index * 70), row, font=body_font, fill="#22313F")
    canvas.save(path)


def remove_unused_images(doc):
    """模板的旧截图不应作为隐藏附件随新周报交付。"""
    used = {node.get(qn("r:embed")) for node in doc.element.body.xpath(".//a:blip")}
    for rel_id, rel in list(doc.part.rels.items()):
        if rel.reltype == RELATIONSHIP_TYPE.IMAGE and rel_id not in used:
            del doc.part.rels[rel_id]


def source_data():
    preview = json.loads((ROOT / "output/week4/realtime_preview.json").read_text(encoding="utf-8"))
    live = json.loads((ROOT / "output/week4/live_browser/20260922_193422/result.json").read_text(encoding="utf-8"))
    unit = (ROOT / "reports/week4_unittest.txt").read_text(encoding="utf-8")
    full = (ROOT / "reports/week4_full_unittest.txt").read_text(encoding="utf-8")
    if "Ran 22 tests" not in unit or "OK" not in unit:
        raise RuntimeError("第四周测试日志与报告数字不符")
    if "Ran 113 tests" not in full or "OK" not in full:
        raise RuntimeError("全量测试日志与报告数字不符")
    if live["status"] != "done" or not all(live["conditions"].values()):
        raise RuntimeError("真实浏览器记录未通过")
    return preview, live


def make_weekly(preview, live):
    reference, digest = SOURCES["weekly"]
    check_reference(reference, digest)
    doc = Document(reference)
    fix_styles(doc)
    doc.core_properties.title = "第四周项目周报"
    doc.core_properties.subject = "桌面 GUI 智能体第四周进度"
    paragraphs = doc.paragraphs
    replacements = {
        0: "第四周项目周报",
        1: "本周完成可暂停的实时循环、截图与 OCR 观察适配器、结构化动作规划和浏览器搜索完成判断。第四周专项测试22项、项目全量回归113项均通过；Chrome 搜索完成了现场复测。",
        2: "一 本周任务完成情况",
        3: "1. 新增预览与真实两种运行模式。实时循环记录 JSONL 事件，限制动作次数，支持失败重试和运行时长上限；动作后重新观察，再判断下一步。",
        4: "2. 将截图、屏幕区域、坐标比例和 OCR 结果整理为观察数据。截图尺寸与 OCR 尺寸不一致时，适配器会拒绝该观察结果。",
        5: "3. 模型规划结果只能是结构化的 click、type_text、scroll、wait、done 或 stop。未知动作、任意代码和多余字段均被拒绝。",
        6: "4. 在 Chrome 新标签页搜索 GUI Agent，确认标题、搜索框与多个结果；整理第四周代码包、专项测试日志和验收材料。",
        7: "二 是否达到预期",
        8: "本周代码与离线验证达到预期：22项第四周测试全部通过，全量113项通过。真实浏览器搜索已通过屏幕观察与无障碍树核查。",
        9: "尚未用项目的 MSS 截图后端完成单程序实时闭环。本次终端返回“未检测到可用屏幕”，因此第四周没有新保存的 Chrome 截图和 OCR 文件；真实搜索也未调用收费模型。",
        10: "三 下周工作计划",
        11: "1. 检查终端屏幕录制权限，恢复 MSS 实时截图，并保存同一次搜索的前后画面与 OCR 证据。",
        12: "2. 将观察、结构化规划、控制和完成判断接成同一程序，先在浏览器搜索任务上做限次实测。",
        13: "3. 验证动作失败后的重新定位与停止流程；把现场证据同 JSONL 日志逐步对齐。",
        14: "4. 再选择文件打开或文本编辑做一类真实任务复测，并继续区分模拟结果和现场结果。",
        16: "四 实际运行结果截图与记录",
        17: "本周 Chrome 页面曾通过屏幕观察核查，但当前终端未能保存项目格式的本地截图。以下两图根据本周实际保存的 JSON 与测试日志排版，仅作为运行记录节选。",
        19: "图1 离线预览记录。状态为 preview_ready，动作数为0；坐标(400,65)来自演示数据，不能用于当前桌面点击。",
        21: "图2 真实搜索核查记录及测试计数。Chrome 页面通过现场观察；第四周未保存新的本地 OCR 文件。",
        22: "原始记录：output/week4/realtime_preview.json；output/week4/live_browser/20260922_193422/result.json；reports/week4_unittest.txt。",
    }
    for index, text in replacements.items():
        replace_paragraph(paragraphs[index], text)

    figure1 = QA_DIR / "week4_preview_record.jpg"
    figure2 = QA_DIR / "week4_live_record.png"
    add_record_image(figure1, "WEEK 4 PREVIEW RECORD", [
        "mode: preview        status: preview_ready",
        f"cycle: {preview['cycle']}             action_count: {preview['action_count']}",
        "proposed_action: click x=400 y=65  [demo data]",
    ])
    add_record_image(figure2, "WEEK 4 LIVE SEARCH RECORD", [
        f"browser: {live['browser']}      status: {live['status']}",
        "query: GUI Agent        result heading: present",
        "week4 tests: 22/22    full regression: 113/113",
        "local Chrome PNG/OCR: not saved in this run",
    ])
    for index, path in ((18, figure1), (20, figure2)):
        paragraphs[index].text = ""
        run = paragraphs[index].add_run()
        run.add_picture(str(path), width=Inches(6.75))
    remove_unused_images(doc)
    output = OUTPUT_DIR / "第四周周报.docx"
    doc.save(output)
    return output


def make_acceptance(live):
    reference, digest = SOURCES["acceptance"]
    check_reference(reference, digest)
    doc = Document(reference)
    fix_styles(doc)
    doc.core_properties.title = "第四周实时循环验收测试报告"
    doc.core_properties.subject = "桌面 GUI 智能体第四周测试与实测边界"
    paragraphs = doc.paragraphs
    replacements = {
        0: "第四周实时循环验收测试报告",
        1: "第四周新增实时循环、观察适配器、结构化规划和浏览器搜索验证。专项测试22项、项目全量回归113项均通过；Chrome 搜索完成现场复测。项目截图后端在本次终端不可用，故尚不能认定单程序真实闭环验收通过。",
        2: "一 对照第四周任务",
        3: "运行器：默认预览只产生建议动作；显式真实模式才调用执行器，并记录动作、验证、重试、停止和超时事件。",
        4: "观察：截图与 OCR 结果统一为含图片路径、屏幕区域和坐标比例的观察数据；尺寸错配直接拒绝。",
        5: "规划：只接收结构化动作、done 或 stop；白名单动作经过参数检查后才可进入运行循环。",
        6: "完成判断：真实模式动作后重新观察；浏览器搜索最终由搜索词和结果证据单独判断。",
        7: "二 自动测试和实测结果",
        8: "2026年9月22日保存的第四周日志显示22项专项测试通过，0项失败；全量回归113项通过，0项失败。单元测试使用构造数据和模拟执行器，不代表现场鼠标与截图已接通。",
        9: "Chrome 现场复测：新标签页搜索 GUI Agent，窗口标题、搜索框、搜索结果标题和多个相关结果均通过无障碍树与屏幕观察核查。记录为 output/week4/live_browser/20260922_193422/result.json；既有运行截图见附录。",
        10: "本次终端执行项目 MSS 截图命令返回“未检测到可用屏幕”。因此没有第四周新保存的本地 Chrome PNG 或 OCR JSON；第三周已有截图不能作为本次新证据。",
        11: "三 问题与验收边界",
        12: "实时循环各模块已通过测试，但尚未由同一程序完成真实截图、OCR、规划、控制和完成判断。真实搜索使用浏览器交互复测，未调用收费模型。其他办公流程仍为模拟；消息不会自动发送。",
        13: "四 提交材料与复现",
        14: "单独提交本报告、第四周周报和 output/week4_submission_package.zip。代码包为第四周增量材料，需放入现有项目；测试命令与运行边界见 WEEK4_PLAN.md，原始日志见 reports/week4_unittest.txt 与 reports/week4_full_unittest.txt。",
        16: "五 各模块测试用例与结果",
        17: "按 test 方法计数：第四周专项共22项，通过22项；全量回归共113项，通过113项。模块分布见下表。",
        18: "六 一个完整用例说明",
        19: "案例：默认预览模式。提供模拟观察结果，并让规划器给出 click(10,20)；执行器替身记录调用次数。预期只生成动作建议，状态为 preview_ready，动作数为0。",
        20: "实际：tests/test_week4_realtime.py 的 test_preview_never_calls_execute 通过；执行器调用次数为0，日志末项为 action_proposed。该用例证明预览边界，不证明坐标适用于真实屏幕。",
        21: "真实搜索另行现场核查。由于本次 MSS 截图失败，报告不以该现场复测声称项目实时循环已端到端运行。",
    }
    for index, text in replacements.items():
        replace_paragraph(paragraphs[index], text)

    rows = [
        ("测试模块", "用例如何设计", "代表案例与预期结果", "测试数", "通过数"),
        ("循环与预览", "预览、两步运行及单步失败", "预览不调用执行器；真实模式动作后重新观察。", "3", "3"),
        ("停止与完成", "停止指令、最终判断及立即超时", "done 仍需完成条件通过；超时前不观察。", "3", "3"),
        ("重试与动作保护", "重试、动作上限、非法输入和等待", "重试一次成功；动作超限前停止执行。", "4", "4"),
        ("观察适配器", "保存证据、尺寸错配和复用", "OCR 尺寸错误时拒绝观察结果。", "3", "3"),
        ("结构化规划", "解析动作、完成、停止及非法输出", "拒绝 shell、代码和额外字段。", "5", "5"),
        ("搜索完成判断", "既有真实证据、缺失证据与工厂函数", "保存的真实搜索截图可通过；缺文件失败。", "4", "4"),
        ("合计", "按 test 方法统计", "失败0项；真实浏览器复测另计", "22", "22"),
    ]
    table = doc.tables[0]
    if len(table.rows) != len(rows) or len(table.columns) != 5:
        raise RuntimeError("第二周模板的模块表格结构已变化")
    for row_index, values in enumerate(rows):
        for column_index, value in enumerate(values):
            cell = table.cell(row_index, column_index)
            cell.text = value
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(2)
                for run in paragraph.runs:
                    set_font(run, size=9.1, bold=row_index in (0, len(rows) - 1))

    screenshot = ROOT / "output/screenshots/screen_1_20260919_171319_864597.png"
    screenshot_digest = "dc16d982831f142220980692f4bc0b3541d7e895f3a61c7508ee5e821e1687a8"
    if hashlib.sha256(screenshot.read_bytes()).hexdigest() != screenshot_digest:
        raise RuntimeError(f"既有运行截图已变化，请重新核对：{screenshot}")
    heading = doc.add_paragraph(style="Heading 1")
    heading.paragraph_format.page_break_before = True
    replace_paragraph(heading, "附录 既有真实运行截图")
    context = doc.add_paragraph()
    replace_paragraph(
        context,
        "下图由项目终端于2026年9月19日17:13保存，显示真实 Chrome 搜索结果。第四周自动测试复用了这张既有截图；9月22日的现场复测虽经屏幕观察确认，但未新保存本地 PNG 或 OCR 文件。",
    )
    figure = doc.add_paragraph()
    figure.alignment = WD_ALIGN_PARAGRAPH.CENTER
    picture = figure.add_run().add_picture(str(screenshot), width=Inches(6.7))
    picture._inline.docPr.set(
        "descr", "2026年9月19日真实 Chrome 搜索 GUI Agent 的屏幕截图；第四周测试复用"
    )
    caption = doc.add_paragraph()
    replace_paragraph(
        caption,
        "图1 既有真实搜索截图。原始文件：output/screenshots/screen_1_20260919_171319_864597.png。",
        size=9,
    )
    output = OUTPUT_DIR / "第四周验收测试报告.docx"
    doc.save(output)
    return output


def main():
    QA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    preview, live = source_data()
    for output in (make_weekly(preview, live), make_acceptance(live)):
        print(output)


if __name__ == "__main__":
    main()
