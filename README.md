# GUI Agent：八周桌面智能体项目

基于Python、MSS、EasyOCR和本地网页控制台的macOS桌面GUI原型。项目覆盖截图、文字定位、坐标映射、受控执行、反馈验证和任务状态展示。当前已验证一次规则驱动的真实单步点击闭环。

**先看[八周时间线](TIMELINE.md)**，按时间顺序进入每周的工作、实现、报告和验收依据。快速查阅全部材料可打开[材料索引](docs/DELIVERABLES.md)。

## 已验证的成果

| 范围 | 2026-10-16的历史验收 |
|---|---|
| 自动单元与集成测试 | 126项通过，多数使用模拟依赖 |
| 既有浏览器回归 | 8个场景通过 |
| 新增实时专项 | 7个场景通过，含成功及拒绝/恢复分支 |
| 网页布局 | 检查6种视口宽度 |
| 真实成功样例 | 从前端输入到项目控制器点击1次，再由OCR和目标页状态验证；单次23.5778秒 |

这些测试使用不同分母，不能合并为整体桌面任务成功率。原始八周PDF仍有未完成项，见[最终核对清单](reports/week8/项目最终核对清单.md)。LoRA训练、20个真实任务的量化对比和演示视频尚未完成。

## 运行本地预览

建议在带桌面会话的macOS和Python 3.12环境运行：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/run_local_executor.py
```

浏览器打开 <http://127.0.0.1:8765/>。预览只观察屏幕并生成动作建议。首次使用OCR需下载EasyOCR模型；屏幕录制和辅助功能权限按[运行说明](docs/RUNBOOK.md)配置。Python服务同时提供前端，不需要前端构建。

基础自动回归：

```bash
.venv/bin/python -m unittest discover -s tests -v
```

真实点击通过`--enable-live`显式启用，输入示例为`点击 VERIFY，确认出现 VERIFIED`。仅在隔离测试页使用，目前网页实时入口最多执行一次可见文字点击。详细操作和历史脚本环境限制见[运行说明](docs/RUNBOOK.md)。

## 仓库结构

```text
TIMELINE.md                 八周时间线和结项补充节点
docs/weeks/01-week1 … 08-week8/  每周导航
src/                        Python实现
gui-agent-console/dist/     前端页面
tests/、scripts/            自动测试、实验及报告工具
reports/、output/docx/、output/pdf/  原始报告和最新结项报告
output/week3 … week8/       历史运行与验收记录
docs/feedback/              已填写的实习反馈表
verification/2026-11-24/    本次归档检查
archive_manifest.json       文件SHA-256校验清单
```

原始实现和报告按现有内容保存；新增时间线负责组织材料。仓库提交时间代表本次归档时间，历史周次不通过倒填提交日期模拟。原有前端提交摘要保存在`docs/history/`。

## 数据、交付和后续工作

本地数据为814条及732/82划分；历史Kaggle摘要为3821条及3434/387划分，全量文件未回传，二者保持区分。数据来源和使用边界见[数据说明](docs/DATA_SOURCES.md)。

最新[结项报告](output/docx/结项报告.docx)为31页，后续技术方案包括任务持久化、动作前焦点校验、取消机制、视觉模型接入、LoRA及20任务评测。方案尚未计入已完成成果。完整报告索引见[材料索引](docs/DELIVERABLES.md)。

仓库不包含虚拟环境、模型权重、访问凭据、临时排版预览、个人求职表和无关桌面截图。归档范围及历史文件解释见[归档说明](docs/ARCHIVE_SCOPE.md)。
