from __future__ import annotations

from pathlib import Path

import easyocr
import numpy as np
from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = PROJECT_ROOT / "artifacts" / "easyocr"


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Helvetica.ttc"),
    )
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def main() -> int:
    model_dir = MODEL_ROOT / "models"
    user_network_dir = MODEL_ROOT / "user_network"
    model_dir.mkdir(parents=True, exist_ok=True)
    user_network_dir.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (640, 160), "white")
    draw = ImageDraw.Draw(image)
    draw.text((40, 45), "HELLO GUI AGENT 123", fill="black", font=load_font(52))

    reader = easyocr.Reader(
        ["en"],
        gpu=False,
        model_storage_directory=str(model_dir),
        user_network_directory=str(user_network_dir),
        download_enabled=True,
        verbose=False,
    )
    results = reader.readtext(np.asarray(image), detail=0)
    recognized = " ".join(results).upper()
    print(f"recognized={recognized}")

    required_tokens = ("HELLO", "GUI", "AGENT", "123")
    missing = [token for token in required_tokens if token not in recognized]
    if missing:
        print("missing_tokens=" + ",".join(missing))
        return 1
    print("EasyOCR smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

