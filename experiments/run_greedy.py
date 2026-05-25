from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.greedy_delivery_agent import GreedyDeliveryAgent
from railways.environment import apply_action, is_terminal, reset_game
from railways.rules import describe_action


def main() -> None:
    state = reset_game()
    agent = GreedyDeliveryAgent(seed=0)

    steps = 0
    while not is_terminal(state) and steps < 500:
        action = agent.choose_action(state)
        print(f"Turn {state.turn} ({state.actions_remaining} actions): {describe_action(action)}")
        _, _, message = apply_action(state, action)
        print(f"  {message}")
        steps += 1

    print()
    print("Greedy baseline complete")
    print(f"Score: {state.player.score}")
    print(f"Bonds: {state.player.bonds}")
    print(f"Final score: {state.final_score()}")
    print(f"Delivered goods: {state.player.delivered_goods_count}")
    print(f"Empty city markers: {sum(1 for city in state.cities.values() if city.empty_marker)}")


if __name__ == "__main__":
    main()
