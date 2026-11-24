"""第四周第四天：浏览器搜索的逐步观察验证和最终完成条件。"""

from pathlib import Path

try:
    from .week3_runtime import verify_search_results_ocr
except ImportError:
    from week3_runtime import verify_search_results_ocr


def verify_post_action_observation(_state, observation, _action, _execution):
    """确认动作后已经重新取得可追溯的截图和 OCR 证据。"""
    if not isinstance(observation, dict):
        return {"success": False, "message": "动作后观察结果不是字典"}
    image = observation.get("image")
    ocr = observation.get("ocr")
    if not image or not ocr:
        return {"success": False, "message": "动作后缺少截图或 OCR 证据"}
    if not Path(image).is_file() or not Path(ocr).is_file():
        return {"success": False, "message": "动作后截图或 OCR 文件不存在"}
    return {
        "success": True,
        "message": "动作后截图和 OCR 证据已保存",
        "evidence": {"image": str(Path(image).resolve()), "ocr": str(Path(ocr).resolve())},
    }


def verify_browser_search_observation(observation, query):
    """用当前观察中的截图和 OCR 判断浏览器搜索是否完成。"""
    if not isinstance(query, str) or not query.strip():
        return {"success": False, "message": "搜索关键词不能为空"}
    if not isinstance(observation, dict):
        return {"success": False, "message": "观察结果不是字典"}
    image = observation.get("image")
    ocr = observation.get("ocr")
    if not image or not ocr:
        return {"success": False, "message": "观察结果缺少截图或 OCR 路径"}
    return verify_search_results_ocr(image, ocr, query)


def make_browser_search_completion(query):
    """返回可直接传入 run_realtime_loop 的完成验证函数。"""
    def verify_done(_state, observation):
        return verify_browser_search_observation(observation, query)

    return verify_done

