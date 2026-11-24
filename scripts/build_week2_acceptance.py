"""生成第二周验收报告与代码包，保留上一版文件。"""

import json
from pathlib import Path
import re
from zipfile import ZipFile, ZIP_DEFLATED

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]


def main():
    # 只采用同时完成单元测试、真实OCR和实拍的记录。
    evidence = None
    for path in sorted((ROOT / 'reports').glob('acceptance_*/summary.json'), reverse=True):
        data = json.loads(path.read_text(encoding='utf-8'))
        checks = data['checks']
        if all(checks.get(k, {}).get('passed') for k in ('unit_tests', 'real_ocr', 'icon_template', 'live_capture')):
            evidence = path.parent
            break
    if evidence is None:
        raise RuntimeError('请先运行 verify_week2.py --ocr --live 并通过检查')
    log = (evidence / 'unittest.txt').read_text(encoding='utf-8')
    count = int(re.search(r'Ran (\d+) tests', log).group(1))
    data = json.loads((evidence / 'summary.json').read_text(encoding='utf-8'))
    live = data['checks']['live_capture']
    width, height = live['frames'][0]['image_size']
    small_w, small_h = live['scaled'][0]['image_size']
    target = data['checks']['real_ocr']['matches'][0]

    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(.65)
    section.left_margin = section.right_margin = Inches(.8)
    for name, size in (('Normal', 11), ('Title', 18), ('Heading 1', 12)):
        style = doc.styles[name]
        style.font.name = 'Arial Unicode MS'
        style.font.size = Pt(size)
        style.font.bold = name != 'Normal'
        style.font.color.rgb = RGBColor(0, 0, 0)
        fonts = style._element.get_or_add_rPr().rFonts
        for key in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
            fonts.attrib.pop(qn('w:' + key), None)
        for key in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
            fonts.set(qn('w:' + key), 'Arial Unicode MS')
        style.paragraph_format.line_spacing = 1.12
        style.paragraph_format.space_after = Pt(4)
        if name == 'Heading 1':
            style.paragraph_format.space_before = Pt(7)
            style.paragraph_format.keep_with_next = True
        for border in list(style._element.get_or_add_pPr().findall(qn('w:pBdr'))):
            border.getparent().remove(border)

    doc.core_properties.title = '第二周桌面感知与控制验收测试报告'
    doc.add_paragraph('第二周桌面感知与控制验收测试报告', style='Title')
    doc.add_paragraph('项目：基于多模态大模型的桌面 GUI 智能体开发与优化\n日期：2026年9月10日    姓名：____________')
    doc.add_paragraph(f'本周已补齐桌面感知与控制模块代码，{count}项单元测试全部通过，Mac 截图和 OCR 检查通过。已具备本地基础演示和提交材料；Windows/Linux 及不同物理显示器仍待实测，不能认定为全平台验收通过。')

    doc.add_heading('一 对照第二周任务', 1)
    for text in (
        '截图：采用 MSS，支持全屏、区域、连续截图及调整输出尺寸，保存时间、区域与坐标还原信息。',
        '识别：EasyOCR 输出中英文、置信度、边界框和中心点；另补充图标模板匹配，用于固定外观的非文字元素。',
        '控制：统一提供移动、点击、英文输入、滚动、拖拽函数。Mac 拖拽保留原生事件方式，增加越界和中断松键检查。',
        '定位：完成缩放与起点偏移换算，使用 OpenCV 绘制文字框和中心点，原始图片不变。',
    ):
        doc.add_paragraph(text)

    doc.add_heading('二 自动测试和实测结果', 1)
    doc.add_paragraph(f'单元测试：{count}项通过，0项失败。覆盖截图保存、分辨率信息、OCR坐标与低置信度过滤、模板匹配、绘框、控制调用和点击保护。测试使用构造图片及模拟鼠标接口，不代表真实桌面操作。')
    doc.add_paragraph(f'本次实测：Mac 连续保存3张{width}×{height}截图，另输出{small_w}×{small_h}图片，还原比例为2。已有菜单截图中的“编辑”置信度为{target["confidence"]:.3f}，中心为({target["center"][0]:.2f},{target["center"][1]:.2f})，文字框检查正常。苹果图标的同图模板定位通过，不作为泛化能力或识别准确率证明。')
    doc.add_paragraph('此前现场验证：移动、点击、英文输入、滚动和原生拖选已在 Mac 练习中确认。20:12的菜单演示点击(184,16)后，程序检测到新增“全选、拷贝、粘贴、重做”，本人确认菜单展开。本次整理控制接口后只做模拟回归，未再次自动输入或拖选。')

    doc.add_heading('三 问题与验收边界', 1)
    doc.add_paragraph('旧图中的“窗口”仍可能识别错误；逐键输入只支持英文等字符，须切换 ABC 输入法。控制函数限主屏幕。多尺寸和2倍像素关系通过构造数据测试，但不同物理分辨率、多显示器及 Windows/Linux 尚未真机验证。当前闭环使用规则反馈，未接入大模型。')

    doc.add_heading('四 提交材料与复现', 1)
    doc.add_paragraph('提交第二周验收代码包.zip和本报告。代码包包含源码、测试、运行说明与原始日志，不含模型权重。复现步骤见 WEEK2_README.md，证据见 reports 目录。后续补测其他系统与物理显示器。')

    output = ROOT / 'output' / 'docx' / '第二周验收测试报告.docx'
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    print(output)

    paths = [*sorted((ROOT / 'src').glob('*.py')), *sorted((ROOT / 'tests').glob('test_*.py')),
             ROOT / 'scripts/verify_week2.py', ROOT / 'scripts/check_textedit_drag.py',
             ROOT / 'requirements-week2.txt', ROOT / 'WEEK2_README.md',
             ROOT / 'reports/week2_environment.txt',
             ROOT / 'output/screenshots/orc测试图像.png',
             ROOT / 'output/demo/20260910_201203_070856/result.json',
             *sorted(evidence.glob('*'))]
    archive_path = ROOT / 'output' / '第二周验收代码包.zip'
    with ZipFile(archive_path, 'w', compression=ZIP_DEFLATED) as archive:
        for path in paths:
            if path.is_file():
                archive.write(path, str(Path('week2_gui_agent') / path.relative_to(ROOT)))
    print(archive_path)


if __name__ == '__main__':
    main()
