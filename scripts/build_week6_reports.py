"""生成第六周分开的周报与验收报告，复用已验证的报告版式。"""
import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from build_week5_reports import (
    configure_document, add_title, add_heading, add_body, add_bullet,
    add_table as base_add_table, add_image, set_run_font,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/docx"
EVIDENCE = "output/week6/e2e/frontend_observability_20261002.json"
FINAL_IMAGE = ROOT / "output/week6/capture_probe/week5_probe_20261002_022345_321016.png"
CAPTURE_IMAGE = ROOT / "output/week6/capture_probe/week5_probe_20261002_022015_693376.png"


def add_table(doc, headers, rows, widths):
    table = base_add_table(doc, headers, rows, widths)
    for column, width in zip(table.columns, widths):
        column.width = Inches(width)
    for row in table.rows:
        for index, cell in enumerate(row.cells):
            if headers[index] in {"用例数", "结果", "结论"}:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    return table


def new_doc(title):
    doc = Document()
    configure_document(doc)
    doc.styles["Normal"].paragraph_format.line_spacing = Pt(16)
    doc.styles["Normal"].paragraph_format.space_after = Pt(6)
    add_title(doc, title, "GUI Agent 项目  2026年10月2日  macOS 本地验收")
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
        header = OxmlElement("w:tblHeader")
        table.rows[0]._tr.get_or_add_trPr().append(header)
        for row in table.rows:
            row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_after = Pt(3)
                    paragraph.paragraph_format.line_spacing = Pt(14)
    for shape in doc.inline_shapes:
        shape._inline.docPr.set("descr", "第六周本地前端真实运行截图")
    footer = doc.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / filename
    doc.save(target)
    return target


def make_weekly(summary):
    doc = new_doc("第六周项目周报")
    add_body(doc, "本周完成控制台前端的接口记录、连接异常提示和截图状态展示，并修复健康检查覆盖任务最终状态的问题。真实前端操作已验证预览成功、实时模式拒绝和本地执行器断开。全量自动回归 120/120 通过。")
    add_heading(doc, "一 本周任务完成情况")
    add_table(doc, ["任务", "本周结果", "验证方式"], [
        ["接口结果展示", "新增最近接口栏，显示方法、路径、HTTP 状态码和任务 ID", "页面提交与轮询"],
        ["连接异常反馈", "断开时显示未连接、网络错误和不可达提示", "停止服务后页面操作"],
        ["截图结果展示", "新增未收到、加载中、成功和失败文案；成功分支实测通过", "真实任务截图回填"],
        ["最终状态保留", "健康检查后仍显示动作方案已生成", "任务结束后观察页面"],
        ["回归与布局检查", "120 项通过；桌面中文和控件检查通过", "自动测试及桌面实查"],
    ], widths=[1.25, 3.9, 1.85])
    add_heading(doc, "二 是否达到预期")
    add_body(doc, "核心目标达到预期。最终复验任务 060c04b24f91 由前端点击开始，后端返回 POST 202，前端通过 GET 200 轮询结果，显示预览完成、101 项 OCR、安全检查通过和截图已加载。实时模式提交返回 403，页面显示拒绝原因；预览与拒绝任务均未执行鼠标键盘动作。")
    add_body(doc, "本周修改文件为 gui-agent-console/dist/index.html，并更新 tests/test_local_bridge.py 中的页面结构断言。本次验收针对本地页面；云端页面尚未发布本周改动。窄屏只检查了媒体规则，超时和截图加载失败分支尚未现场验证。")
    add_heading(doc, "三 下周工作计划")
    add_bullet(doc, "补充可重复运行的前端自动化，保存接口响应、最终页面状态和截图。")
    add_bullet(doc, "实测窄屏布局，并覆盖请求超时、截图失败和断开后的恢复流程。")
    add_bullet(doc, "完善提交拒绝后的进度展示，检查新任务与旧任务结果的显示关系。")
    add_body(doc, "无需 Kaggle 运行。本周没有模型训练或 GPU 推理任务。")
    doc.add_page_break()
    add_heading(doc, "四 实际运行结果截图与记录")
    add_body(doc, "图 1 为本周保存的项目 MSS 截图，任务编号 65f9cc4933d3。顶部保留动作方案已生成，下方显示 GET 200、99 项 OCR、安全检查通过及截图已加载。截图尺寸为 1470 × 956，坐标比例 1:1。")
    add_image(doc, FINAL_IMAGE, "图 1 第六周任务最终状态与接口记录", width=6.9)
    add_body(doc, "原图：output/week6/capture_probe/week5_probe_20261002_022345_321016.png。该截图对应状态保留测试，最终复验任务 060c04b24f91 的 OCR 为 101 项，两次任务分别记录。")
    add_heading(doc, "五 提交材料")
    add_body(doc, "周报与验收测试报告分开提供。端到端记录位于 " + EVIDENCE + "，最终复验事件日志位于 output/local_bridge/060c04b24f91/events.jsonl。自动回归原始日志及按模块数量见 output/week6/verification/。")
    add_body(doc, "最终回归：" + summary["checked_at"] + "，120 项执行，失败 0 项，错误 0 项，跳过 0 项。")
    return finalize(doc, "第六周周报.docx")


def make_acceptance(summary):
    doc = new_doc("第六周验收测试报告")
    add_body(doc, "本报告记录第六周控制台前端改动的本地验收。自动回归 120/120 通过；真实前端成功和 403 拒绝路径通过，断开提示、截图回填及最终状态保留均有页面实测记录。尚未实测的分支在验收边界中列明。")
    add_heading(doc, "一 对照第六周任务")
    add_table(doc, ["要求", "实际结果", "结论"], [
        ["显示接口与状态码", "成功显示 GET 200；拒绝显示 POST 403", "通过"],
        ["显示任务结果", "任务 ID、最终状态、OCR 数量和截图回填", "通过"],
        ["保留安全边界", "默认仅预览，实时未启用时后端拒绝", "通过"],
        ["真实前端端到端", "页面触发后端处理，再回到页面显示", "通过"],
        ["回归与界面检查", "120 项通过；桌面实查与窄屏规则静查", "按范围通过"],
    ], widths=[1.7, 4.25, 1.05])
    add_heading(doc, "二 自动测试与模块用例结果")
    add_body(doc, "最终报告回归执行时间：" + summary["checked_at"] + "。结果为 120 项通过、0 项失败、0 项错误、0 项跳过。详细用例名称与结果保存在 output/week6/verification/regression.log，模块数量保存在 regression_summary.json。")
    add_table(doc, ["模块范围", "用例数", "代表性检查", "结果"], [
        ["基础模块与演示", "37", "截图、OCR 坐标、点击守卫、拖拽释放", "通过"],
        ["本地桥接服务", "5", "页面返回、来源限制、预览任务接口", "通过"],
        ["第三周 Agent 与数据", "54", "数据规范、模型请求、重试与完成条件", "通过"],
        ["第四周实时循环", "22", "观察规划、动作上限、预览不执行", "通过"],
        ["第五周采集探针", "2", "截图成功保存与失败摘要", "通过"],
    ], widths=[1.8, 0.7, 3.6, 0.9])
    add_body(doc, "上述自动测试包含模拟执行器及后端直测。页面结构断言验证新增元素和文案是否被返回；实际浏览器交互结果另列端到端测试，未并入 120 项自动测试数量。")
    doc.add_page_break()
    add_heading(doc, "三 端到端测试")
    add_body(doc, "以下用例通过本地浏览器页面填写任务和点击控件触发。成功链路为 taskForm 提交 POST /api/tasks，页面轮询 GET /api/tasks/:id，再回填结果及加载 screenshot_url。后端函数、urllib 与 curl 直调未用于替代这些页面测试。")
    add_table(doc, ["用例", "前端触发与后端结果", "页面核对结果", "结论"], [
        ["最终预览成功", "输入搜索 GUI Agent 并点击开始；POST 202，GET 200", "060c04b24f91；预览完成；101 项 OCR；截图已加载", "通过"],
        ["实时模式拒绝", "切换实时并提交点击 编辑；POST 返回 403", "显示仅允许预览及启用实时的提示", "通过"],
        ["本地服务断开", "页面连接后停止服务，再点击开始；请求失败", "未连接；GET /api/health 网络错误；不可达", "通过"],
        ["截图回填", "任务 486671f340e8 返回截图地址；浏览器加载图片", "截图已加载；101 项 OCR；安全检查通过", "通过"],
        ["最终状态保留", "任务 65f9cc4933d3 结束后等待健康检查", "保持动作方案已生成；任务接口 GET 200", "通过"],
    ], widths=[1.1, 2.6, 2.4, 0.9])
    add_body(doc, "原始端到端记录：" + EVIDENCE + "。任务截图及 OCR 数据保存在 output/local_bridge/ 对应任务目录。断开场景没有后端响应，因此作为连接异常前端测试；成功和拒绝路径负责验证完整接口往返。")
    add_heading(doc, "四 一个完整用例说明")
    add_body(doc, "输入为搜索 GUI Agent，模式为预览。点击开始任务后，后端创建任务 060c04b24f91 并返回 202。页面轮询返回 200，任务完成为 preview_ready。页面实际显示动作方案已生成、预览完成、101 项 OCR、安全检查通过，以及截图已加载提示。")
    add_body(doc, "后端事件日志记录 loop_started、observation_ready 和 action_proposed。动作方案为 type_text，文本 GUI Agent；预览只生成方案，未执行键盘输入，也未完成真实浏览器搜索。测试断言为页面结果与后端记录一致，判定通过。")
    doc.add_page_break()
    add_heading(doc, "五 运行截图与状态保留验证")
    add_body(doc, "图 1 对应任务 65f9cc4933d3，显示 99 项 OCR；它用于验证最终状态在健康检查后仍保留，与最终复验任务的 101 项 OCR 分开记录。")
    add_image(doc, FINAL_IMAGE, "图 1 任务完成后的前端状态和接口证据", width=6.9)
    add_heading(doc, "六 问题与验收边界")
    add_bullet(doc, "本周验收对象为本地页面 http://127.0.0.1:8765/，云端版本尚未发布本周改动。实时执行默认关闭，本周没有实时鼠标键盘执行测试。")
    add_bullet(doc, "网络断开提示已实测；请求超时和截图加载失败只完成代码及文案检查，尚未做故障注入实测。")
    add_bullet(doc, "桌面中文和控件布局已目视检查。窄屏仅检查媒体规则存在，尚未完成实际窄屏浏览器验收。")
    add_bullet(doc, "拒绝提交后的进度列表仍可能显示等待或进行中；完整失败状态展示及断开后的恢复留待补测。")
    add_body(doc, "无需 Kaggle 运行。本周无模型训练或 GPU 推理任务。")
    doc.add_page_break()
    add_heading(doc, "七 截图回填运行证据")
    add_image(doc, CAPTURE_IMAGE, "图 2 任务 486671f340e8 的截图加载成功状态", width=6.9)
    add_body(doc, "原图：output/week6/capture_probe/week5_probe_20261002_022015_693376.png。页面显示截图已加载、101 项 OCR 和安全检查通过；截图本身保留了当时顶部状态尚未修复的界面，图 1 展示修复后的结果。")
    add_heading(doc, "八 提交材料与复现")
    add_body(doc, "项目根目录：/Users/ziang/Documents/ChatGPT/New project。前端源码为 gui-agent-console/dist/index.html；测试断言为 tests/test_local_bridge.py；计划为 WEEK6_PLAN.md。端到端 JSON、PNG、OCR 和 events.jsonl 按本报告路径保留。")
    add_body(doc, '启动本地服务：\n"/Users/ziang/Documents/ChatGPT/New project/.venv/bin/python" -m src.local_bridge --port 8765')
    add_body(doc, "在项目根目录执行启动命令，打开 http://127.0.0.1:8765/，选择预览，输入搜索 GUI Agent 并点击开始。完成后核对任务 ID、GET 200、OCR、截图及最终状态；切换实时提交一次，核对 403 与拒绝提示。")
    add_body(doc, '保存回归证据：\n"/Users/ziang/Documents/ChatGPT/New project/.venv/bin/python" scripts/record_week6_regression.py')
    return finalize(doc, "第六周验收测试报告.docx")


if __name__ == "__main__":
    summary = json.loads((ROOT / "output/week6/verification/regression_summary.json").read_text(encoding="utf-8"))
    if not summary["passed"] or summary["tests_run"] != 120:
        raise SystemExit("最终回归结果与报告预期不一致")
    for image in (FINAL_IMAGE, CAPTURE_IMAGE):
        if not image.is_file():
            raise SystemExit(f"运行截图不存在：{image}")
    for target in (make_weekly(summary), make_acceptance(summary)):
        print(target)
