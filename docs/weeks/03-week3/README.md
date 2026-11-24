# 第3周：数据处理、模型接口与基础Agent

可核实节点：2026-09-16。

## 工作与方法

规范WebArena、ScreenAgent和Mind2Web相关轨迹，统一JSONL字段；实现模型接口、计划解析、任务推进与反馈历史，并记录DeepSeek搜索计划。

## 已有结果

历史Kaggle摘要报告3821条有效记录，训练/验证3434/387。第三周39项单元测试通过，另有9月19日的运行器与浏览器补充记录。

## 当时的限制

当前本地仅814条及732/82划分，全量历史产物未回传。离线轨迹含模拟反馈；没有真实视觉模型部署或训练收益验收。

## 阶段报告

- [第三周周报.docx](../../../output/docx/第三周周报.docx)

- [第三周验收测试报告.docx](../../../output/docx/第三周验收测试报告.docx)

- [第三周补充测试报告.pdf](../../../output/pdf/第三周补充测试报告.pdf)

## 主要实现

- [week3_dataset.py](../../../src/week3_dataset.py)

- [week3_model.py](../../../src/week3_model.py)

- [week3_agent.py](../../../src/week3_agent.py)

- [week3_runtime.py](../../../src/week3_runtime.py)

- [week3_kaggle_full_preprocess.py](../../../scripts/week3_kaggle_full_preprocess.py)

## 验收依据

- [kaggle_full_summary.txt](../../../reports/week3/kaggle_full_summary.txt)

- [deepseek_summary.txt](../../../reports/week3/deepseek_summary.txt)

- [integration_test_report.md](../../../reports/week3/integration_test_report.md)

- [statistics.json](../../../data/week3/splits/statistics.json)

- [WEEK3_README.md](../../../WEEK3_README.md)

## 版本说明

代码链接指向本仓库当前归档快照，周报和日志用于说明历史阶段。并未把当前完整实现伪装成每周均已存在的源码版本。

[返回完整时间线](../../../TIMELINE.md)
