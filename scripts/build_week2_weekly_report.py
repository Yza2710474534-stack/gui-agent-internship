"""生成简洁的第二周进度周报，不替代验收测试报告。"""

from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
doc = Document()
section = doc.sections[0]
section.page_width, section.page_height = Inches(8.5), Inches(11)
section.top_margin = section.bottom_margin = Inches(.75)
section.left_margin = section.right_margin = Inches(.85)

for name, size in [('Normal', 11), ('Title', 18), ('Heading 1', 12)]:
    style = doc.styles[name]
    style.font.name = 'Arial Unicode MS'
    style.font.size = Pt(size)
    style.font.bold = name != 'Normal'
    style.font.color.rgb = RGBColor(0, 0, 0)
    fonts = style._element.get_or_add_rPr().rFonts
    for key in ['asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme']:
        fonts.attrib.pop(qn('w:' + key), None)
    for key in ['ascii', 'hAnsi', 'eastAsia', 'cs']:
        fonts.set(qn('w:' + key), 'Arial Unicode MS')
    style.paragraph_format.line_spacing = 1.15
    style.paragraph_format.space_after = Pt(7)
    if name == 'Heading 1':
        style.paragraph_format.space_before = Pt(9)
        style.paragraph_format.keep_with_next = True
    for border in list(style._element.get_or_add_pPr().findall(qn('w:pBdr'))):
        border.getparent().remove(border)

doc.core_properties.title = '第二周项目周报'
doc.core_properties.subject = '桌面 GUI 智能体项目进度跟踪与汇报'
doc.core_properties.author = '项目成员'
doc.add_paragraph('第二周项目周报', style='Title')
doc.add_paragraph('项目：基于多模态大模型的桌面 GUI 智能体开发与优化\n项目周期：第2周    姓名：____________')
doc.add_paragraph('本周完成 Mac 桌面截图、文字识别、坐标定位和基础控制模块，跑通打开“编辑”菜单并检查反馈的演示。代码包和验收测试报告已整理完成。')

doc.add_heading('一 本周任务完成情况', 1)
for text in [
    '1. 完成全屏、区域和连续截图，记录图片尺寸及坐标还原比例，验证1470×956截图和半尺寸输出。',
    '2. 接入 EasyOCR，输出文字、置信度、边界框和中心点；完成坐标换算、绘框及简单图标模板定位。',
    '3. 整理移动、点击、英文输入、滚动和拖拽函数。英文输入切换 ABC 后正常，文本编辑中的拖选改用 Mac 原生事件后正常。',
    '4. 完成“截图—识别—点击—反馈”演示，确认编辑菜单成功展开。补充并通过37项单元测试，整理运行说明和提交代码。',
]:
    doc.add_paragraph(text)

doc.add_heading('二 是否达到预期', 1)
doc.add_paragraph('Mac 本地基础开发目标已达到预期，截图、识别和菜单操作能够串联运行。37项单元测试使用模拟接口，不能替代实际桌面验证；本次整理控制函数后未重新实测全部输入和拖拽动作。')
doc.add_paragraph('跨平台验收尚未完成，目前只在 Mac 上做过现场验证，Windows/Linux 和不同物理显示器仍待补测。旧截图中的“窗口”仍有误识别，中文自动输入暂不支持。以上问题已在验收报告中注明。')

doc.add_heading('三 下周工作计划', 1)
for text in [
    '1. 复测整理后的输入和拖拽函数，继续排查“窗口”误识别，保留成功与失败记录。',
    '2. 学习 GUI 数据集和操作轨迹格式，整理少量“截图、目标、动作、结果”样例。',
    '3. 学习 Agent 的基本执行流程，尝试用简单函数连接任务、动作和反馈，暂不引入复杂代码结构。',
    '4. 有其他系统测试条件后补做跨平台验证；整理第三周学习记录、阶段成果和周报。',
]:
    doc.add_paragraph(text)

output = ROOT / 'output' / 'docx' / '第二周周报.docx'
output.parent.mkdir(parents=True, exist_ok=True)
doc.save(output)
print(output)
