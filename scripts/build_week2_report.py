"""生成简洁的第二周测试报告，并打包现有练习代码。"""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]


def build_report():
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = Inches(0.6)
    section.bottom_margin = Inches(0.55)
    section.left_margin = section.right_margin = Inches(0.8)
    for name, size in (("Normal", 11), ("Title", 18), ("Heading 1", 12)):
        style = doc.styles[name]
        style.font.name = "Arial Unicode MS"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = name != "Normal"
        fonts = style._element.get_or_add_rPr().rFonts
        for key in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
            fonts.attrib.pop(qn(f"w:{key}"), None)
        for key in ("ascii", "hAnsi", "eastAsia", "cs"):
            fonts.set(qn(f"w:{key}"), "Arial Unicode MS")
        style.paragraph_format.line_spacing = 1.12
        style.paragraph_format.space_after = Pt(4)
        if name == "Heading 1":
            style.paragraph_format.space_before = Pt(7)
            style.paragraph_format.keep_with_next = True
        ppr = style._element.get_or_add_pPr()
        for border in list(ppr.findall(qn("w:pBdr"))):
            ppr.remove(border)

    doc.core_properties.title = "第二周桌面感知与控制测试报告"
    doc.add_paragraph("第二周桌面感知与控制测试报告", style="Title")
    doc.add_paragraph("项目：基于多模态大模型的桌面 GUI 智能体开发与优化\n记录日期：2026年9月10日    姓名：____________")
    doc.add_paragraph("阶段结论：Mac 本地基础练习已完成，4项自动测试通过，打开“编辑”菜单的操作与反馈得到现场确认。当前版本仍有待完善项，不等于全部第二周要求已验收。")

    doc.add_heading("一 本周完成情况", 1)
    for text in (
        "完成全屏、区域和连续截图练习。全屏尺寸为1470×956，菜单栏测试图为1000×80。",
        "接入中英文 OCR，输出文字、置信度、边界框和中心点；完成坐标缩放、偏移换算及绘框验证。",
        "手动验证鼠标移动、点击、英文输入、滚动及原生拖选；串联截图、识别、定位、点击和截图反馈。",
    ):
        doc.add_paragraph(text)

    doc.add_heading("二 自动测试结果", 1)
    doc.add_paragraph("2026年9月10日重新运行 tests/test_demo.py，结果为4项通过、0项失败，输出已保存到 reports/week2_unittest.txt。覆盖内容如下：")
    for n, text in enumerate((
        "坐标缩放和截图起点偏移计算正确。",
        "未找到目标或出现重名目标时，不生成点击动作。",
        "反馈判断同时检查画面变化与新增菜单文字。",
        "前台应用不符或点击位置越界时，阻止调用点击。",
    ), 1):
        p = doc.add_paragraph(f"{n}. {text}")
        p.paragraph_format.space_after = Pt(2)
    doc.add_paragraph("上述测试使用模拟鼠标和构造数据，不实际操作桌面，也未覆盖全部截图、OCR和输入功能。")

    doc.add_heading("三 手动与集成验证", 1)
    doc.add_paragraph("截图、绘框、移动、输入、滚动和拖选均由本人在 Mac 上观察确认。英文输入出现汉字后，切换 ABC 输入法重试正常；TextEdit 自动拖选改用原生鼠标事件后正常。")
    doc.add_paragraph("9月10日20:12的集成记录中，“编辑”置信度为0.985，点击坐标为(184,16)。点击后新增“全选、拷贝、粘贴、重做”等菜单文字，程序初步判断菜单展开，本人现场确认结果一致。证据目录：output/demo/20260910_201203_070856。")

    doc.add_heading("四 遗留问题与后续计划", 1)
    doc.add_paragraph("旧截图中的“窗口”仍被误读为“囱0”。移动、输入、滚动尚未统一封装，拖选仍为独立脚本；真实多分辨率、多显示器及 Windows/Linux 场景未验证。当前流程采用固定规则，尚未接入大模型规划。")
    doc.add_paragraph("下周先补齐控制接口与测试，再学习 GUI 数据集处理和 Agent 框架。")
    output = ROOT / "output" / "docx" / "第二周测试报告.docx"
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    print(output)


def bundle_code():
    paths = [
        *sorted((ROOT / "src").glob("*.py")),
        *sorted((ROOT / "tests").glob("test_*.py")),
        ROOT / "scripts/check_textedit_drag.py",
        ROOT / "scripts/check_easyocr.py",
        ROOT / "scripts/check_mac_environment.py",
        ROOT / "requirements-mac.txt",
        ROOT / "requirements-ocr.txt",
        ROOT / "WEEK2_README.md",
        ROOT / "reports/week2_unittest.txt",
        ROOT / "reports/week2_environment.txt",
        ROOT / "output/screenshots/orc测试图像.png",
    ]
    output = ROOT / "output" / "第二周代码包.zip"
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, str(Path("第二周代码") / path.relative_to(ROOT)))
    print(output)


if __name__ == "__main__":
    build_report()
    bundle_code()
