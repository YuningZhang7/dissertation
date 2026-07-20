#!/bin/zsh
set -euo pipefail

pause_on_error() {
    echo
    echo "Launch failed. Review the message above."
    echo "Press any key to close this window."
    read -k 1 || true
    echo
}

finish() {
    local status=$?
    trap - EXIT
    if (( status != 0 )); then
        pause_on_error
    fi
    exit "$status"
}

trap finish EXIT

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "This launcher is intended for macOS." >&2
    false
fi

if [[ "$(uname -m)" != "arm64" ]]; then
    echo "Apple Silicon arm64 environment is required." >&2
    echo "The current shell or Python may be running under Rosetta." >&2
    false
fi

if [[ -x "/opt/homebrew/bin/python3" ]]; then
    PYTHON_BIN="/opt/homebrew/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
else
    echo "Apple Silicon Python 3.10 or newer was not found." >&2
    echo "Install an Apple Silicon Python with: brew install python" >&2
    false
fi

if ! "$PYTHON_BIN" -c 'import platform, sys; raise SystemExit(0 if sys.version_info >= (3, 10) and platform.machine() == "arm64" else 1)'; then
    echo "Apple Silicon Python 3.10 or newer is required." >&2
    "$PYTHON_BIN" -c 'import platform, sys; print(f"Detected Python: {sys.version.split()[0]}"); print(f"Detected architecture: {platform.machine()}")' || true
    echo "Install an Apple Silicon Python with: brew install python" >&2
    false
fi

VENV_DIR="$SCRIPT_DIR/.venv-macos-arm64"
if [[ -e "$VENV_DIR" && ! -x "$VENV_DIR/bin/python" ]]; then
    echo "The existing $VENV_DIR is not a usable Python virtual environment." >&2
    echo "Remove it manually, then launch again." >&2
    false
fi

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating Apple Silicon virtual environment..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

if ! "$VENV_DIR/bin/python" -c 'import platform, sys; raise SystemExit(0 if sys.version_info >= (3, 10) and platform.machine() == "arm64" else 1)'; then
    echo "The existing virtual environment is not Apple Silicon Python 3.10+." >&2
    echo "Remove $VENV_DIR manually, then launch again." >&2
    false
fi

REQ_FILE="$SCRIPT_DIR/requirements.txt"
if [[ ! -f "$REQ_FILE" ]]; then
    echo "Cannot find requirements.txt in $SCRIPT_DIR." >&2
    false
fi

REQ_HASH="$(shasum -a 256 "$REQ_FILE" | awk '{print $1}')"
STAMP_FILE="$VENV_DIR/.requirements.sha256"
INSTALLED_HASH=""
if [[ -f "$STAMP_FILE" ]]; then
    INSTALLED_HASH="$(<"$STAMP_FILE")"
fi

if [[ "$INSTALLED_HASH" != "$REQ_HASH" ]]; then
    echo "Installing application dependencies..."
    "$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
    "$VENV_DIR/bin/python" -m pip install -r "$REQ_FILE"
    print -r -- "$REQ_HASH" > "$STAMP_FILE"
else
    echo "Application dependencies are up to date."
fi

export MPLBACKEND=Agg
export PYTHONUNBUFFERED=1
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo "Starting Railways AI Simulator..."
"$VENV_DIR/bin/python" "$SCRIPT_DIR/run_app.py"
