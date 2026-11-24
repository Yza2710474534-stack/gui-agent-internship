# macOS development environment

This project uses a local virtual environment for desktop capture and control.
Kaggle remains the preferred environment for CUDA training and larger model jobs.

## Activate the environment

```bash
cd "/Users/ziang/Documents/ChatGPT/New project"
source .venv/bin/activate
```

## Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-mac.txt
python -m pip install -r requirements-ocr.txt
```

## Verify

```bash
python scripts/check_mac_environment.py
```

The verification script only reads the current cursor position and captures a
small 64 x 64 pixel region. It never moves the cursor, types, or clicks.

## Required macOS permissions

Open **System Settings > Privacy & Security** and grant the terminal application
used to start Python:

- **Screen & System Audio Recording** for screenshots.
- **Accessibility** for future mouse and keyboard control.

Quit and reopen the terminal after changing either permission. Keep PyAutoGUI's
corner fail-safe enabled in all automation code.

## Optional system tools

Apple Command Line Tools are still recommended for system `git`, compilers, and
native Python packages. Install them manually with:

```bash
xcode-select --install
```

