# 第八周运行与交付说明

## 复现

1. 在当前Mac项目根目录执行 `.venv/bin/python scripts/run_week8_acceptance.py`，检查自动回归和既有浏览器端到端场景，预计90至180秒。
2. 执行 `.venv/bin/python scripts/run_week8_acceptance.py --live`，追加真实实时专项；完整运行预计180至300秒。目标窗口需保持可见，8765与18765端口需空闲，运行进程需有屏幕录制和辅助功能权限。
3. 报告生成使用捆绑Python执行 `scripts/build_week8_reports.py`，需先有三套通过的证据。报告位于 `output/docx/`，论文源稿位于 `reports/week8/结项报告.md`，正文统计位于 `output/week8/document_statistics.json`。

## 当前成果

真实输入为“点击 VERIFY，确认出现 VERIFIED”。前端真实提交HTTP任务，由项目MSS、EasyOCR及PyAutoGUI执行一次点击；目标页DOM和新截图OCR共同确认VERIFIED，任务done，前端显示完成说明。目标按钮不是由Playwright点击。项目网页实时规划当前为规则驱动单步文字点击，不代表大模型自主多步任务。

错误预期MISSING触发action_failed；同名目标触发stopped且零动作。前端轮询现在避免重叠；状态查询中断后保留原任务并提供恢复按钮，避免重复提交；图片404提供单独重试入口。超时和循环上限状态可释放后端任务槽，并在前端正确结束。

## 证据分类

- `output/week8/verification/`：自动回归，模拟依赖与构造数据居多；HTTP接口测试使用真实回环HTTP及模拟执行器。
- `output/week8/browser_regression/`：第七周8个浏览器场景在本周重跑，包含实际服务停止与重启；六种宽度另列。
- `output/week8/live_e2e/`：7个专项场景。成功和错误预期各实际点击1次；目标歧义0次；恢复和窄屏使用预览。
- `output/local_bridge/<任务标识>/`：项目原始MSS截图、OCR与事件日志；专项目录有任务记录和事件副本。

轮询超时与断线在浏览器网络层注入，后端继续处理，不等于服务进程崩溃恢复。任务存储仍在内存。停止与运行时限为协作式及循环边界控制，不能硬中断进行中的OCR。无显式业务结果条件的旧任务仅保存动作证据。原工程验收时未发布云端；2026年10月16日最终核对后，经用户明确授权已发布前端版本3，权限保持不变。

本周无需 Kaggle 运行，没有模型训练、微调或新增GPU推理。Node可用 `GUI_AGENT_NODE` 指定；当前浏览器脚本依赖本机捆绑Playwright路径与Google Chrome。新机器需调整依赖路径并准备OCR模型。

## 最终验收

此处测试通过仅代表当前工程范围。原始八周PDF大纲仍有LoRA、20任务定量评估、视频等缺项；完整核对见 reports/week8/项目最终核对清单.md，不能把126项自动测试或15个浏览器场景代替原纲20个桌面任务。

126项自动测试、8个既有浏览器场景、7个新增专项及6种宽度检查通过。三份Word共36页，正文10996个汉字。最终摘要为 `output/week8/acceptance_summary.json`，校验清单为 `output/week8/delivery_manifest.json`。

文档渲染使用捆绑Python运行 `scripts/render_week8_reports.py`，自动加载系统中文字体并依据渲染页码填写目录。渲染图片仅用于内部排版核查，最终交付为 `output/docx/` 下的三份Word。
