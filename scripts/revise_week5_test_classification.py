"""Add traceable module/type classifications without rebuilding the Week 5 report."""

import ast
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from build_week5_reports import add_body, add_heading, add_table, set_run_font

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "output/docx/第五周验收测试报告.docx"
TARGET = ROOT / "output/docx/第五周验收测试报告_修订版.docx"

# Each row represents a unique test class; no overlapping subtotal rows.
MODULES = [
    ("屏幕采集", "单元与文件集成\n功能 异常 边界", "显示器选择、缩放、截图序列、保存失败；采集后端模拟", "test_modules.py", "CaptureTests", 10),
    ("坐标换算", "单元\n边界", "分辨率、Retina 比例、负偏移、非法坐标；不操作桌面", "test_modules.py", "CoordinateTests", 3),
    ("OCR 处理", "单元\n功能 异常 边界", "坐标还原、低置信度分离、缺图与参数校验；识别器模拟", "test_modules.py", "OCRTests", 4),
    ("元素定位与可视化", "单元\n功能 异常", "构造图片的模板匹配、缩放与框选；非真实桌面识别", "test_modules.py", "ElementTests", 6),
    ("鼠标键盘控制", "单元\n功能 安全 异常", "点击、输入、滚动、拖拽中断释放；控制后端模拟", "test_modules.py", "ControllerTests", 10),
    ("演示与反馈判断", "单元\n功能 安全", "坐标偏移、歧义拒绝、图像变化与点击保护；构造证据", "test_demo.py", "DemoTests", 4),
    ("数据标准化", "单元与文件集成\n功能 异常", "三类数据字段、唯一 ID、JSONL 输出与坏数据；本地样本", "test_week3_dataset.py", "Week3DatasetTests", 11),
    ("批处理与划分", "单元与文件集成\n功能 异常", "字段校验、稳定划分、动作分类、统计与错误输出", "test_week3_batch.py", "Week3BatchTests", 5),
    ("模型接口适配", "单元\n接口契约 异常", "请求构造、图片编码、配置检查；模型及网络响应模拟", "test_week3_model.py", "Week3ModelTests", 9),
    ("任务规划与状态", "单元\n功能 异常 边界", "离线计划、JSON 校验、步数上限、成功推进与失败重试", "test_week3_agent.py", "Week3AgentTests", 9),
    ("长任务运行器", "单元与证据集成\n功能 异常 安全", "模拟动作的重试与上限、日志落盘、既有截图复核；非新现场运行", "test_week3_runtime.py", "Week3RuntimeTests", 10),
    ("任务场景目录", "单元与模拟集成\n功能 异常", "五类流程、多步骤、未知场景拒绝、模拟状态机运行", "test_week3_task_catalog.py", "Week3TaskCatalogTests", 5),
    ("轨迹离线演示", "单元与文件集成\n功能 异常 安全", "读取上限、坏记录、离线状态推进、摘要保存；无桌面动作", "test_week3_trajectory_demo.py", "Week3TrajectoryDemoTests", 5),
    ("屏幕观察管线", "单元与文件集成\n功能 异常", "图片与 OCR 落盘、尺寸对齐、状态转发；采集与 OCR 模拟", "test_week4_observation.py", "Week4ObservationTests", 3),
    ("实时动作规划", "单元\n接口契约 安全", "动作 JSON、白名单、额外字段拒绝、提示约束；模型模拟", "test_week4_planner.py", "Week4PlannerTests", 5),
    ("实时循环", "单元与模拟集成\n功能 安全 异常", "预览不执行、完成校验、重试、超时和动作上限；回调模拟", "test_week4_realtime.py", "Week4RealtimeTests", 10),
    ("搜索完成判断", "单元与证据集成\n功能 异常", "既有搜索证据、缺失文件、查询条件；不发起新浏览器搜索", "test_week4_search.py", "Week4SearchTests", 4),
    ("本地桥接接口", "单元与 HTTP 集成\n接口契约 安全", "真实本地 HTTP 的健康、页面、来源拒绝、任务轮询；执行器模拟", "test_local_bridge.py", "LocalBridgeTest", 5),
    ("第五周采集探针", "单元与文件集成\n功能 异常 安全", "成功摘要、采集失败记录、动作数 0；采集与保存模拟", "test_week5_capture_probe.py", "Week5CaptureProbeTests", 2),
]

REAL_CASES = [
    ("屏幕采集", "真实环境\n功能与冒烟", "MSS 保存 1470 × 956 截图，坐标比例 1:1，动作数 0", "capture_probe/result.json"),
    ("OCR 与完成判断", "真实环境集成\n功能", "真实截图 → EasyOCR → 完成条件；success=true", "live_browser/verification_20260929.json"),
    ("前端预览任务", "端到端\n功能", "页面开始 → POST 202 → GET 轮询 → 页面 preview_ready；任务 3f12e224b945", "e2e/frontend_bridge_20260929.json"),
    ("前端实时拒绝", "端到端\n安全与负向", "页面实时开始 → POST 403 live_disabled → 页面拒绝；未执行鼠标键盘", "e2e/frontend_bridge_20260929.json"),
    ("前端截图复现", "端到端\n功能与复现", "再次页面预览 → 任务 f0c2550e9504 → 页面预览完成、68 项 OCR 和截图", "e2e/frontend_bridge_replay_20260929.json"),
    ("Chrome 搜索", "真实环境系统\n功能", "授权 CUA 导航，查询 GUI Agent 并核对多个结果；非本地 bridge 实时执行", "live_browser/20260929_cua_result.json"),
]


def validate_counts():
    for _, _, _, filename, class_name, expected in MODULES:
        tree = ast.parse((ROOT / "tests" / filename).read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
        count = sum(isinstance(n, ast.FunctionDef) and n.name.startswith("test_") for n in cls.body)
        assert count == expected, (filename, class_name, count, expected)
    assert sum(row[5] for row in MODULES) == 120


def classification_table(doc, headers, rows, widths):
    table = add_table(doc, headers, rows, widths)
    for col, width in zip(table.columns, widths):
        col.width = Inches(width)
    table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    for row in table.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for i, cell in enumerate(row.cells):
            for p in cell.paragraphs:
                p.paragraph_format.line_spacing = 1.05
                p.paragraph_format.space_after = Pt(1)
                if i == len(headers) - 1 or (len(headers) == 5 and i == 3):
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return table


def main():
    validate_counts()
    doc = Document(SOURCE)
    original_images = len(doc.inline_shapes)
    original_paragraphs = [p.text for p in doc.paragraphs]
    heading = next(p for p in doc.paragraphs if p.text == "二 自动测试和实测结果")
    heading.text = "二 模块与测试类型分类"
    intro = next(p for p in doc.paragraphs if p.text.startswith("全量测试命令为"))
    intro.text = (
        "第五周全量回归记录为 120 项通过、0 项失败、0 项跳过。下表按模块列出测试层级、"
        "检查类型、依赖方式、来源与数量；本次仅修订分类，不产生新的测试结果。"
    )
    # Remove only the old overlapping aggregate table. Preserve all other content/images.
    old = doc.tables[1]._tbl
    old.getparent().remove(old)
    anchor = next(p for p in doc.paragraphs if p.text == "三 端到端测试")._p
    before = set(doc._element.body)
    add_body(doc, "分类修订日期为 2026年10月3日。单元测试检查局部逻辑；集成测试检查模块或接口连接；端到端测试必须由前端触发后端并回到页面。功能、安全、异常、边界属于检查类型；自动回归是执行范围，不单独计数。")
    add_heading(doc, "自动测试分类表", 2)
    add_body(doc, "共 19 个模块分组，互不重复，合计 120 项。第四周 22 项和第五周探针 2 项均包含在合计内。来源文件均位于 tests/；模拟依赖通过不代表真实设备或在线模型已通过。")
    rows = [
        [name, kind, f"{coverage}\n来源 {file} · {cls}", str(count), "通过"]
        for name, kind, coverage, file, cls, count in MODULES
    ]
    auto = classification_table(doc, ["模块", "测试类型", "检查内容与来源", "数量", "结果"], rows,
                                [1.05, 1.45, 3.55, 0.45, 0.50])
    for row in auto.rows[1:]:
        p = row.cells[2].paragraphs[0]
        text = p.text
        coverage, source = text.split("\n来源 ", 1)
        p.clear()
        set_run_font(p.add_run(coverage), 9.3)
        set_run_font(p.add_run("\n来源 " + source), 8, color="444444")
    add_heading(doc, "端到端与真实环境测试分类表", 2)
    add_body(doc, "以下为第五周独立现场记录，不计入上述 120 项自动测试。多行可能复用同一次截图或运行证据，不能相加为独立执行次数。证据路径以 output/week5/ 为根目录。")
    classification_table(doc, ["模块或场景", "测试类型", "检查内容与证据", "结果"],
                         [[name, kind, f"{coverage}\n证据 {evidence}", "通过"]
                          for name, kind, coverage, evidence in REAL_CASES],
                         [1.1, 1.45, 3.9, 0.55])
    # Insert the added blocks at the original section-two location, not at the end.
    new_blocks = [el for el in list(doc._element.body) if el not in before and el.tag != qn("w:sectPr")]
    for el in new_blocks:
        anchor.addprevious(el)
    # Correct inherited title decoration and the old E2E table's page overflow.
    for style in doc.styles:
        for border in style.element.xpath(".//w:pBdr"):
            border.getparent().remove(border)
    for border in doc._element.body.xpath(".//w:pBdr"):
        border.getparent().remove(border)
    e2e = next(t for t in doc.tables if t.cell(0, 0).text == "用例")
    e2e_widths = [0.9, 1.45, 2.2, 1.9, 0.55]
    for col, width in zip(e2e.columns, e2e_widths):
        col.width = Inches(width)
    for row in e2e.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for cell, width in zip(row.cells, e2e_widths):
            cell.width = Inches(width)
    e2e.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    if hasattr(doc, "add_comment"):
        doc.add_comment(heading.runs[0], text="按修改建议补充模块与测试类型分类；保留第五周原有结果和运行截图。", author="项目报告修订")
    assert len(doc.inline_shapes) == original_images == 2
    retained = {p.text for p in doc.paragraphs}
    for text in original_paragraphs:
        if text and text not in {"二 自动测试和实测结果"} and not text.startswith("全量测试命令为"):
            assert text in retained, text
    doc.save(TARGET)
    print(f"{TARGET}\n模块分组 19；自动测试 120；现场分类 6；保留截图 2")


if __name__ == "__main__":
    main()
