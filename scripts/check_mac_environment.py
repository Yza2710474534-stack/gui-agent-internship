from __future__ import annotations

import importlib
import importlib.metadata
import platform
import sys
from dataclasses import dataclass


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def package_check(import_name: str, distribution_name: str | None = None) -> Check:
    distribution_name = distribution_name or import_name
    try:
        importlib.import_module(import_name)
        version = importlib.metadata.version(distribution_name)
        return Check(distribution_name, True, version)
    except Exception as exc:  # Import errors often contain useful native-library details.
        return Check(distribution_name, False, f"{type(exc).__name__}: {exc}")


def check_torch_mps() -> Check:
    try:
        import torch

        built = torch.backends.mps.is_built()
        available = torch.backends.mps.is_available()
        if available:
            value = (torch.ones(4, device="mps") * 2).sum().item()
            return Check("PyTorch MPS", value == 8, f"built={built}, available={available}")
        return Check("PyTorch MPS", False, f"built={built}, available={available}")
    except Exception as exc:
        return Check("PyTorch MPS", False, f"{type(exc).__name__}: {exc}")


def check_screen_capture() -> Check:
    try:
        import numpy as np
        from mss import MSS

        with MSS() as capture:
            if len(capture.monitors) < 2:
                return Check(
                    "Screen capture",
                    False,
                    "no displays visible; run from a logged-in Terminal session",
                )
            monitor = capture.monitors[1]
            region = {
                "left": monitor["left"],
                "top": monitor["top"],
                "width": min(64, monitor["width"]),
                "height": min(64, monitor["height"]),
            }
            frame = np.asarray(capture.grab(region))
        return Check(
            "Screen capture",
            frame.size > 0,
            f"shape={tuple(frame.shape)}, pixel_std={float(frame.std()):.2f}",
        )
    except Exception as exc:
        return Check("Screen capture", False, f"{type(exc).__name__}: {exc}")


def check_gui_read_access() -> Check:
    try:
        import pyautogui

        width, height = pyautogui.size()
        x, y = pyautogui.position()
        return Check("GUI read access", width > 0 and height > 0, f"screen={width}x{height}, cursor=({x},{y})")
    except Exception as exc:
        return Check("GUI read access", False, f"{type(exc).__name__}: {exc}")


def check_accessibility_permission() -> Check:
    try:
        import ApplicationServices

        trusted = bool(ApplicationServices.AXIsProcessTrusted())
        detail = "granted" if trusted else "not granted for the current launcher"
        return Check("Accessibility", trusted, detail)
    except Exception as exc:
        return Check("Accessibility", False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    checks = [
        Check("Python", sys.version_info >= (3, 10), sys.version.split()[0]),
        Check("Architecture", platform.machine() == "arm64", platform.machine()),
        package_check("numpy"),
        package_check("pandas"),
        package_check("PIL", "Pillow"),
        package_check("cv2", "opencv-python"),
        package_check("mss"),
        package_check("pyautogui"),
        package_check("pynput"),
        package_check("torch"),
        package_check("easyocr"),
        check_torch_mps(),
        check_screen_capture(),
        check_gui_read_access(),
        check_accessibility_permission(),
    ]

    width = max(len(check.name) for check in checks)
    for check in checks:
        marker = "PASS" if check.ok else "FAIL"
        print(f"[{marker}] {check.name:<{width}}  {check.detail}")

    failures = [check.name for check in checks if not check.ok]
    if failures:
        print("\nFailed checks: " + ", ".join(failures))
        return 1
    print("\nAll core macOS environment checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
