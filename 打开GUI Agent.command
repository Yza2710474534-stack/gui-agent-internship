#!/bin/zsh

set -u

script_dir="${0:A:h}"
python_bin="$script_dir/.venv/bin/python"
runner="$script_dir/scripts/run_local_executor.py"
local_url="http://127.0.0.1:8765/"
health_url="http://127.0.0.1:8765/api/health"
executor_pid=""

cleanup_executor() {
  if [[ -n "$executor_pid" ]] && kill -0 "$executor_pid" 2>/dev/null; then
    kill "$executor_pid" 2>/dev/null
  fi
}

if curl --silent --fail --max-time 1 "$health_url" >/dev/null 2>&1; then
  open "$local_url"
  exit 0
fi

if [[ ! -x "$python_bin" ]]; then
  echo "未找到项目 Python 环境：$python_bin"
  echo "请先完成项目环境安装。"
  read -r "?按回车键关闭窗口。"
  exit 1
fi

if [[ ! -f "$runner" ]]; then
  echo "未找到本地执行器：$runner"
  read -r "?按回车键关闭窗口。"
  exit 1
fi

trap cleanup_executor EXIT INT TERM HUP

echo "正在启动 GUI Agent……"
"$python_bin" "$runner" &
executor_pid=$!

for attempt in {1..50}; do
  if curl --silent --fail --max-time 1 "$health_url" >/dev/null 2>&1; then
    open "$local_url"
    echo ""
    echo "GUI Agent 已打开。保持此窗口运行；按 Control-C 停止。"
    wait "$executor_pid"
    exit $?
  fi
  if ! kill -0 "$executor_pid" 2>/dev/null; then
    echo "本地执行器启动失败，请查看上方错误。"
    read -r "?按回车键关闭窗口。"
    exit 1
  fi
  sleep 0.2
done

echo "本地执行器启动超时。"
read -r "?按回车键关闭窗口。"
exit 1
