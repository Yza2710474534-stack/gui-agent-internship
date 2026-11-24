from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "docx"
OUT.mkdir(parents=True, exist_ok=True)

FRONTEND_IMAGE = ROOT / "output/week5/capture_probe/week5_probe_20260929_185729_902162.png"
SEARCH_IMAGE = ROOT / "output/week5/capture_probe/week5_probe_20260929_185433_602500.png"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_borders(cell, color="D9D9D9", size="6"):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def set_cell_margins(cell, top=100, start=120, bottom=100, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    margins = tc_pr.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn("w:" + side))
        if node is None:
            node = OxmlElement("w:" + side)
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_run_font(run, size=10.5, bold=False, color="000000"):
    run.font.name = "Arial Unicode MS"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Arial Unicode MS")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial Unicode MS")
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial Unicode MS")
    run.font.size = Pt(size)
    run.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)


def configure_document(doc):
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Arial Unicode MS"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Arial Unicode MS")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial Unicode MS")
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial Unicode MS")
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.15
    title = styles["Title"]
    title.font.name = "Arial Unicode MS"
    title._element.rPr.rFonts.set(qn("w:ascii"), "Arial Unicode MS")
    title._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial Unicode MS")
    title._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial Unicode MS")
    title.font.size = Pt(20)
    title.font.bold = True
    title.font.color.rgb = RGBColor(0, 0, 0)
    title.paragraph_format.space_after = Pt(8)
    for name in ("Heading 1", "Heading 2"):
        style = styles[name]
        style.font.name = "Arial Unicode MS"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Arial Unicode MS")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial Unicode MS")
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial Unicode MS")
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = True
        style.paragraph_format.space_before = Pt(10)
        style.paragraph_format.space_after = Pt(5)
    styles["Heading 1"].font.size = Pt(14)
    styles["Heading 2"].font.size = Pt(11.5)


def add_title(doc, title, subtitle):
    p = doc.add_paragraph(style="Title")
    p.add_run(title)
    p = doc.add_paragraph()
    r = p.add_run(subtitle)
    set_run_font(r, 10.5, color="444444")
    p.paragraph_format.space_after = Pt(12)


def add_heading(doc, text, level=1):
    doc.add_paragraph(text, style=f"Heading {level}")


def add_body(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    set_run_font(r)
    return p


def add_bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text)
    set_run_font(r)
    return p


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.autofit = False
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        if widths:
            cell.width = Inches(widths[i])
        set_cell_shading(cell, "1F4E78")
        set_cell_borders(cell)
        set_cell_margins(cell)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(header)
        set_run_font(r, 9.5, bold=True, color="FFFFFF")
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cell = cells[i]
            if widths:
                cell.width = Inches(widths[i])
            set_cell_shading(cell, "EEF4F8" if row_index % 2 else "FFFFFF")
            set_cell_borders(cell)
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            r = p.add_run(str(value))
            set_run_font(r, 9.3)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_image(doc, path, caption, width=6.6):
    if not path.is_file():
        add_body(doc, f"截图缺失：{path}")
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=Inches(width))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(caption)
    set_run_font(r, 9, color="444444")


def add_footer(doc, label):
    for section in doc.sections:
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = footer.add_run(label)
        set_run_font(r, 8.5, color="666666")


def make_weekly():
    doc = Document()
    configure_document(doc)
    add_title(doc, "第五周项目周报", "GUI Agent 项目　|　2026年9月29日　|　Mac 本地环境")
    add_body(doc, "本周完成真实屏幕采集证据恢复、OCR 复核、前端到后端端到端验证和一次限次浏览器搜索。第五周的验收重点已达到：前端页面能够触发本地接口，页面能显示后端处理结果，预览模式不执行鼠标键盘动作；真实搜索截图也由项目 OCR 和完成判断代码复核通过。")

    add_heading(doc, "一 本周任务完成情况")
    add_table(doc, ["任务", "完成情况", "原始证据"], [
        ["屏幕采集健康检查", "MSS 可用；1470 × 956；坐标比例 1:1；动作数 0", "output/week5/capture_probe/"],
        ["真实截图 OCR", "EasyOCR 成功读取截图并保存 JSON，坐标仍在原始图片空间", "output/ocr/ocr_20260929_185457_572028.json"],
        ["前端端到端成功", "页面提交 → POST 202 → GET 轮询 → 页面显示预览完成", "output/week5/e2e/frontend_bridge_20260929.json"],
        ["前端端到端拒绝", "实时模式由后端返回 403，页面显示仅允许预览", "同上记录中的 rejection_post"],
        ["真实浏览器搜索", "Chrome 搜索 GUI Agent，截图、OCR、完成判断均通过", "output/week5/live_browser/verification_20260929.json"],
    ], widths=[1.45, 3.15, 2.15])

    add_heading(doc, "二 是否达到预期")
    add_body(doc, "达到本周预期。项目 MSS 已能保存当前 Mac 屏幕，EasyOCR 能在同一截图上工作；gui-agent-console 的预览链路已经完成一次真实前端端到端闭环，并覆盖了实时模式被拒绝的安全边界。全量回归测试在允许本地临时端口绑定的环境中为 120/120 通过。")
    add_body(doc, "本周仍保留一个清晰边界：Chrome 搜索的实际导航由授权的 CUA 浏览器控制完成，项目本地桥接服务的实时模式仍默认关闭；本地桥接服务已验证预览闭环，但没有把未知焦点下的实时搜索误当作已支持功能。")

    add_heading(doc, "三 实际运行结果截图")
    add_body(doc, "以下截图均为本周运行时保存的 PNG，没有使用旧截图替代本周结果。")
    add_image(doc, FRONTEND_IMAGE, "图 1　前端端到端预览完成状态。任务内容为“搜索 GUI Agent”，页面显示预览完成、识别文字 68 项和安全检查通过。原图：output/week5/capture_probe/week5_probe_20260929_185729_902162.png。", 6.55)
    add_image(doc, SEARCH_IMAGE, "图 2　真实 Chrome 搜索完成状态。搜索框包含 GUI Agent，页面显示 GitHub Topics、AI 概览和多个搜索结果。原图：output/week5/capture_probe/week5_probe_20260929_185433_602500.png。", 6.55)

    add_heading(doc, "四 下周工作计划")
    add_bullet(doc, "把真实浏览器搜索从单独的授权浏览器控制步骤进一步收敛为可复现的项目运行器流程，并继续保留动作上限。")
    add_bullet(doc, "补充一个可重复执行的前端端到端自动化脚本，覆盖预览成功和实时模式拒绝。")
    add_bullet(doc, "继续补充失败重试、停止和多显示器边界证据。")
    add_bullet(doc, "本周无需 Kaggle 运行；下周只有在安排模型训练或 GPU 推理时才使用 Kaggle。")

    add_heading(doc, "五 提交材料")
    add_body(doc, "本周周报与验收测试报告分开提供。代码、测试和原始运行记录保留在项目目录；端到端接口记录、屏幕截图、OCR JSON 和浏览器完成判断均可按报告中的路径复核。")
    add_footer(doc, "第五周项目周报")
    path = OUT / "第五周周报.docx"
    doc.save(path)
    return path


def make_acceptance():
    doc = Document()
    configure_document(doc)
    add_title(doc, "第五周验收测试报告", "GUI Agent 项目　|　自动测试与真实运行验收　|　2026年9月29日")
    add_body(doc, "本报告按第二周递交标准单独记录第五周验收。验收结论为：自动测试 120/120 通过；项目 MSS、OCR 和真实搜索完成判断通过；前端到后端端到端成功与拒绝路径均通过。实时执行仍需显式启动参数，默认安全边界保持有效。")

    add_heading(doc, "一 对照第五周任务")
    add_table(doc, ["任务", "验收要求", "结果"], [
        ["屏幕采集", "保存截图、尺寸、坐标区域和比例", "通过"],
        ["OCR 观察", "读取真实截图并保留 OCR JSON", "通过"],
        ["前端闭环", "前端操作触发接口并回到页面显示结果", "通过"],
        ["安全边界", "预览不执行；实时未启用时拒绝", "通过"],
        ["真实搜索", "搜索框、结果标题、目标结果和多个结果存在", "通过"],
    ], widths=[1.35, 4.2, 1.2])

    add_heading(doc, "二 自动测试和实测结果")
    add_body(doc, "全量测试命令为 `python -m unittest discover -s tests -v`，结果为 120 项通过、0 项失败、0 项跳过。第一次在受限环境运行时，5 个 local bridge 测试因禁止绑定 127.0.0.1 临时端口而报权限错误；使用项目本机权限复跑后 5 项全部通过，因此不计为代码失败。")
    add_table(doc, ["范围", "数量", "结果", "说明"], [
        ["项目全量回归", "120", "通过", "包括旧模块、第四周专项测试和第五周采集探针测试"],
        ["第四周专项测试", "22", "通过", "观察、规划、实时循环和搜索完成判断"],
        ["第五周采集探针", "2", "通过", "成功保存与失败记录分支"],
        ["真实搜索完成判断", "1", "通过", "项目截图 + OCR + 完成条件"],
    ], widths=[1.7, 0.8, 1.0, 3.25])

    add_heading(doc, "三 端到端测试")
    add_body(doc, "端到端测试从 gui-agent-console 页面实际填写任务并点击开始，经过本地桥接服务接口，再回到同一页面核对状态和结果。直接调用 Python 函数、urllib 或 curl 未作为本节通过依据。")
    add_table(doc, ["用例", "前端触发", "后端响应", "页面结果", "结论"], [
        ["预览成功", "填写“搜索 GUI Agent”，选择预览并点击开始", "POST /api/tasks 返回 202；GET /api/tasks/3f12e224b945 返回 preview_ready", "显示预览完成、动作方案、120 项识别文字、安全检查通过", "通过"],
        ["实时拒绝", "同一页面切换实时并点击开始", "POST /api/tasks 返回 403，原因 live_disabled", "显示本地执行器当前仅允许预览，需 --enable-live", "通过"],
        ["报告截图复现", "再次从页面提交预览任务", "任务 f0c2550e9504；事件日志记录 loop_started、observation_ready、action_proposed", "显示预览完成、68 项识别文字、安全检查通过", "通过"],
    ], widths=[1.0, 1.7, 2.3, 2.0, 0.7])
    add_body(doc, "端到端原始记录：output/week5/e2e/frontend_bridge_20260929.json；复现截图记录：output/week5/e2e/frontend_bridge_replay_20260929.json；页面截图：output/week5/capture_probe/week5_probe_20260929_185729_902162.png。")

    add_heading(doc, "四 真实搜索测试")
    add_body(doc, "使用 Google Chrome 搜索 GUI Agent。无障碍树确认搜索框值为 GUI Agent、页面存在“搜索结果”标题、存在 GitHub Topics 结果，并能看到多个结果。项目随后用 MSS 保存 1470 × 956 截图，EasyOCR 读取并保存 JSON，自动完成判断返回 success=true。")
    add_body(doc, "原始记录：output/week5/live_browser/20260929_cua_result.json；完成判断：output/week5/live_browser/verification_20260929.json；OCR：output/ocr/ocr_20260929_185457_572028.json。")
    add_image(doc, SEARCH_IMAGE, "图 1　真实 Chrome 搜索截图及项目完成判断输入。", 6.55)

    add_heading(doc, "五 问题和验收边界")
    add_bullet(doc, "本地桥接服务默认只允许预览；实时模式返回 403 是预期安全行为。启用 --enable-live 后仍需遵守动作白名单和上限。")
    add_bullet(doc, "实时搜索的实际浏览器导航由授权的 CUA 控制完成；本地桥接服务不会在未知焦点下向浏览器输入搜索词。")
    add_bullet(doc, "OCR 仍可能产生低置信度误识别，报告只依据搜索框、浏览器和多个结果等组合条件判断完成。")
    add_bullet(doc, "本周未进行 Kaggle 运行，因为没有训练或 GPU 推理任务。")

    add_heading(doc, "六 提交材料与复现")
    add_table(doc, ["材料", "路径"], [
        ["本周计划和进度", "WEEK5_PLAN.md"],
        ["端到端成功与拒绝记录", "output/week5/e2e/frontend_bridge_20260929.json"],
        ["端到端页面截图记录", "output/week5/e2e/frontend_bridge_replay_20260929.json"],
        ["真实搜索记录", "output/week5/live_browser/20260929_cua_result.json"],
        ["截图和 OCR", "output/week5/capture_probe/；output/ocr/"],
    ], widths=[2.3, 4.4])
    add_body(doc, "复现顺序：先用项目虚拟环境启动本地 bridge；打开 http://127.0.0.1:8765/；在页面选择预览、填写搜索 GUI Agent 并点击开始；等待页面显示预览完成；再切换实时提交，核对 403 拒绝；最后运行全量 unittest。真实搜索截图的完成判断可用 scripts/verify_live_search.py 复核。")

    add_heading(doc, "七 一个完整用例说明")
    add_body(doc, "案例：前端预览任务。输入为“搜索 GUI Agent”，运行模式为预览。页面提交后后端创建任务并返回任务编号，前端持续读取任务状态；本次报告复现的任务编号为 f0c2550e9504。")
    add_body(doc, "预期：任务最终状态为 preview_ready，页面显示预览完成，且鼠标键盘动作数为 0。实际：事件日志保存了 loop_started、observation_ready 和 action_proposed，页面显示预览完成、识别文字 68 项和安全检查通过；截图保存在 output/week5/capture_probe/week5_probe_20260929_185729_902162.png，断言通过。")
    add_image(doc, FRONTEND_IMAGE, "图 2　完整用例的前端结果页面。", 6.55)
    add_footer(doc, "第五周验收测试报告")
    path = OUT / "第五周验收测试报告.docx"
    doc.save(path)
    return path


if __name__ == "__main__":
    for result in (make_weekly(), make_acceptance()):
        print(result)
