from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
APP = ROOT / "app.py"

if not APP.exists():
    raise FileNotFoundError(f"Cannot find app.py at {APP}")

subprocess.run(
    [sys.executable, "-m", "streamlit", "run", str(APP)],
    check=True,
)
