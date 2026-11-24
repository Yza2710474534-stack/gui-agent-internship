# 第三周运行说明

本周完成公开 GUI 数据处理、基础 Agent、统一模型接口和离线闭环演示。代码保持为普通函数，便于逐段运行和修改。

## 已完成内容

1. 将 WebArena、ScreenAgent、Mind2Web 转成统一 JSONL 格式。
2. 本地先检查 814 条记录；随后在 Kaggle 完成 3,821 条全量数据检查，得到 3,434 条训练数据和 387 条验证数据。
3. 使用 LangChain 串联任务输入、模型规划和状态记录。
4. 支持模拟模型、OpenAI 兼容 API 和本地 Ollama 接口，已用 DeepSeek API 完成一次真实任务规划。
5. 三种数据集各取一条任务完成离线闭环；另加入长任务运行器，支持逐步验证、失败重试、重试上限、完成条件和 JSONL 日志。
6. 使用第二周真实“编辑菜单”操作留下的截图和 OCR 结果，补充真实截图单步复核；不会在测试时再次操作鼠标。
7. 将长任务拆成浏览器搜索、打开文件、文本编辑、消息草稿和关闭应用五类，分别定义步骤和完成条件，避免只用浏览器搜索代表所有办公流程。

## 本地复现

运行全部第三周测试：

```bash
./.venv/bin/python -m unittest tests.test_week3_dataset tests.test_week3_batch tests.test_week3_agent tests.test_week3_model tests.test_week3_trajectory_demo tests.test_week3_runtime
```

运行长任务、异常恢复、日志和真实截图测试：

```bash
./.venv/bin/python -m unittest -v tests.test_week3_runtime
```

生成一份 6 步长任务和失败重试日志示例：

```bash
./.venv/bin/python scripts/run_week3_runtime_demo.py
```

运行离线 Agent：

```bash
./.venv/bin/python src/week3_agent.py "点击编辑菜单" --provider mock --simulate
```

运行三种数据集闭环：

```bash
./.venv/bin/python src/week3_trajectory_demo.py data/week3/processed/webarena.jsonl data/week3/processed/screenagent.jsonl data/week3/processed/mind2web.jsonl --max-records 3 --provider mock
```

## Kaggle 完整数据处理

`scripts/week3_kaggle_full_preprocess.py` 用于 Kaggle。参数 `--mind2web-limit 0` 表示处理全部 Mind2Web 数据，不会因为 Mac 性能改成小训练集。2026 年 9 月 16 日已在 Kaggle 实际运行：WebArena 812 条、ScreenAgent 2,000 条、Mind2Web 1,009 条，共 3,821 条，全部通过检查；训练集 3,434 条，验证集 387 条。

## 当前边界

离线轨迹中的 `done` 仍然只表示模拟反馈完成，不能当成真实桌面成功。新增运行器只有在每一步验证通过且最终完成条件通过时才会返回 `done`。长任务目录目前分为浏览器搜索、打开文件、文本编辑、消息草稿和关闭应用五类，分类测试共覆盖 5 种工作流。2026 年 9 月 19 日已补充一次真实 Chrome 搜索任务，成功输入 `GUI Agent` 并通过页面标题、搜索框、结果标题和相关链接完成验证；文本编辑已有真实单步证据，其余三类目前明确标记为模拟测试。随后使用项目截图代码获得 1470×956、坐标比例 1:1 的真实 Chrome 截图，EasyOCR 和自动完成条件再次验证通过。目前各模块已真实验证，但步骤间仍有人工切换窗口，尚未形成单程序全自动实时循环。本机尚未安装 Ollama，也未运行本地多模态模型。DeepSeek API 已用于文字任务规划，API Key 只保存在用户当前终端环境中。
