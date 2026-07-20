# macOS Apple Silicon Setup

## Requirements

- Apple Silicon Mac running macOS
- Apple Silicon Python 3.10 or newer
- An internet connection for the first dependency installation

If Python is not installed, Homebrew users can install an ARM-native version with:

```bash
brew install python
```

## Launch

In Finder, double-click:

```text
Launch Railways AI.command
```

The first launch creates `.venv-macos-arm64`, installs the full contents of
`requirements.txt`, and opens the Streamlit application in a browser. The first
launch is therefore slower than subsequent launches. Dependencies are installed
again only when `requirements.txt` changes.

## Permission issue

If the launcher does not have execute permission, open Terminal in the repository
directory and run:

```bash
chmod +x "Launch Railways AI.command"
```

## Gatekeeper

If macOS blocks the launcher, right-click `Launch Railways AI.command`, choose
**Open**, then choose **Open** again. Do not disable macOS security features.

If the downloaded repository has a quarantine attribute and the right-click method
does not resolve it, remove that attribute from this file only:

```bash
xattr -d com.apple.quarantine "Launch Railways AI.command"
```

## Architecture check

Run:

```bash
uname -m
python3 -c "import platform; print(platform.machine())"
```

Both commands should print `arm64`. The launcher stops instead of creating an x86
virtual environment when the shell or Python is running under Rosetta.

## Manual fallback

The same application can be started without the Finder launcher:

```bash
python3 -m venv .venv-macos-arm64
source .venv-macos-arm64/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
export MPLBACKEND=Agg
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
python run_app.py
```

The launcher never deletes an existing virtual environment. If it reports that
`.venv-macos-arm64` has the wrong architecture or is invalid, remove that directory
manually only after confirming that it contains no files you need, then launch again.
