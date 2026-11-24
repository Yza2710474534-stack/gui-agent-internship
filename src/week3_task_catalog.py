"""第三周长任务分类目录；每类任务都有自己的完成条件。"""

import copy


TASK_SCENARIOS = [
    {
        "scenario_id": "browser_search",
        "category": "浏览器搜索",
        "instruction": "打开浏览器并搜索 GUI Agent",
        "steps": ["确认浏览器已打开", "定位地址栏", "输入并提交 GUI Agent", "检查搜索结果"],
        "done_condition": "搜索框包含 GUI Agent 且页面出现相关结果",
        "execution_status": "real_single_run",
    },
    {
        "scenario_id": "open_file",
        "category": "文件打开",
        "instruction": "打开桌面上的项目说明文件",
        "steps": ["确认文件管理器已打开", "定位项目说明文件", "双击打开文件", "检查文件内容已显示"],
        "done_condition": "目标文件窗口出现且标题或内容匹配",
        "execution_status": "simulation_only",
    },
    {
        "scenario_id": "text_edit",
        "category": "文本编辑",
        "instruction": "在文本编辑中输入一行项目记录",
        "steps": ["确认文本编辑已打开", "定位编辑区域", "输入项目记录", "检查文字已出现在文档中"],
        "done_condition": "文档中出现完整项目记录",
        "execution_status": "single_step_evidence",
    },
    {
        "scenario_id": "message_draft",
        "category": "消息草稿",
        "instruction": "在消息应用中准备一条项目进度草稿",
        "steps": ["确认消息应用已打开", "定位联系人或草稿区域", "输入进度内容", "检查草稿内容正确"],
        "done_condition": "草稿内容完整，但不自动发送",
        "execution_status": "simulation_only",
    },
    {
        "scenario_id": "close_app",
        "category": "应用关闭",
        "instruction": "关闭已经完成使用的应用",
        "steps": ["确认目标应用在前台", "保存或确认不需要保存", "执行关闭操作", "检查应用窗口已消失"],
        "done_condition": "目标应用窗口不再显示",
        "execution_status": "simulation_only",
    },
]


def list_task_scenarios():
    """返回任务目录副本，避免调用方修改原始定义。"""
    return copy.deepcopy(TASK_SCENARIOS)


def get_task_scenario(scenario_id):
    """按编号读取一个任务类别。"""
    for scenario in TASK_SCENARIOS:
        if scenario["scenario_id"] == scenario_id:
            return copy.deepcopy(scenario)
    raise ValueError(f"未知任务类别：{scenario_id}")
