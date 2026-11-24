"""Build Week 8 reports from verified evidence; reject incomplete acceptance data."""
import json
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from build_week5_reports import configure_document, add_title, add_body, add_heading, add_image, set_run_font
from build_week6_reports import add_table
from revise_week5_test_classification import MODULES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/docx'
WORK = ROOT / 'output/week8'
LIVE = WORK / 'live_e2e'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def page_field(doc):
    p = doc.sections[0].footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    f = OxmlElement('w:fldSimple'); f.set(qn('w:instr'), 'PAGE'); p._p.append(f)


def finish(doc, name):
    for root in (doc._element, doc.styles.element):
        for border in list(root.iter(qn('w:pBdr'))):
            border.getparent().remove(border)
    for p in doc.paragraphs:
        if p._p.xpath('.//w:drawing'):
            p.paragraph_format.line_spacing = 1
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.keep_with_next = True
    for table in doc.tables:
        table.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
        for row in table.rows:
            row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.first_line_indent = Pt(0)
                    p.paragraph_format.line_spacing = 1.1
                    p.paragraph_format.space_after = Pt(3)
    for s in doc.inline_shapes:
        s._inline.docPr.set('descr', '第八周实际浏览器运行证据，图注说明场景与状态')
    page_field(doc)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    doc.save(path)
    return path


def new_weekly(title):
    doc = Document(); configure_document(doc)
    doc.styles['Normal'].paragraph_format.line_spacing = Pt(16)
    add_title(doc, title, 'GUI Agent 项目  2026年10月16日  macOS 本地验收')
    return doc


def image(doc, filename, caption, width=6.6):
    add_image(doc, LIVE / filename, caption, width=width)


def page_heading(doc, text):
    p = doc.add_paragraph(text, style='Heading 1')
    p.paragraph_format.page_break_before = True


def weekly(auto, old, live, success):
    doc = new_weekly('第八周项目周报')
    add_body(doc, f"本周补齐真实实时成功闭环：前端提交任务后，项目MSS和EasyOCR定位目标，控制器实际点击一次，目标页出现VERIFIED，后端返回done，前端显示完成条件通过。自动回归{auto['tests_run']}项、既有浏览器{len(old['cases'])}个场景和新增专项{len(live['cases'])}个场景均通过。结项报告按论文结构完成，正文汉字超过8000字。")
    add_heading(doc, '一 本周任务完成情况')
    add_table(doc, ['任务', '完成结果', '证据'], [
        ['实时成功闭环', '实际点击1次；OCR与目标页均为VERIFIED；前端显示通过', success['task_id']],
        ['完成条件与安全边界', '增加明确结果文字核验；错误结果判失败；重复目标零动作停止', 'live_e2e/results.json'],
        ['运行中恢复', '轮询超时与断线恢复同一任务；截图持续不可用后手动恢复', '专项场景及页面截图'],
        ['固定回归与窄屏', f"自动{auto['tests_run']}项；浏览器8场景；6种宽度；320像素长文案实际提交", 'verification与browser_regression'],
        ['结项材料', '周报、验收报告及论文式结项报告分别交付；正文独立统计', 'output/docx'],
    ], widths=[1.05, 4.25, 1.7])
    add_heading(doc, '二 是否达到预期')
    add_body(doc, '达到本周受控单步实时验收目标。该成功路径由规则定位驱动，不使用大模型自主规划；目标为隔离测试页。未将403拒绝、模拟执行或历史搜索当作本周实时成功。测试中修复了多个轮询重叠导致旧响应覆盖恢复提示的竞态，并补齐超时与循环上限终态。')
    add_heading(doc, '三 结项后的工作建议')
    add_body(doc, '优先补充任务持久化、动作前焦点校验与阻塞调用取消；扩大独立任务集后再评估模型驱动多步任务。以上属于后续建议，不计入本周已完成功能。本周无需 Kaggle 运行。')
    page_heading(doc, '四 实际运行结果截图与记录')
    add_body(doc, f"任务{success['task_id']}，输入“点击 VERIFY，确认出现 VERIFIED”，耗时{success['duration_seconds']}秒，动作数1。图1为前端完成结果，图2为目标页面。")
    image(doc, '02_console_live_success.png', '图1 实时任务完成后 前端显示已确认出现VERIFIED', 6.1)
    image(doc, '03_target_after.png', '图2 项目控制器实际点击后的目标页 状态为VERIFIED', 4.7)
    return finish(doc, '第八周周报.docx')


def acceptance(auto, old, live, success):
    doc = new_weekly('第八周验收测试报告')
    add_body(doc, '本报告验收实时模式成功路径及第七周遗留的运行中恢复问题。真实桌面动作、浏览器网络故障注入、模拟依赖自动测试分别统计，所有结果均对应本周重新执行的记录。')
    add_heading(doc, '一 任务对照与结果口径')
    add_table(doc, ['验收项', '实际结果', '结论'], [
        ['实时成功', '前端POST 202；真实OCR定位及点击；任务done；页面显示VERIFIED', '通过'],
        ['错误结果与目标歧义', 'MISSING不出现则action_failed；两处VERIFY则stopped且零点击', '通过'],
        ['运行中故障恢复', '轮询超时与断线后查询同一任务；截图404撤去后重新加载', '通过'],
        ['浏览器及窄屏回归', '既有8场景与6种宽度；320像素长任务提交无横向溢出', '通过'],
        ['结项报告', '论文结构完整；第一至十章正文汉字独立计数超过8000字', '通过'],
    ], widths=[1.4, 5.1, .5])
    add_body(doc, f"自动回归{auto['tests_run']}项，失败{auto['failures']}，错误{auto['errors']}，跳过{auto['skipped']}；浏览器基线{len(old['cases'])}个场景；专项{len(live['cases'])}个场景。六种宽度属于检查维度，不与场景数相加。负向场景通过是指正确失败或停止，不能计为成功业务任务。")
    add_heading(doc, '二 测试环境与依赖')
    add_body(doc, '本机macOS，项目Python虚拟环境、MSS、EasyOCR、PyAutoGUI与Google Chrome；浏览器自动化使用捆绑Node和Playwright。实时目标页可见，控制台使用独立无头会话。首次受限会话无法检测屏幕，改用可访问桌面的执行环境后采集成功，尺寸1470×956、坐标比例1∶1。OCR模型复用本地权重，无需训练或下载新模型。')
    add_body(doc, '成功路径没有模拟执行器、没有替换截图或OCR结果、没有用浏览器脚本代点目标按钮；目标页面是本地受控测试页面，不代表任意网站或办公软件。')
    page_heading(doc, '三 自动测试模块与类型分类')
    rows = [[name, kind.replace('\n', ' '), coverage + '\n' + filename, str(count), '通过']
            for name, kind, coverage, filename, cls, count in MODULES]
    rows.append(['点击结果与终态', '单元与文件集成 功能 异常 边界',
                 '显式结果提取、精确匹配、坏证据拒绝、历史验证、无业务条件标注、终态释放\ntest_week8_verification.py', '6', '通过'])
    assert sum(int(row[3]) for row in rows) == auto['tests_run']
    add_body(doc, '下表每一行互不重复，共20组。证据为output/week8/verification/regression.log；测试文件位于tests。控制、模型、采集等依赖方式在检查内容中明确，不代表新现场动作。')
    add_table(doc, ['模块', '层级与类型', '检查内容与来源', '数量', '结果'], rows,
              widths=[1.0, 1.2, 3.9, .45, .45])
    page_heading(doc, '四 端到端测试与真实环境分类')
    labels = {
      'real_live_click_success': ('实时成功', '端到端及真实环境 功能', '实际MSS与OCR、项目控制器单次点击；OCR和DOM均为VERIFIED'),
      'completion_text_missing': ('结果不匹配', '端到端及真实环境 异常', '实际点击1次；预期MISSING未出现；后端action_failed'),
      'ambiguous_target_no_action': ('目标歧义', '端到端及真实环境 安全', '真实页面两处同名目标；stopped；实际动作0'),
      'active_task_poll_timeout_and_recovery': ('运行中轮询超时', '浏览器端到端 故障注入', 'GET延迟超过5秒；保留任务；恢复后读取同一任务'),
      'screenshot_unavailable_and_manual_recovery': ('截图持续不可用', '浏览器端到端 故障注入', '资源404直到撤去注入；点击重试截图后加载成功'),
      'active_poll_disconnect_and_recovery': ('运行中断线', '浏览器端到端 故障注入', '任务GET注入连接拒绝；后端继续；恢复同一任务'),
      'mobile_320_long_task': ('320像素长文案', '浏览器端到端 边界', '实际提交预览；控件在视口内；无横向溢出'),
    }
    add_table(doc, ['模块', '层级与类型', '用例与证据', '数量', '结果'], [
      [*labels[c['id']][:2], labels[c['id']][2] + '\n任务 ' + c.get('task_id', ''), '1', '通过'] for c in live['cases']
    ], widths=[1.15, 1.4, 3.5, .45, .5])
    add_body(doc, '专项原始来源为output/week8/live_e2e/results.json，包含真实HTTP请求及响应。前3项读取真实桌面；后续恢复故障在浏览器网络层注入，其后端没有实际崩溃。专项中实际桌面点击总计2次：成功案例1次，错误预期案例1次。歧义及预览恢复案例均不执行动作。')
    add_heading(doc, '五 既有浏览器场景回归')
    add_body(doc, '原有8场景本周重新执行并单独保存：预览成功、实时403拒绝、截图404、截图恢复、POST请求超时、超时重试、真实服务停止和重启恢复。前端实际提交、真实HTTP桥接和真实屏幕OCR参与运行。超时与图片404由网络层注入；服务停止则实际关闭后端进程。')
    add_body(doc, '320、375、680、768、980、1280像素均测量文档、表单及面板宽度；320像素实际完成预览。原始来源为output/week8/browser_regression/results.json。与专项的320像素长文案检查不同，不将宽度数重复计入场景数。')
    page_heading(doc, '六 一个完整实时用例')
    add_body(doc, f"前置：本地服务显式--enable-live；可见目标页READY；目标计数0。输入：点击 VERIFY，确认出现 VERIFIED。触发：控制台选择实时并点击开始任务。任务标识：{success['task_id']}。")
    add_body(doc, f"接口：POST /api/tasks返回202；GET /api/tasks/{success['task_id']}返回200并最终为done；截图接口返回200。处理：MSS截图、EasyOCR唯一定位VERIFY、控制器点击一次、再次截图及OCR、最终完成核验。结果：目标DOM为VERIFIED，点击计数1；OCR完整匹配VERIFIED；前端显示任务执行完成和已确认出现VERIFIED。耗时{success['duration_seconds']}秒。")
    image(doc, '02_console_live_success.png', '图1 成功用例的实际控制台结果', 5.5)
    image(doc, '03_target_after.png', '图2 实际控制器点击后的目标页面', 4.3)
    page_heading(doc, '七 异常证据与修复结果')
    add_body(doc, '位置：前端pollTask。原因：定时轮询在前一次请求尚未结束时再次发起，旧响应可能覆盖中断提示。修复：增加轮询执行锁，在finally释放，轮询中断时保留任务并提供恢复按钮。现在恢复同一任务成功，且中断期间开始按钮保持禁用。')
    image(doc, '05_poll_timeout.png', '图3 运行中任务轮询超时 恢复按钮保留原任务', 5.0)
    page_heading(doc, '七 异常证据与修复结果 续')
    add_body(doc, '负向结果对照：输入要求确认出现MISSING，项目实际点击后目标页显示VERIFIED。后端返回action_failed，前端显示动作验证失败。图4保留了实际页面、任务标识、错误说明与动作日志，证明执行一次点击不等于满足业务完成条件。')
    image(doc, '04_expected_result_missing.png', '图4 点击执行后预期MISSING未出现 页面显示动作验证失败', 6.0)
    page_heading(doc, '八 验收边界与复现')
    add_body(doc, '本周证明规则驱动的单步实时点击闭环，未证明模型自主长任务、任意文本输入、Windows或Linux真机能力。无显式预期文字的旧任务仅保存动作证据，不代表业务完成。运行时间与停止为循环边界及协作式控制，无法硬中断正在进行的OCR。任务为内存存储，不具备进程崩溃后的持久化恢复。')
    add_body(doc, '普通固定回归：.venv/bin/python scripts/run_week8_acceptance.py\n包含真实动作：.venv/bin/python scripts/run_week8_acceptance.py --live\n单独实时专项：使用捆绑Node运行scripts/run_week8_live_e2e.mjs。')
    add_body(doc, '预计完整验收180至300秒，实际时间随OCR与机器负载变化。需要桌面会话权限、本地OCR模型、Chrome以及空闲8765和18765端口。测试期间目标窗口需保持可见。全部服务和隔离浏览器在测试结束时关闭。无需 Kaggle 运行。')
    add_heading(doc, '九 提交材料')
    add_body(doc, '三份Word报告位于output/docx；论文源稿为reports/week8/结项报告.md；统计为output/week8/document_statistics.json。自动回归、既有浏览器回归和真实专项分别位于output/week8/verification、browser_regression、live_e2e。原始桌面图及OCR保留在output/local_bridge的任务目录。当前更改用于本地验收，云端站点发布不属于本次交付。')
    return finish(doc, '第八周验收测试报告.docx')


def thesis(auto, old, live, success):
    text = (ROOT / 'reports/week8/结项报告.md').read_text(encoding='utf-8')
    mapping = {'AUTO_TESTS': auto['tests_run'], 'AUTO_FAILURES': auto['failures'],
      'AUTO_ERRORS': auto['errors'], 'AUTO_SKIPPED': auto['skipped'], 'BROWSER_CASES': len(old['cases']),
      'LIVE_CASES': len(live['cases']), 'LIVE_TASK_ID': success['task_id'], 'LIVE_DURATION': success['duration_seconds']}
    for key, value in mapping.items():
        text = text.replace('{{' + key + '}}', str(value))
    assert '{{' not in text
    main_body = '# 第一章' + text.split('# 第一章', 1)[1].split('# 参考文献', 1)[0]
    body_paragraphs = '\n'.join(line for line in main_body.splitlines() if line.strip() and not line.startswith('#'))
    chars = len(re.findall(r'[\u4e00-\u9fff]', body_paragraphs))
    assert chars >= 8000, chars
    (WORK / '结项报告_最终正文.md').write_text(text, encoding='utf-8')
    stats = {'scope': '第一章至第十章正文，不含标题、摘要、参考文献、附录、图表说明',
      'chinese_characters': chars, 'minimum_required': 8000, 'meets_requirement': chars >= 8000,
      'count_method': 'regex U+4E00 through U+9FFF on non-heading main-body paragraphs',
      'source': 'output/week8/结项报告_最终正文.md'}
    (WORK / 'document_statistics.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    doc = Document(); configure_document(doc)
    s = doc.sections[0]
    s.page_width = Cm(21); s.page_height = Cm(29.7)
    s.top_margin = s.bottom_margin = Cm(2.3)
    s.left_margin = s.right_margin = Cm(2.5)
    normal = doc.styles['Normal']
    normal.font.name = 'Times New Roman'; normal.font.size = Pt(12)
    normal._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), 'Songti SC')
    normal.paragraph_format.line_spacing = Pt(20)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.first_line_indent = Pt(24)
    for h, size in [('Heading 1', 16), ('Heading 2', 14)]:
        st = doc.styles[h]; st.font.size = Pt(size)
        st.paragraph_format.first_line_indent = Pt(0)
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.space_before = Pt(12)
        st.paragraph_format.space_after = Pt(8)
    doc.styles['Heading 1'].paragraph_format.page_break_before = True
    title = text.splitlines()[0].removeprefix('# ')
    for _ in range(3): doc.add_paragraph()
    p = doc.add_paragraph(style='Title'); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(title)
    p.paragraph_format.first_line_indent = Pt(0)
    p = doc.add_paragraph('项目结项报告'); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    for _ in range(3): doc.add_paragraph()
    for label in ['研究周期  第一周至第八周', '成果范围  屏幕感知 受控执行 网页桥接与分层验证', '提交日期  2026年10月16日', f'正文汉字  {chars}字']:
        p = doc.add_paragraph(label); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
    doc.add_page_break()
    p = doc.add_paragraph('目录', style='Heading 1'); p.paragraph_format.page_break_before = False
    chapters = [l[2:] for l in text.splitlines() if l.startswith('# ')][1:]
    for line in ['摘要', 'Abstract', *chapters]:
        p = doc.add_paragraph(line + '\t0'); p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(15.8), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        p.paragraph_format.space_after = Pt(6)
    first_content = True
    for block in text.split('\n\n')[1:]:
        block = block.strip()
        if not block: continue
        if block.startswith('# '):
            doc.add_paragraph(block[2:], style='Heading 1')
        elif block.startswith('## '):
            name = block[3:]
            if name.startswith('5.3'):
                add_table(doc, ['来源', '项目处理记录', '当次格式检查'],
                          [['WebArena', '812', '通过'], ['ScreenAgent', '2000', '通过'],
                           ['Mind2Web', '1009', '通过'], ['合计', '3821', '通过']],
                          widths=[2.1, 2.1, 2.1])
                p = doc.add_paragraph('表1 第三周项目数据处理规模 训练划分3434条 验证划分387条')
                p.paragraph_format.first_line_indent = Pt(0)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if name.startswith('7.2'):
                add_table(doc, ['评价范围', '数量', '本周结果'],
                          [['自动单元及集成测试', str(auto['tests_run']), '全部通过'],
                           ['既有浏览器场景', str(len(old['cases'])), '全部通过'],
                           ['新增专项场景', str(len(live['cases'])), '全部通过'],
                           ['布局检查宽度', '6', '无横向溢出']], widths=[3.1, 1.0, 2.2])
                p = doc.add_paragraph('表2 分层验收结果 各类分母不同 不合并计算任务成功率')
                p.paragraph_format.first_line_indent = Pt(0)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if name.startswith('7.3'):
                image(doc, '02_console_live_success.png', '图1 第八周真实实时任务的前端完成状态', 6.1)
                image(doc, '03_target_after.png', '图2 项目控制器点击后 目标页显示VERIFIED', 5.1)
            p = doc.add_paragraph(name, style='Heading 1' if name in ('摘要', 'Abstract') else 'Heading 2')
            if first_content: first_content = False
        else:
            p = doc.add_paragraph(block)
            if block.startswith(('关键词', 'Keywords', '[')):
                p.paragraph_format.first_line_indent = Pt(0)
            if block.startswith('['):
                p.paragraph_format.line_spacing = 1.2
                p.paragraph_format.space_after = Pt(8)
    path = finish(doc, '第八周项目结项报告.docx')
    # Verify delivered OOXML body, not just the source draft.
    saved = Document(path)
    actual = '\n'.join(p.text for p in saved.paragraphs)
    assert '{{' not in actual and str(chars) in actual
    return path


def main():
    auto = read(WORK / 'verification/regression_summary.json')
    old = read(WORK / 'browser_regression/results.json')
    live = read(LIVE / 'results.json')
    assert auto['passed'] and auto['failures'] == auto['errors'] == auto['skipped'] == 0
    assert old['result'] == live['result'] == 'passed'
    assert len(old['cases']) == 8 and len(old['widths']) == 6 and len(live['cases']) == 7
    success = next(c for c in live['cases'] if c['id'] == 'real_live_click_success')
    for path in (weekly(auto, old, live, success), acceptance(auto, old, live, success), thesis(auto, old, live, success)):
        print(path)


if __name__ == '__main__': main()
