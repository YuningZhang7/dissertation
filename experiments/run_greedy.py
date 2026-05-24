from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.greedy_agent import choose_greedy_action
from railways.game_state import GameState
from railways.rules import apply_action, describe_action


def main() -> None:
    state = GameState.from_files(
        PROJECT_ROOT / "data" / "toy_map.json",
        PROJECT_ROOT / "data" / "rules_config.json",
    )

    while not state.is_terminal():
        action = choose_greedy_action(state)
        print(f"Turn {state.player.turn}: {describe_action(action)}")
        apply_action(state, action)

    print()
    print("Greedy baseline complete")
    print(f"Score: {state.player.score}")
    print(f"Bonds: {state.player.bonds}")
    print(f"Final score: {state.final_score()}")
    print(f"Delivered goods: {state.player.delivered_goods_count}")


if __name__ == "__main__":
    main()
