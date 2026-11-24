"""统一模型接口：模拟模型、OpenAI 兼容 API 和本地 Ollama。"""

import base64
import json
import mimetypes
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class ModelCallError(RuntimeError):
    """模型接口无法正常返回结果。"""


def encode_image(image_path):
    """读取图片，返回 MIME 类型和 base64 内容。"""
    path = Path(image_path)
    if not path.is_file():
        raise ModelCallError(f"图片不存在：{path}")
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return mime_type, encoded


def _post_json(url, payload, headers=None, timeout=60, bypass_proxy=False):
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    try:
        if bypass_proxy:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            response_context = opener.open(request, timeout=timeout)
        else:
            response_context = urllib.request.urlopen(request, timeout=timeout)
        with response_context as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ModelCallError(f"模型请求失败：{exc}") from exc


def _task_from_prompt(prompt):
    marker = "用户任务："
    return prompt.split(marker, 1)[1].strip() if marker in prompt else prompt.strip()


def call_mock(prompt, image_path=None):
    """返回固定规则生成的 JSON，供离线开发和测试使用。"""
    if image_path:
        encode_image(image_path)
    task = _task_from_prompt(prompt)

    if "搜索" in task:
        keyword = task.split("搜索", 1)[1].strip(" ：:，,") or "目标关键词"
        steps = [
            "观察当前界面并确认浏览器位置",
            "打开浏览器并定位地址栏或搜索框",
            f"输入“{keyword}”并提交",
            "检查结果页是否出现相关内容",
        ]
        done_condition = f"页面中出现与“{keyword}”相关的搜索结果"
    elif "点击" in task:
        target = task.split("点击", 1)[1].strip(" ：:，,") or "目标控件"
        steps = [
            "观察当前界面",
            f"定位“{target}”的位置",
            f"点击“{target}”",
            "检查界面是否发生预期变化",
        ]
        done_condition = f'点击“{target}”后界面出现预期变化'
    else:
        steps = [
            "观察当前界面并识别可操作元素",
            f"执行任务：{task}",
            "检查界面结果是否符合任务要求",
        ]
        done_condition = "界面结果符合用户任务要求"

    return json.dumps(
        {"steps": steps, "done_condition": done_condition}, ensure_ascii=False
    )


def call_openai_compatible(prompt, model, base_url, api_key="", image_path=None):
    """调用采用 /v1/chat/completions 格式的云端或自建服务。"""
    if not model:
        raise ModelCallError("API 模式缺少模型名称")
    if not base_url:
        raise ModelCallError("API 模式缺少 base_url")

    content = prompt
    if image_path:
        mime_type, image_data = encode_image(image_path)
        content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
            },
        ]

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
    }
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    hostname = urllib.parse.urlparse(endpoint).hostname
    if hostname == "api.deepseek.com" and not api_key:
        raise ModelCallError("未读取到 DeepSeek API Key")
    result = _post_json(
        endpoint,
        payload,
        headers,
        bypass_proxy=hostname == "api.deepseek.com",
    )
    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelCallError("API 返回内容中缺少模型回答") from exc


def call_ollama(prompt, model, base_url="http://localhost:11434", image_path=None):
    """调用本机 Ollama；图片会按 Ollama REST API 要求转成 base64。"""
    if not model:
        raise ModelCallError("Ollama 模式缺少模型名称")
    message = {"role": "user", "content": prompt}
    if image_path:
        _, image_data = encode_image(image_path)
        message["images"] = [image_data]

    payload = {
        "model": model,
        "messages": [message],
        "stream": False,
        "format": "json",
    }
    result = _post_json(f"{base_url.rstrip('/')}/api/chat", payload)
    try:
        return result["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise ModelCallError("Ollama 返回内容中缺少模型回答") from exc


def call_model(prompt, provider="mock", model="", base_url="", api_key="", image_path=None):
    """统一入口。provider 可选 mock、api 或 ollama。"""
    if provider == "mock":
        return call_mock(prompt, image_path)
    if provider == "api":
        return call_openai_compatible(prompt, model, base_url, api_key, image_path)
    if provider == "ollama":
        return call_ollama(prompt, model, base_url or "http://localhost:11434", image_path)
    raise ModelCallError(f"不支持的模型类型：{provider}")
