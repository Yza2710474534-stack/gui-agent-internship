"""沿用第二周最终版模板生成第三周周报和验收报告。"""

import json
import re
import shutil
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "output/docx"
WEEKLY_TEMPLATE = DOCS / "第二周周报.docx"
ACCEPTANCE_TEMPLATE = DOCS / "第二周验收测试报告.docx"
WEEKLY_OUTPUT = DOCS / "第三周周报.docx"
ACCEPTANCE_OUTPUT = DOCS / "第三周验收测试报告.docx"
FONT_NAME = "Heiti SC"


def set_font(run, size=11, bold=False):
    run.font.name = FONT_NAME
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    fonts = run._element.get_or_add_rPr().rFonts
    for key in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        fonts.attrib.pop(qn("w:" + key), None)
    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn("w:" + key), FONT_NAME)


def clear_paragraph(paragraph):
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)


def set_text(paragraph, value, size=11, bold=False):
    clear_paragraph(paragraph)
    run = paragraph.add_run(value)
    set_font(run, size, bold)


def set_picture(paragraph, image_path, width, description):
    clear_paragraph(paragraph)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    shape = paragraph.add_run().add_picture(str(image_path), width=Inches(width))
    shape._inline.docPr.set("descr", description)


def set_cell(cell, value, size=9.5, bold=False, centered=False):
    paragraph = cell.paragraphs[0]
    set_text(paragraph, str(value), size, bold)
    paragraph.paragraph_format.space_before = Pt(1.5)
    paragraph.paragraph_format.space_after = Pt(1.5)
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if centered else WD_ALIGN_PARAGRAPH.LEFT


def build_weekly():
    shutil.copyfile(WEEKLY_TEMPLATE, WEEKLY_OUTPUT)
    doc = Document(WEEKLY_OUTPUT)
    paragraphs = doc.paragraphs
    content = {
        0: ("第三周项目周报", 18, True),
        1: ("本周完成公开 GUI 数据处理、基础 Agent 框架和模型调用接口。Kaggle 已完成三种数据集的全量预处理，DeepSeek API 也生成了一份六步任务计划。第三周代码、测试和运行说明已整理。", 11, False),
        2: ("一 本周任务完成情况", 12, True),
        3: ("1. 整理 WebArena、ScreenAgent 和 Mind2Web 的字段，将任务指令、环境、动作步骤和评估条件转成统一 JSONL 格式。", 11, False),
        4: ("2. 先在本地检查 814 条样例，再到 Kaggle 处理完整数据。最终读取 3,821 条记录，全部通过检查；划分为 3,434 条训练数据和 387 条验证数据。", 11, False),
        5: ("3. 使用 LangChain 串联任务输入、提示词、模型输出和计划解析，完成当前步骤选择、成功推进、失败重试及反馈历史记录。", 11, False),
        6: ("4. 完成模拟模型、OpenAI 兼容 API 和 Ollama 接口。DeepSeek API 实测成功，生成六步搜索计划；三种数据集各运行一条离线轨迹。第三周 39 项单元测试全部通过。", 11, False),
        7: ("二 是否达到预期", 12, True),
        8: ("第三周要求的数据预处理脚本和基础 Agent 框架已经完成。数据格式、批量检查、任务规划、模型调用和反馈记录可以分别运行，也可以连成离线流程。DeepSeek 的实际接口已验证，结果文件保存正常。", 11, False),
        9: ("Kaggle 已完成 WebArena 812 条、ScreenAgent 2,000 条和 Mind2Web 1,009 条数据的处理。全量数据要求已经达到。本机没有安装 Ollama；三条数据集轨迹使用模拟反馈，不能视为真实桌面任务成功。", 11, False),
        10: ("三 下周工作计划", 12, True),
        11: ("1. 连接截图、OCR、坐标定位、鼠标键盘控制和 Agent 规划模块，先在安全的本地界面完成集成。", 11, False),
        12: ("2. 实现“用户指令、屏幕感知、任务规划、动作执行、结果反馈”的端到端闭环，并保留每一步截图和日志。", 11, False),
        13: ("3. 开发简单命令行入口，可以输入任务、选择模型并查看每一步状态，不增加复杂代码结构。", 11, False),
        14: ("4. 测试打开浏览器、搜索内容、打开文件、发送消息和关闭应用五类任务。发送消息先使用草稿或模拟环境，真实发送前由本人确认。", 11, False),
        16: ("四 实际运行结果截图", 12, True),
        17: ("以下图片由第三周保存的运行日志和结果文件排版生成，文字内容与实际记录一致。", 11, False),
        19: ("图1 数据处理与测试结果。Kaggle 共读取 3,821 条记录，全部有效，训练集 3,434 条，验证集 387 条；39 项单元测试全部通过。", 10, False),
        21: ("图2 模型与闭环结果。DeepSeek API 为搜索任务生成六步计划并记录六条反馈；三种数据集样例完成 3 条离线轨迹，真实桌面操作为 0 次。", 10, False),
        22: ("证据目录：reports/week3；结果目录：output/week3", 10, False),
    }
    for index, (value, size, bold) in content.items():
        set_text(paragraphs[index], value, size, bold)
    set_picture(
        paragraphs[18],
        ROOT / "output/week3/screenshots/data_and_tests.png",
        6.0,
        "第三周全量数据处理和39项单元测试运行结果",
    )
    set_picture(
        paragraphs[20],
        ROOT / "output/week3/screenshots/agent_and_api.png",
        6.0,
        "DeepSeek API任务规划和三种数据集离线闭环结果",
    )
    doc.core_properties.title = "第三周项目周报"
    doc.core_properties.subject = "GUI 数据处理与基础 Agent 项目进度"
    doc.save(WEEKLY_OUTPUT)


def build_acceptance():
    shutil.copyfile(ACCEPTANCE_TEMPLATE, ACCEPTANCE_OUTPUT)
    doc = Document(ACCEPTANCE_OUTPUT)
    paragraphs = doc.paragraphs
    content = {
        0: ("第三周数据处理与基础 Agent 验收测试报告", 18, True),
        1: ("第三周要求的两项交付物已经完成：公开 GUI 数据预处理脚本和基础 Agent 框架代码。39 项单元测试全部通过，DeepSeek API 实际规划成功，三种数据集也已在 Kaggle 完成全量处理。", 11, False),
        2: ("一 对照第三周任务", 12, True),
        3: ("数据处理：支持 WebArena、ScreenAgent、Mind2Web 三种来源，统一输出任务编号、指令、环境、步骤和评估信息。", 11, False),
        4: ("批量流程：逐行检查 JSONL，记录缺失字段、非法步骤和重复任务，使用稳定规则划分训练集与验证集，并输出数据来源和动作统计。", 11, False),
        5: ("Agent 框架：使用 LangChain 连接任务输入、提示词、模型规划和状态解析，支持步骤选择、反馈记录、失败重试及完成判断。", 11, False),
        6: ("模型接口：支持模拟模型、OpenAI 兼容 API 和本地 Ollama 接口。文字和图片均有输入入口，DeepSeek API 已完成一次实际调用。", 11, False),
        7: ("二 自动测试和实测结果", 12, True),
        8: ("单元测试共 39 项，通过 39 项，失败 0 项，跳过 0 项。覆盖三种数据格式转换、批量校验、固定划分、Agent 状态、模型请求和数据闭环。测试运行耗时 0.238 秒。", 11, False),
        9: ("Kaggle 实测读取 3,821 条记录，其中 WebArena 812 条、ScreenAgent 2,000 条、Mind2Web 1,009 条；全部通过检查，划分得到训练集 3,434 条和验证集 387 条。", 11, False),
        10: ("模型实测使用 DeepSeek API 处理“打开浏览器并搜索 GUI Agent”，返回六步计划并保存六条模拟反馈。三种数据集各取一条任务完成离线轨迹，共 3 条，真实桌面操作为 0 次。", 11, False),
        11: ("三 问题与验收边界", 12, True),
        12: ("完整数据已在 Kaggle 处理，但本机仍未安装 Ollama。DeepSeek 只验证了文字任务规划，尚未验证截图理解。状态为 done 表示模拟反馈结束，不代表网页或桌面任务真实完成。", 11, False),
        13: ("四 提交材料与复现", 12, True),
        14: ("提交第三周验收代码包、周报和本报告。代码包包含数据脚本、Agent、模型接口、离线闭环、测试、运行说明和日志；不包含公开数据集原文件、模型权重或 API Key。复现步骤见 WEEK3_README.md。", 11, False),
        16: ("五 各模块测试用例与结果", 12, True),
        17: ("统计依据为本周保存的测试日志。每个 test 方法算 1 项，共 39 项；全部通过，失败 0 项，跳过 0 项。实际 API 和数据运行单独记录，不重复计入单元测试数量。", 10, False),
        18: ("六 一个完整用例说明", 12, True),
        19: ("案例：DeepSeek API 任务规划。输入任务“打开浏览器并搜索 GUI Agent”，使用 deepseek-flash 和官方 API 地址生成操作计划。", 10, False),
        20: ("预期：模型返回 1 至 8 个非空步骤，程序能够逐步记录模拟反馈，最终状态为 done。实际：模型返回 6 个步骤，完成 6 次状态更新并保存结果，符合预期。", 10, False),
        21: ("这个案例验证了实际 API、计划解析和状态记录。程序没有执行鼠标或键盘动作，因此不能把本次结果记为真实 GUI 任务成功。", 10, False),
        22: ("测试日志：reports/week3/unittest.txt\n全量统计：reports/week3/kaggle_full_summary.txt\nAPI结果：output/week3/deepseek_demo.json", 9, False),
    }
    for index, (value, size, bold) in content.items():
        set_text(paragraphs[index], value, size, bold)

    rows = [
        ("测试模块", "用例如何设计", "代表案例与预期结果", "测试数", "通过数"),
        ("数据标准化", "构造三种原始记录，检查自动识别、统一字段、错误输入、大字段删除和 ScreenAgent 编号唯一性。", "同一 session 的多个 ScreenAgent 文件使用不同任务编号，避免全量处理时重复。", "11", "11"),
        ("批量处理", "检查字段缺失、步骤编号、重复任务、固定划分和统计文件。", "相同 task_id 重复出现时记录错误；同一任务重复运行时分组一致。", "5", "5"),
        ("Agent 状态", "检查提示词、JSON 计划、当前步骤、成功推进、失败重试和完成状态。", "当前步骤失败后标为 retry，步骤序号不前进；成功后才进入下一步。", "9", "9"),
        ("模型接口", "模拟 API 和 Ollama 响应，检查图片编码、鉴权、地址、代理绕过和异常。", "DeepSeek 官方地址绕过错误代理；没有读取到 Key 时给出明确提示。", "9", "9"),
        ("数据闭环", "读取统一 JSONL，检查数量限制、坏数据、结果保存和离线完成状态。", "三种数据各取一条，共 3 条轨迹全部 done，真实桌面操作为 0。", "5", "5"),
        ("实际运行", "在 Kaggle 运行三种完整数据，并运行 DeepSeek 规划和离线闭环。", "3,821 条数据全部有效；DeepSeek 生成 6 步。此项不计入单元测试。", "-", "-"),
        ("合计", "按 test 方法统计", "失败 0 项；跳过 0 项", "39", "39"),
    ]
    table = doc.tables[0]
    if len(table.rows) != len(rows) or len(table.columns) != 5:
        raise RuntimeError("第二周验收报告表格结构发生变化")
    for row_index, values in enumerate(rows):
        for col_index, value in enumerate(values):
            set_cell(
                table.rows[row_index].cells[col_index],
                value,
                size=9.2,
                bold=row_index == 0,
                centered=col_index >= 3,
            )
    doc.core_properties.title = "第三周数据处理与基础 Agent 验收测试报告"
    doc.core_properties.subject = "第三周交付物与测试结果"
    doc.save(ACCEPTANCE_OUTPUT)


def verify_inputs():
    log = (ROOT / "reports/week3/unittest.txt").read_text(encoding="utf-8")
    if not re.search(r"Ran 39 tests", log) or "OK" not in log:
        raise RuntimeError("第三周测试日志不完整")
    stats = (ROOT / "reports/week3/kaggle_full_summary.txt").read_text(encoding="utf-8")
    if "Total records: 3821" not in stats or "Valid records: 3821" not in stats or "Invalid records: 0" not in stats:
        raise RuntimeError("第三周数据统计与报告不一致")
    deepseek = json.loads((ROOT / "output/week3/deepseek_demo.json").read_text(encoding="utf-8"))
    if deepseek["model_name"] != "api" or deepseek["status"] != "done" or len(deepseek["steps"]) != 6:
        raise RuntimeError("DeepSeek 实测结果与报告不一致")


def main():
    verify_inputs()
    build_weekly()
    build_acceptance()
    print(WEEKLY_OUTPUT)
    print(ACCEPTANCE_OUTPUT)


if __name__ == "__main__":
    main()
