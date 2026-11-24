import json
import tempfile
import unittest
from pathlib import Path

from src.week4_realtime import run_realtime_loop, validate_action


def run_in_temp(**kwargs):
    directory = tempfile.TemporaryDirectory()
    log_path = Path(directory.name) / "events.jsonl"
    result = run_realtime_loop(log_path=log_path, **kwargs)
    logs = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    directory.cleanup()
    return result, logs


class Week4RealtimeTests(unittest.TestCase):
    def test_preview_never_calls_execute(self):
        calls = []
        result, logs = run_in_temp(
            task="搜索 GUI Agent",
            observe=lambda state: {"image_path": "screen.png", "items": []},
            decide=lambda state, observation: {"kind": "action",
                                                "action": {"type": "click", "x": 10, "y": 20}},
            execute=lambda action: calls.append(action),
            verify=lambda *args: True,
            verify_done=lambda *args: True,
            mode="preview",
        )
        self.assertEqual(result["status"], "preview_ready")
        self.assertEqual(calls, [])
        self.assertEqual(logs[-1]["event"], "action_proposed")

    def test_live_runs_two_actions_then_done(self):
        executed = []
        observed_cycles = []

        def observe(state):
            observed_cycles.append(state["cycle"])
            return {"screen": state["cycle"]}

        def decide(state, observation):
            return {"kind": "done"} if state["action_count"] == 2 else {
                "kind": "action", "action": {"type": "wait", "seconds": 0}
            }

        result, logs = run_in_temp(
            task="连续执行两步",
            observe=observe,
            decide=decide,
            execute=lambda action: executed.append(action) or {"ok": True},
            verify=lambda *args: {"success": True, "message": "画面已更新"},
            verify_done=lambda *args: {"success": True, "message": "结果已确认"},
            mode="live",
        )
        self.assertEqual(result["status"], "done")
        self.assertEqual(result["action_count"], 2)
        self.assertEqual(len(executed), 2)
        self.assertEqual(observed_cycles, [1, 1, 2, 2, 3])
        self.assertEqual(logs[-1]["event"], "loop_completed")

    def test_failed_verification_stops_live_loop(self):
        result, _ = run_in_temp(
            task="验证失败",
            observe=lambda state: {},
            decide=lambda state, observation: {"kind": "action",
                                                "action": {"type": "click", "x": 1, "y": 2}},
            execute=lambda action: {"clicked": True},
            verify=lambda *args: {"success": False, "message": "目标没有出现"},
            verify_done=lambda *args: True,
            mode="live",
        )
        self.assertEqual(result["status"], "action_failed")
        self.assertEqual(result["action_count"], 1)

    def test_action_failure_can_retry_then_recover(self):
        checks = {"count": 0}

        def verify(*args):
            checks["count"] += 1
            return {"success": checks["count"] == 2, "message": "第二次观察通过"}

        def decide(state, observation):
            return {"kind": "done"} if state["action_count"] >= 2 else {
                "kind": "action", "action": {"type": "wait", "seconds": 0}
            }

        with tempfile.TemporaryDirectory() as directory:
            output = run_realtime_loop(
                "重试任务", lambda state: {"cycle": state["cycle"]}, decide,
                lambda action: {}, verify, lambda *args: True,
                Path(directory) / "retry.jsonl", mode="live", max_action_retries=1,
            )
        self.assertEqual(output["status"], "done")
        self.assertEqual(output["action_count"], 2)

    def test_timeout_stops_before_observation(self):
        calls = []
        result, logs = run_in_temp(
            task="超时任务",
            observe=lambda state: calls.append(state["cycle"]) or {},
            decide=lambda state, observation: {"kind": "done"},
            execute=lambda action: None,
            verify=lambda *args: True,
            verify_done=lambda *args: True,
            mode="live",
            max_duration_seconds=0,
        )
        self.assertEqual(result["status"], "timed_out")
        self.assertEqual(calls, [])
        self.assertEqual(logs[-1]["event"], "loop_timed_out")

    def test_stop_decision_is_recorded(self):
        result, logs = run_in_temp(
            task="安全停止",
            observe=lambda state: {},
            decide=lambda state, observation: {"kind": "stop", "reason": "用户要求暂停"},
            execute=lambda action: None,
            verify=lambda *args: True,
            verify_done=lambda *args: True,
        )
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["stop_reason"], "用户要求暂停")
        self.assertEqual(logs[-1]["event"], "loop_stopped")

    def test_done_requires_completion_verification(self):
        result, _ = run_in_temp(
            task="完成条件不足",
            observe=lambda state: {},
            decide=lambda state, observation: {"kind": "done"},
            execute=lambda action: None,
            verify=lambda *args: True,
            verify_done=lambda *args: {"success": False, "message": "缺少结果证据"},
        )
        self.assertEqual(result["status"], "completion_failed")

    def test_action_validation_rejects_unknown_and_chinese_input(self):
        with self.assertRaises(ValueError):
            validate_action({"type": "shell", "command": "rm -rf"})
        with self.assertRaises(ValueError):
            validate_action({"type": "type_text", "text": "中文"})

    def test_action_validation_rejects_out_of_range_wait(self):
        with self.assertRaises(ValueError):
            validate_action({"type": "wait", "seconds": 31})

    def test_action_limit_stops_before_extra_execution(self):
        calls = []
        result, _ = run_in_temp(
            task="动作上限",
            observe=lambda state: {},
            decide=lambda state, observation: {"kind": "action",
                                                "action": {"type": "wait", "seconds": 0}},
            execute=lambda action: calls.append(action),
            verify=lambda *args: True,
            verify_done=lambda *args: True,
            mode="live",
            max_actions=1,
            max_cycles=3,
        )
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["action_count"], 1)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
