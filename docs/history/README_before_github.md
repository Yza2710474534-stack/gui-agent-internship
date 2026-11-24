# GUI Agent 桌面原型

本项目已实现macOS上的屏幕采集、OCR、坐标映射、受控动作、任务循环与网页控制台，并完成一次真实单步点击闭环。**按最初八周PDF大纲核对，整个项目尚未全部完成**；LoRA训练、20个真实桌面任务的定量评估和演示视频仍缺失。最终状态以[项目最终核对清单](reports/week8/项目最终核对清单.md)为准。

## 快速运行

1. 在当前项目根目录执行 `.venv/bin/python scripts/run_local_executor.py`，默认仅预览；浏览器打开 `http://127.0.0.1:8765/`。
2. 确需真实单次点击时，停止预览服务后执行 `.venv/bin/python scripts/run_local_executor.py --enable-live`。输入格式为 `点击 可见文字，确认出现 预期结果文字`，先在受控练习页面使用。
3. 自动回归执行 `.venv/bin/python scripts/record_week8_regression.py`；浏览器验收执行 `.venv/bin/python scripts/run_week8_acceptance.py`，追加 `--live` 才运行真实桌面专项。完整验收预计180至300秒。

现有Mac可直接使用项目虚拟环境。新机器需Python3.12、Chrome、屏幕录制与辅助功能权限，按requirements文件安装依赖并准备EasyOCR权重。当前浏览器和文档生成脚本包含本机捆绑Node、Playwright和文档工具的绝对路径，新机器须调整；不能宣称解压后无需配置即可全平台运行。详细约束见WEEK2_README.md、WEEK3_README.md及WEEK8_README.md。

## 目录

- `src/`：屏幕感知、控制、模型接口、数据处理、任务循环和本地HTTP服务。
- `tests/`：126个自动单元及集成测试，主要使用模拟依赖；不能替代真实任务评估。
- `scripts/`：演示、数据预处理、验收、报告生成和渲染入口。
- `gui-agent-console/dist/index.html`：当前前端，已发布为线上版本3；版本与发布包状态见output/week8/final_audit/frontend_sync_status.json。
- `reports/`、`output/docx/`及`output/week8/`：历史说明、周报、结项报告和原始验收记录。

## 能力与边界

实时网页入口目前通过规则定位可见文字，仅执行一次受控点击；不会向未知焦点输入文本。模型API接口与模拟长任务已经实现，但没有真实开源多模态模型部署或模型驱动长任务的完整验收。消息草稿不能替代原PDF的发送消息实测，实际发送需要明确授权。任务记录在内存，停止和超时为协作式及循环边界控制，无法硬中断正在进行的OCR。

本地完整源代码位于本目录；现有Git仓库只覆盖前端，不是整个Python项目的GitHub仓库。最终源码材料包不含虚拟环境、OCR权重、凭据和无关桌面截图。三份第八周Word报告仍可单独打开，不能以源码压缩包替代。

## Kaggle与结项口径

完成目前的工程回归无需Kaggle。若要满足原PDF第五周的多模态模型LoRA微调，仍需GPU实验，可使用Kaggle或Colab；须产生真实训练日志、适配器权重及微调前后对比。目前只有历史数据预处理记录，没有上述训练成果。

本地data/week3/splits为814条处理记录及732/82划分；历史Kaggle摘要记录3821条及3434/387划分，但对应全量产物尚未回传到当前目录，二者不可混用。最新完整性核对另见reports/week8/项目最终核对清单.md。
