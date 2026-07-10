#!/usr/bin/env python3
"""ResellPro launcher — starts backend and opens the app in browser."""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    print("Starting ResellPro backend...")
    backend = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=ROOT / "backend",
    )
    time.sleep(3)
    print("Opening ResellPro at http://localhost:5173")
    print("Make sure to run 'npm run dev' in desktop/ folder")
    print("Or use start.bat on Windows for full auto-launch")
    webbrowser.open("http://localhost:5173")
    try:
        backend.wait()
    except KeyboardInterrupt:
        backend.terminate()


if __name__ == "__main__":
    main()
