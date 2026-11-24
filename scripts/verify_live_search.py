"""用截图和 OCR JSON 复核真实搜索任务，不操作鼠标和键盘。"""

import argparse
import json
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from src.week3_runtime import verify_search_results_ocr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("ocr", type=Path)
    parser.add_argument("--query", default="GUI Agent")
    parser.add_argument("--output", type=Path,
                        default=Path("output/week3/live_search_verification.json"))
    args = parser.parse_args()

    result = verify_search_results_ocr(args.image, args.ocr, args.query)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"完成判断：{'通过' if result['success'] else '未通过'}")
    print(f"搜索框证据：{result.get('evidence', {}).get('query_evidence', [])}")
    print(f"结果证据：{result.get('evidence', {}).get('result_evidence', [])}")
    print(f"验证结果：{args.output.resolve()}")
    raise SystemExit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
