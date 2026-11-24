"""在 Kaggle 批量处理 WebArena、ScreenAgent 和 Mind2Web 训练数据。"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.week3_batch import split_and_report
from src.week3_dataset import normalize_mind2web, normalize_screenagent, preprocess


def clone(url, path):
    """仓库存在时不重复下载。"""
    if path.is_dir():
        print(f"已存在，跳过下载：{path}")
        return
    env = dict(os.environ)
    env["GIT_LFS_SKIP_SMUDGE"] = "1"  # 不下载无关的压缩权重或测试包。
    subprocess.run(["git", "clone", "--depth", "1", url, str(path)], check=True, env=env)


def write_screenagent(source_dir, output):
    files = sorted(source_dir.glob("**/*_translate.json"))
    files = [path for path in files if "_neg_" not in path.name]
    with output.open("w", encoding="utf-8") as stream:
        for path in files:
            record = json.loads(path.read_text(encoding="utf-8"))
            normalized = normalize_screenagent(record)
            # 同一个 session 会拆成多个轨迹文件，使用相对文件名保证每条记录编号唯一。
            relative_id = path.relative_to(source_dir).with_suffix("").as_posix().replace("/", "_")
            normalized["task_id"] = f"screenagent_{relative_id}"
            stream.write(json.dumps(normalized, ensure_ascii=False) + "\n")
    print(f"ScreenAgent：{len(files)} 条")


def write_mind2web(output, limit=0):
    """默认处理完整训练集；limit仅用于排查代码，正式运行保持0。"""
    from datasets import load_dataset
    dataset = load_dataset("osunlp/Mind2Web", split="train", streaming=True)
    count = 0
    with output.open("w", encoding="utf-8") as stream:
        for record in dataset:
            stream.write(json.dumps(normalize_mind2web(record), ensure_ascii=False) + "\n")
            count += 1
            if limit and count >= limit:
                break
            if count % 100 == 0:
                print(f"Mind2Web 已处理：{count} 条", flush=True)
    print(f"Mind2Web：{count} 条")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=Path("/kaggle/working/week3_data"))
    parser.add_argument("--mind2web-limit", type=int, default=0,
                        help="0表示完整训练集；正式验收必须使用0")
    args = parser.parse_args()
    if args.mind2web_limit < 0:
        parser.error("mind2web-limit不能小于0")
    sources = args.work_dir / "sources"
    processed = args.work_dir / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    screenagent = sources / "ScreenAgent"
    webarena = sources / "webarena"
    clone("https://github.com/niuzaisheng/ScreenAgent.git", screenagent)
    clone("https://github.com/web-arena-x/webarena.git", webarena)

    preprocess(webarena / "config_files/test.raw.json", processed / "webarena.jsonl", "webarena")
    write_screenagent(screenagent / "data/ScreenAgent/train", processed / "screenagent.jsonl")
    write_mind2web(processed / "mind2web.jsonl", args.mind2web_limit)
    report = split_and_report(sorted(processed.glob("*.jsonl")), args.work_dir / "splits")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
