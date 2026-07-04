#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
fi

.venv/bin/python replay/animate_agent_episode.py \
  --map official_like \
  --agent objective_aware_greedy \
  --seed 42 \
  --max-steps 60 \
  --frame-mode events

echo
echo "Replay generated under outputs/agent_animations/."
