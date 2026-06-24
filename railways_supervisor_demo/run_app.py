from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
APP = ROOT / "app.py"


def main() -> None:
    if not APP.exists():
        raise FileNotFoundError(f"Cannot find app.py at {APP}")

    if _running_under_streamlit():
        from app import main as app_main

        app_main()
        return

    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(APP)],
        check=True,
    )


def _running_under_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return False
    return get_script_run_ctx() is not None


if __name__ == "__main__":
    main()
