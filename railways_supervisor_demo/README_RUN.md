# Railways Supervisor Demo

This package contains the Streamlit simulator and three simple agents:

- `random`
- `greedy_delivery`
- `greedy_expansion`

## Create a Virtual Environment

macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## Install Dependencies

```bash
python -m pip install -r requirements.txt
```

On macOS, use `python3` instead of `python` if required.

## Run the App

```bash
python run_app.py
```

Streamlit normally opens `http://localhost:8501`.

## Run the Smoke Test

```bash
python experiments/smoke_test_supervisor_demo.py
```
