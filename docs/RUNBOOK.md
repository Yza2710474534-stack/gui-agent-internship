# 运行与复核

## 基础环境

推荐Python 3.12、macOS桌面会话和Chrome。根目录`requirements.txt`汇总原有基础控制与Agent依赖；文档生成工具的依赖未计入运行时。Windows/Linux保留接口，不代表已完成真机验收。

在项目根目录创建`.venv`并安装依赖后，执行`.venv/bin/python scripts/run_local_executor.py`。打开`http://127.0.0.1:8765/`，选择预览并提交任务。macOS需为实际运行Python的终端启用屏幕录制；真实控制还需辅助功能权限。首次OCR需联网下载模型至`artifacts/easyocr/models/`。

## 受控实时路径

停止预览服务后，执行`.venv/bin/python scripts/run_local_executor.py --enable-live`。使用独立练习页面，输入`点击 VERIFY，确认出现 VERIFIED`，检查最终状态、动作次数及新观察中的预期文字。该入口使用文字规则定位，最多一次动作；目标歧义时应停止。正式历史用例位于`output/week8/live_e2e/results.json`。

## 自动测试与历史复核

执行`.venv/bin/python -m unittest discover -s tests -v`运行自动测试。多数测试以模拟依赖验证逻辑，不操作真实桌面，不替代原始大纲的20任务评估。本次归档时的结果另存`verification/2026-11-24/`。

历史浏览器脚本`run_week7_browser_e2e.mjs`和`run_week8_live_e2e.mjs`保留原本的本机Playwright绝对导入路径；Chrome路径和`.venv/bin/python`也依赖macOS环境。迁移机器需安装Playwright并调整这些路径后再运行。历史报告生成和渲染脚本同样可能依赖本机文档运行时，不保证在新机器直接执行。

`run_week8_acceptance.py`会更新`output/week8/`中的结果；复现实验前应另存旧记录或在独立副本运行。`verification/`的新检查记录与原始验收分开保存。

## 材料完整性

执行`.venv/bin/python scripts/verify_archive.py`核对`archive_manifest.json`中列出的文件。该清单记录本次提交前的内容；后续主动修改文件后，校验不一致是版本变化，不会自动改写历史记录。
