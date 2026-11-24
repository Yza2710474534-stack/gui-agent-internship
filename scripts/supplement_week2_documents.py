"""仅补充周报截图和测试明细，保留原 Word 及用户已有修改。"""

from collections import Counter
from pathlib import Path
import re
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'output/docx'
EVIDENCE = ROOT / 'reports/acceptance_20260910_203013_921617'
DEMO = ROOT / 'output/demo/20260910_201203_070856'
log = (EVIDENCE / 'unittest.txt').read_text(encoding='utf-8')
counts = Counter(re.findall(r'\(test_\w+\.(\w+)\.test_\w+\) \.\.\. ok', log))
assert sum(counts.values()) == 37 and 'Ran 37 tests' in log and log.rstrip().endswith('OK')


def text(doc, value, size=11):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.1
    run = p.add_run(value)
    font(run, size)
    return p


def font(run, size=11, bold=False):
    run.font.name = 'Arial Unicode MS'
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    fonts = run._element.get_or_add_rPr().rFonts
    for key in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
        fonts.attrib.pop(qn('w:' + key), None)
    for key in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
        fonts.set(qn('w:' + key), 'Arial Unicode MS')


def heading(doc, value):
    p = doc.add_heading(value, 1)
    for run in p.runs:
        font(run, 12, True)
    return p


def picture(doc, path, width, height, right, bottom=0):
    # 在 Word 中显示局部，不改动或重新生成截图文件。
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    shape = p.add_run().add_picture(str(path), width=Inches(width))
    shape.height = Inches(height)
    rect = OxmlElement('a:srcRect')
    for name, value in [('l', 0), ('t', 0), ('r', right), ('b', bottom)]:
        rect.set(name, str(value))
    fill = shape._inline.graphic.graphicData.pic.blipFill
    fill.insert(1, rect)
    shape._inline.docPr.set('descr', '实际运行截图的局部显示，原文件为' + path.name)


weekly = Document(DOCS / '第二周周报.docx')
weekly.add_page_break()
p = heading(weekly, '四 实际运行结果截图')
weekly.add_comment(p.runs, '新增实际运行截图及说明。截图来自9月10日已保存的演示记录，原正文保持不变。', author='补充说明')
text(weekly, '以下为2026年9月10日20:12在 Mac 文本编辑中的实际运行截图。为便于阅读，只显示相关区域；没有重新生成界面或修改识别结果。')
picture(weekly, DEMO / 'marked.png', 6, 1.2, 60000)
text(weekly, '图1 识别定位结果。绿色框标出了“编辑”，本次计划点击坐标为(184,16)，置信度约0.985。图片显示原1000×80截图的左侧400像素。', 10)
picture(weekly, DEMO / 'after_action.png', 6, 6 * 330 / 420, 58000, 45000)
text(weekly, '图2 点击后的结果。编辑菜单已展开，可见“拷贝、粘贴、全选”等项目；程序检测到新增菜单文字，本人当时确认操作成功。显示原1000×600截图左上420×330区域。', 10)
text(weekly, '原图目录：output/demo/20260910_201203_070856\n图1：marked.png；图2：after_action.png。坐标只适用于本次截图，不能直接用于其他界面。', 10)
weekly.save(DOCS / '第二周周报_含运行截图.docx')

report = Document(DOCS / '第二周验收测试报告.docx')
report.add_page_break()
p = heading(report, '五 各模块测试用例与结果')
report.add_comment(p.runs, '新增模块统计和具体案例。按9月10日保存的37项测试日志统计，本次未重新执行测试。', author='补充说明')
text(report, '统计依据为9月10日保存的单元测试日志：共37项，通过37项，失败0项，跳过0项，日志记录测试运行耗时0.008秒（不含启动和导入）。每个test方法算1项，方法内多个输入不重复计数。', 10)

rows = [
    ('截图', '模拟截图、缩放和连续保存；检查无屏幕、越界及写入失败。', '连续截图3次，检查3张不同文件名的PNG及对应JSON均已保存。', 'CaptureTests'),
    ('坐标换算', '构造不同分辨率、2倍像素关系、负偏移和非法坐标。', '图内(50,20)，图片100×100，区域(-200,30,200,100)，应得(-100,50)。', 'CoordinateTests'),
    ('OCR处理', '模拟识别结果，检查坐标还原、低置信度过滤、缺图及参数异常。', '阈值0.3时，保留置信度0.98的“编辑”，将0.1的“错误”归入低置信度结果。', 'OCRTests'),
    ('图标定位\n及绘框', '构造图标及缩放图标，检查缺失/纯色模板、标注颜色、坏框和原图不变。', '12×12图标放在(30,20)，应定位中心(35.5,25.5)；绘框后原图不变。', 'ElementTests'),
    ('鼠标键盘', '模拟移动、点击、输入、滚动、拖拽；覆盖越界、非法输入及中断松键。', '输入Hello GUI Agent应调用英文输入接口；模拟Mac拖拽中断后应发送松键事件。', 'ControllerTests'),
    ('演示闭环\n及保护', '构造唯一/缺失/重名目标；组合图片变化和新增文字，检查前台及点击边界。', '仅图片变化或仅菜单文字变化不判成功；两者满足才初判菜单展开。', 'DemoTests'),
]
table = report.add_table(rows=1, cols=5)
table.autofit = False
widths = [.95, 1.9, 2.7, .6, .6]
for col, width in zip(table.columns, widths):
    col.width = Inches(width)
all_rows = [('测试模块', '用例如何设计', '代表案例与预期结果', '测试数', '通过数')]
all_rows += [(a, b, c, str(counts[k]), str(counts[k])) for a, b, c, k in rows]
all_rows.append(('合计', '按test方法统计', '失败0项；跳过0项', '37', '37'))
for index, values in enumerate(all_rows):
    cells = table.rows[0].cells if index == 0 else table.add_row().cells
    for col, (cell, value) in enumerate(zip(cells, values)):
        cell.width = Inches(widths[col])
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(1.5)
        p.paragraph_format.space_before = Pt(1.5)
        p.paragraph_format.line_spacing = 1.05
        if col >= 3:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        font(p.add_run(value), 10, index == 0)
        pr = cell._tc.get_or_add_tcPr()
        borders = OxmlElement('w:tcBorders')
        for side in ('top', 'left', 'bottom', 'right'):
            edge = OxmlElement('w:' + side)
            for name, val in [('val', 'single'), ('sz', '4'), ('color', 'D9D9D9')]:
                edge.set(qn('w:' + name), val)
            borders.append(edge)
        pr.append(borders)
        margins = OxmlElement('w:tcMar')
        for side in ('top', 'left', 'bottom', 'right'):
            edge = OxmlElement('w:' + side)
            edge.set(qn('w:w'), '70')
            edge.set(qn('w:type'), 'dxa')
            margins.append(edge)
        pr.append(margins)
        if index == 0:
            shade = OxmlElement('w:shd')
            shade.set(qn('w:fill'), 'E8EDF2')
            pr.append(shade)
    trpr = table.rows[index]._tr.get_or_add_trPr()
    trpr.append(OxmlElement('w:cantSplit'))
table.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))

heading(report, '六 一个完整用例说明')
text(report, '案例：缩放与起点偏移。输入一张500×40的识别图片，“编辑”中心为(100,10)，对应屏幕区域为(50,100,1000,80)。调用定位计划函数，检查生成的点击坐标及执行标志。', 10)
text(report, '预期：横纵比例均为2，屏幕坐标为(100×2+50,10×2+100)=(250,120)，且executed为False，表示只生成计划，不真实点击。实际：断言全部通过，日志记为ok。对应tests/test_demo.py中的test_scale_and_offset。', 10)
text(report, '上述37项都是单元测试，OCR和鼠标接口使用模拟数据。真实OCR推理、连续截图和菜单展开另见原报告及周报截图，不计入这37项；不据此声称全平台通过或OCR准确率100%。', 10)
text(report, '日志：reports/acceptance_20260910_203013_921617/unittest.txt\n模块测试：tests/test_modules.py；闭环测试：tests/test_demo.py。', 9)
report.save(DOCS / '第二周验收测试报告_含用例明细.docx')
print('已保存周报截图版和测试报告明细版；原文件未修改。')
