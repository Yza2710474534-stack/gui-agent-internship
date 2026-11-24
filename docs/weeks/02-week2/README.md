# 第2周：屏幕感知、坐标映射与基础控制

可核实节点：2026-09-10。

## 工作与方法

封装MSS截图、EasyOCR识别、坐标转换和绘框，整理移动、点击、英文输入、滚动与拖拽接口，完成Mac编辑菜单演示。

## 已有结果

37项单元测试通过；历史现场记录中点击“编辑”后出现展开菜单。9月10日环境与测试记录可复核。

## 当时的限制

测试多数使用模拟接口。Windows/Linux、不同物理显示器、中文自动输入和全部控制函数整理后的实测仍不充分。

## 阶段报告

- [第二周周报.docx](../../../output/docx/第二周周报.docx)

- [第二周验收测试报告.docx](../../../output/docx/第二周验收测试报告.docx)

- [第二周测试报告.docx](../../../output/docx/第二周测试报告.docx)

## 主要实现

- [screen_capture.py](../../../src/screen_capture.py)

- [ocr_engine.py](../../../src/ocr_engine.py)

- [controller.py](../../../src/controller.py)

- [coordinate.py](../../../src/coordinate.py)

- [element_locator.py](../../../src/element_locator.py)

## 验收依据

- [WEEK2_README.md](../../../WEEK2_README.md)

- [week2_environment.txt](../../../reports/week2_environment.txt)

- [week2_unittest.txt](../../../reports/week2_unittest.txt)

## 版本说明

代码链接指向本仓库当前归档快照，周报和日志用于说明历史阶段。并未把当前完整实现伪装成每周均已存在的源码版本。

[返回完整时间线](../../../TIMELINE.md)
