# 第二周桌面感知与控制验收说明

本周交付代码和测试报告，已补齐基础控制函数和模块测试。采用简单函数，不新增框架。Mac 有实际操作记录；Windows/Linux 只有兼容接口和模拟测试，未完成真机验收。当前尚未接入大模型。

## 对照 PDF 要求

1. 截图：src/screen_capture.py 支持全屏、区域、连续截图及输出尺寸调整；每张连续截图附带时间、屏幕区域、图片尺寸、还原比例。采用 MSS 跨平台接口，不承诺固定帧率。
2. 识别：src/ocr_engine.py 使用 EasyOCR 识别中英文，区分低置信度结果。src/element_locator.py 补充非文字图标模板匹配，只返回最相似的一处，不代表通用图标理解。
3. 控制：src/controller.py 提供 move_to、click、type_text、scroll、drag_to 五个函数。Mac 拖拽沿用之前通过的原生事件方式，其他平台使用 PyAutoGUI。
4. 定位绘框：src/coordinate.py 负责缩放和起点偏移；src/visualizer.py 绘制绿框、红色中心点，保留原图。
5. 提交物：完整源代码、37项单元测试、原始测试日志、真实 OCR 及截图记录摘要、简洁 Word 测试报告。src/demo.py 保留“截图—识别—点击—反馈”的单次演示。

## 环境

现有项目直接使用 .venv，不用重新安装。Mac 实测环境为 Python 3.12.14，主要包版本见 reports/week2_environment.txt。

新机器先安装 Python 3.12，进入解压后的 week2_gui_agent 文件夹，再执行：

1. `python3 -m venv .venv`（Windows 改为 `py -3.12 -m venv .venv`）。
2. `./.venv/bin/python -m pip install -r requirements-week2.txt`。

Windows 后续命令中的 ./.venv/bin/python改成 .venv\Scripts\python.exe。Linux 需要桌面会话和 X11；Wayland 未适配。Mac 需要给运行终端屏幕录制、辅助功能权限。代码包不包含虚拟环境或 OCR 模型权重。

## 验证顺序

在项目根目录执行。除明确带 --click 或 --run 的命令外，不操作鼠标键盘。

1. 单元测试：`./.venv/bin/python scripts/verify_week2.py`。结果存入新的 reports/acceptance_时间/。
2. OCR 样例：`./.venv/bin/python src/ocr_engine.py --target 编辑`。首次联网下载模型；以后使用本地模型。
3. 完整只读检查：`./.venv/bin/python scripts/verify_week2.py --ocr --live`。识别随包图片、绘框、匹配苹果图标、连续实拍3张及输出1张半尺寸截图。--ocr 本身不会下载模型，应先完成上一步。
4. Mac 菜单演示：`./.venv/bin/python src/demo.py --target 编辑 --click`。模型加载后出现8秒提示，切到文本编辑，保持菜单关闭。只点击菜单标题，不执行下拉菜单命令。省略 --click 可先预览。
5. Mac 拖选：`./.venv/bin/python scripts/check_textedit_drag.py --run`。10秒内切到练习文档，将鼠标放在文字开头；脚本向右拖120像素。先在练习文档测试，勿用于重要内容。

## 基础控制函数怎么用

从 src.controller 导入需要的函数，顺序调用即可。例如 move_to(200, 100) 表示移动，不是点击；click(200, 100) 单击；type_text("Hello GUI Agent") 输入英文；scroll(-3) 向下滚动；drag_to(320, 100) 从当前鼠标位置开始拖拽。

坐标示例不能直接用于你的界面。控制函数只操作主屏幕，不会自动选择应用或输入框。输入前手动切换 ABC；中文字符串会被拒绝。通用函数没有 TextEdit 限制，只有菜单演示和拖选练习有前台保护。紧急停止可将鼠标移到主屏幕角落；拖拽中断后程序会尝试松开鼠标。

## 证据与限制

37项单元测试使用模拟接口，覆盖截图、OCR坐标、绘框、图标定位、控制调用与安全检查。真实 OCR 使用同一张菜单图片验证“编辑”，不能计算整体识别准确率。图标模板从同图裁取，仅检查定位流程。

9月10日20:12的历史集成记录中，“编辑”置信度约0.985，点击(184,16)后出现“全选、拷贝、粘贴、重做”，本人确认菜单展开。点击、英文输入、滚动及原生拖选此前已在 Mac 练习中确认；本次控制器整理后采用模拟回归，没有再次自动输入或拖选。

截图实测和缩小输出不等于换了物理显示器。1280×720、1470×956、1920×1080、3840×2160和2倍像素关系来自构造数据测试。MSS 元数据描述截图区域；若系统截图坐标与鼠标逻辑坐标不同，调用 image_to_screen 时必须传入对应的鼠标坐标区域，不能盲用像素宽高。

旧图“窗口”被误读的问题仍存在。Windows/Linux、不同物理显示器、跨显示器控制、不同主题图标、中文自动输入均未通过真机验证。不能填写“全平台全部验收通过”。

代码包不含新拍的完整屏幕图片，避免带入无关桌面内容。当前机器原图保留在 output/acceptance/；包内保存日志和摘要，旧 JSON 中的绝对路径仅为历史记录。解压后重新运行会生成当前机器的新路径。
