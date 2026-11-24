# 数据来源与现存规模

本项目整理了WebArena、ScreenAgent和Mind2Web相关公开数据及项目样例。数据源分别参见[WebArena](https://github.com/web-arena-x/webarena)、[ScreenAgent](https://github.com/niuzaisheng/ScreenAgent)、[Mind2Web](https://github.com/OSU-NLP-Group/Mind2Web)。这些来源来自已有项目记录，本次没有重新获取或更新数据。

| 范围 | 总记录 | 训练 | 验证 | 证据 |
|---|---:|---:|---:|---|
| 当前本地划分 | 814 | 732 | 82 | `data/week3/splits/statistics.json` |
| 历史Kaggle预处理摘要 | 3821 | 3434 | 387 | `reports/week3/kaggle_full_summary.txt` |

历史全量产物尚未回传。以上是项目处理范围，不表示公开数据集官方全量规模，也不表示已完成视觉模型训练。实际图像、动作标注、授权和无泄漏划分仍需在后续VLM/LoRA实验前核对。

第三方数据及相关素材继续受各自来源的许可约束。本仓库不为这些材料另行授予许可；保留处理脚本、样例和来源记录用于阶段复核。
