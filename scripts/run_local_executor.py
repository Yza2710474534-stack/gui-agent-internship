"""启动 GUI Agent 本地网页桥接服务。"""

from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.local_bridge import main


if __name__ == "__main__":
    raise SystemExit(main())
