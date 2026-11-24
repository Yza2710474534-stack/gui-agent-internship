"""Build separate Week 7 weekly and acceptance reports from saved evidence."""

import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

from build_week5_reports import (
    add_body, add_bullet, add_heading, add_image, add_title, configure_document,
    set_run_font,
)
from build_week6_reports import add_table
from revise_week5_test_classification import MODULES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/docx"
BROWSER = ROOT / "output/week7/browser_e2e"
EVIDENCE = BROWSER / "results.json"
REGRESSION = ROOT / "output/week7/verification/regression_summary.json"


def new_doc(title):
    doc = Document()
    configure_document(doc)
    doc.styles["Normal"].paragraph_format.line_spacing = Pt(16)
    doc.styles["Normal"].paragraph_format.space_after = Pt(6)
    add_title(doc, title, "GUI Agent 项目  2026年10月9日  macOS 本地验收")
    for run in doc.paragraphs[-1].runs:
        set_run_font(run, 10.5)
    return doc


def finalize(doc, filename):
    for root in (doc._element, doc.styles.element):
        for border in list(root.iter(qn("w:pBdr"))):
            border.getparent().remove(border)
    for paragraph in doc.paragraphs:
        if paragraph._p.xpath(".//w:drawing"):
            paragraph.paragraph_format.line_spacing = 1.0
            paragraph.paragraph_format.keep_with_next = True
    for table in doc.tables:
        table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
        for row in table.rows:
            row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_after = Pt(3)
                    paragraph.paragraph_format.line_spacing = Pt(14)
    for shape in doc.inline_shapes:
        shape._inline.docPr.set("descr", "第七周真实浏览器端到端运行页面截图")
    footer = doc.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / filename
    doc.save(target)
    return target


def case_map(browser):
    return {case["id"]: case for case in browser["cases"]}


def make_weekly(regression, browser):
    cases = case_map(browser)
    doc = new_doc("第七周项目周报")
    add_body(doc, "本周补齐了第六周留下的浏览器验收。页面实际触发了本地预览、403 拒绝、请求超时、截图加载失败和服务断开；修正了失败后仍显示进行中与旧日志的问题。六种浏览器宽度均完成布局测量，320 像素下完成一次预览任务。自动回归 120 项全部通过。")
    add_heading(doc, "一 本周任务完成情况")
    add_table(doc, ["任务", "完成结果", "证据"], [
        ["浏览器端到端", "真实页面提交预览，后端 POST 202、GET 200、截图 200，页面显示预览完成", "results.json 与截图"],
        ["安全拒绝", "页面切换实时提交，后端 403，页面显示拒绝及未执行", "results.json 与截图"],
        ["故障注入", "POST 延迟超过 8 秒、截图请求返回 404、真实服务停止；均显示对应提示", "三张故障截图"],
        ["故障恢复", "超时后重试、截图重新加载、服务重启后重新提交均通过", "results.json"],
        ["响应式验收", "320、375、680、768、980、1280 像素无横向溢出；修复移动端卡片宽度", "宽度测量和 PNG"],
    ], widths=[1.2, 4.45, 1.35])
    add_heading(doc, "二 是否达到预期")
    success = cases["preview_success"]
    add_body(doc, f"达到本周目标。最终成功用例任务 {success['task_id']} 由 Chrome 页面点击开始，后端创建并处理预览，页面通过轮询显示“动作方案已生成”、{success['ocr']} OCR 和截图已加载。403 拒绝、超时、截图 404 与服务关闭后的页面状态均由浏览器检查。自动测试 120/120 通过，失败和跳过均为 0。")
    add_body(doc, "本周改动在 gui-agent-console/dist/index.html；新增可重复运行的 scripts/run_week7_browser_e2e.mjs。浏览器使用本机真实桥接服务和项目 OCR 读取屏幕；超时与图片 404 在浏览器网络层注入。实时模式保持关闭，未执行鼠标或键盘，也未完成真实浏览器搜索。")
    add_heading(doc, "三 下周工作计划")
    add_bullet(doc, "把浏览器端到端脚本接入固定回归流程，继续保留原始请求和页面截图。")
    add_bullet(doc, "覆盖正在运行时服务断线、任务轮询超时和截图长期不可用的恢复操作。")
    add_bullet(doc, "继续检查 320 像素页面的导航遮挡和长文案可读性。")
    add_body(doc, "无需 Kaggle 运行。本周没有模型训练或 GPU 推理任务。")
    doc.add_page_break()
    add_heading(doc, "四 实际运行结果截图")
    add_body(doc, f"图 1 为任务 {success['task_id']} 的真实浏览器页面。最近接口显示 GET 200，页面显示 {success['ocr']} OCR、安全检查通过和截图已加载。")
    add_image(doc, BROWSER / "01_preview_success_1280.png", "图 1 预览任务完成后的页面和后端结果", width=6.8)
    add_heading(doc, "五 提交材料")
    add_body(doc, "两份报告单独交付。浏览器结果及各张截图位于 output/week7/browser_e2e/；全量回归日志和模块数量位于 output/week7/verification/。本地前端修改尚未发布至云端。")
    add_body(doc, "回归时间：" + regression["checked_at"] + "；120 项通过。")
    return finalize(doc, "第七周周报.docx")


def make_acceptance(regression, browser):
    cases = case_map(browser)
    doc = new_doc("第七周验收测试报告")
    add_body(doc, "本报告按模块和测试类型记录第七周验收。自动回归 120/120 通过；真实 Chrome 页面完成预览和 403 拒绝闭环；超时、截图 404、服务断开及恢复由运行中的浏览器触发。六种视口均无横向溢出，最窄 320 像素完成实际任务提交。")
    add_heading(doc, "一 对照本周任务")
    add_table(doc, ["验收项", "实际结果", "结论"], [
        ["真实前端端到端", "页面操作 → POST 202 → GET 200 → 页面预览完成并加载截图", "通过"],
        ["安全拒绝", "实时模式提交返回 403，页面显示未执行", "通过"],
        ["故障注入", "POST 超时、截图 404、停止服务均触发预期页面状态", "通过"],
        ["恢复", "超时重试、截图重载和服务重启后的任务提交成功", "通过"],
        ["窄屏", "六种视口无横向溢出，320 像素成功提交预览", "通过"],
    ], widths=[1.55, 4.65, 0.8])
    add_heading(doc, "二 自动测试模块分类")
    add_body(doc, "自动回归执行时间：" + regression["checked_at"] + "。19 个模块分组互不重叠，合计 120 项；失败 0 项、错误 0 项、跳过 0 项。功能、安全、异常、边界属于检查类型；接口集成测试包含真实本地 HTTP，但使用模拟执行器。")
    auto_rows = []
    for name, layer, check, filename, cls, count in MODULES:
        auto_rows.append([name, layer, f"{check}\n{filename} · {cls}", str(count), "通过"])
    add_table(doc, ["模块", "测试类型", "检查内容与来源", "用例数", "结果"], auto_rows,
              widths=[1.0, 1.45, 3.35, 0.65, 0.55])
    add_body(doc, "全部自动用例的逐项结果见 output/week7/verification/regression.log。以下浏览器用例与自动回归分开统计，避免把浏览器现场执行和模拟测试相加。")
    add_heading(doc, "三 浏览器端到端和故障注入分类")
    rows = [
        ["任务提交与观察", "端到端 功能", "点击开始；POST 202、GET 200、截图 200；页面显示最终状态、OCR 和截图", "通过"],
        ["实时模式安全", "端到端 安全", "切换实时提交；POST 403；页面显示拒绝及未执行", "通过"],
        ["请求超时", "端到端 故障", "浏览器将 POST 延迟超过 8 秒；显示超时、停止进度，可再次提交", "通过"],
        ["截图加载", "端到端 故障", "任务成功后将图片 GET 注入 404；显示加载失败，恢复网络后重载成功", "通过"],
        ["服务断开", "端到端 故障", "页面连接后停止本地进程；POST 网络错误；显示未连接和未执行", "通过"],
        ["服务恢复", "端到端 恢复", "重启本地进程，页面重新连接并成功提交预览", "通过"],
        ["移动端提交", "端到端 兼容", "320 像素 Chrome 页面点击开始，后端返回任务并回填预览状态", "通过"],
    ]
    add_table(doc, ["模块或场景", "测试类型", "前端触发和实际结果", "结论"], rows,
              widths=[1.2, 1.25, 3.85, 0.7])
    add_body(doc, "前端使用 Google Chrome headless 与 Playwright。真实服务只监听 127.0.0.1:8765；预览调用项目 LocalExecutor、MSS 和 OCR。超时与截图 404 是浏览器网络层注入的失败响应；断线用例真实关闭了本地服务。截图故障不表示后端文件不存在。")
    add_heading(doc, "四 多宽度浏览器布局")
    width_rows = []
    for measurement in browser["widths"]:
        width = measurement["viewport"]
        width_rows.append([str(width), str(measurement["document"]),
                           "页面提交成功" if width == 320 else "核心控件均在视口内", "通过"])
    add_table(doc, ["视口像素", "页面宽度", "操作与控件检查", "结果"], width_rows,
              widths=[1.2, 1.2, 3.8, 0.8])
    add_body(doc, "六种宽度的 document 和 body 滚动宽度均未超过视口。移动端 320、375、680 像素的两列卡片均铺满可用工作区；320 像素实际提交任务成功。PNG 位于 output/week7/browser_e2e/width_*.png。")
    add_heading(doc, "五 运行截图与一个完整用例")
    success = cases["preview_success"]
    add_body(doc, f"完整用例：输入“搜索 GUI Agent”，选择预览并点击开始；后端创建任务 {success['task_id']}，POST 返回 202。页面轮询任务接口 GET 200，读取真实屏幕并得到 {success['ocr']} OCR；截图接口返回 200，页面显示动作方案已生成、截图已加载和安全检查通过。")
    add_body(doc, "预览仅生成 type_text 动作方案，未向浏览器实际输入搜索词；鼠标键盘未执行。图 1 展示成功状态。图 2 为图片请求注入 404 后的页面提示，后端任务本身仍成功。")
    add_image(doc, BROWSER / "01_preview_success_1280.png", "图 1 预览完成", width=3.35)
    add_image(doc, BROWSER / "03_screenshot_failure_1280.png", "图 2 截图加载失败", width=3.35)
    add_body(doc, "图 3 为 POST 注入超过 8 秒延迟后页面显示超时；图 4 为真实停止服务后的页面状态。两种故障下页面均停止显示进行中，安全状态为未执行。")
    add_image(doc, BROWSER / "04_request_timeout_1280.png", "图 3 请求超时", width=3.35)
    add_image(doc, BROWSER / "05_service_disconnected_1280.png", "图 4 服务断开", width=3.35)
    add_heading(doc, "六 问题和验收边界")
    add_bullet(doc, "本地前端改动仍未发布至云端；本报告只验收本地页面。")
    add_bullet(doc, "实时模式默认关闭，因此仅验证 403 安全拒绝和预览，未执行真实点击或输入。")
    add_bullet(doc, "超时和截图故障通过浏览器路由注入，未改写服务端文件。正在运行时的轮询断线尚未单独覆盖。")
    add_body(doc, "无需 Kaggle 运行，本周没有训练或 GPU 推理任务。")
    add_heading(doc, "七 提交材料与复现")
    add_body(doc, "原始结果和全部请求记录：output/week7/browser_e2e/results.json；浏览器脚本：scripts/run_week7_browser_e2e.mjs；自动回归：output/week7/verification/regression_summary.json 与 regression.log。")
    add_body(doc, '在项目根目录复现：\n"/Users/ziang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node" scripts/run_week7_browser_e2e.mjs')
    add_body(doc, '自动测试：\n"/Users/ziang/Documents/ChatGPT/New project/.venv/bin/python" scripts/record_week7_regression.py')
    add_heading(doc, "八 窄屏运行截图")
    add_body(doc, "图 5 为 320 像素页面完成预览后的全页截图，包含任务提交、预览完成、OCR 计数和图片回填。")
    add_image(doc, BROWSER / "width_320_preview_result.png", "图 5 320 像素浏览器预览完成状态；原图见 output/week7/browser_e2e/width_320_preview_result.png", width=1.1)
    return finalize(doc, "第七周验收测试报告.docx")


def main():
    regression = json.loads(REGRESSION.read_text(encoding="utf-8"))
    browser = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if not regression["passed"] or regression["tests_run"] != 120:
        raise SystemExit("自动回归未满足验收要求")
    if browser["result"] != "passed" or len(browser["cases"]) != 8 or len(browser["widths"]) != 6:
        raise SystemExit("浏览器验收结果未满足要求")
    if sum(row[5] for row in MODULES) != 120:
        raise SystemExit("模块分类数量错误")
    for target in (make_weekly(regression, browser), make_acceptance(regression, browser)):
        print(target)


if __name__ == "__main__":
    main()
