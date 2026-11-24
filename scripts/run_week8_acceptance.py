"""固定验收入口；只有显式 --live 才运行真实桌面点击。"""

import argparse
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = Path(os.environ.get("GUI_AGENT_NODE", "/Users/ziang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="在受控 Chrome 页面执行真实单次点击")
    args = parser.parse_args()
    env = {**os.environ, "GUI_AGENT_E2E_OUTPUT": "output/week8/browser_regression"}
    commands = [
        [str(ROOT / ".venv/bin/python"), "scripts/record_week8_regression.py"],
        [str(NODE), "scripts/run_week7_browser_e2e.mjs"],
    ]
    if args.live:
        commands.append([str(NODE), "scripts/run_week8_live_e2e.mjs"])
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, env=env, check=False)
        if result.returncode:
            return result.returncode
    output = ROOT / "output/week8/acceptance_summary.json"
    regression = json.loads((ROOT / "output/week8/verification/regression_summary.json").read_text())
    browser = json.loads((ROOT / "output/week8/browser_regression/results.json").read_text())
    summary = {"unit_and_integration_tests": regression["tests_run"],
               "browser_regression_scenarios": len(browser["cases"]),
               "viewport_widths": len(browser["widths"]),
               "live_run_this_invocation": args.live,
               "passed": regression["passed"] and browser["result"] == "passed"}
    if args.live:
        live = json.loads((ROOT / "output/week8/live_e2e/results.json").read_text())
        summary.update(live_suite_scenarios=len(live["cases"]),
                       passed=summary["passed"] and live["result"] == "passed")
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
