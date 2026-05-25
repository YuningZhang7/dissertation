from __future__ import annotations

import csv
from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.greedy_delivery_agent import GreedyDeliveryAgent
from agents.greedy_expansion_agent import GreedyExpansionAgent
from agents.random_agent import RandomAgent
from experiments.run_experiments import run_batch
from experiments.simulation_runner import run_episode
from railways.environment import apply_action, get_legal_actions, reset_game


def test_random_agent_returns_legal_action() -> None:
    state = reset_game()
    agent = RandomAgent(seed=1)
    action = agent.choose_action(state)
    assert action in get_legal_actions(state)


def test_greedy_delivery_agent_returns_delivery_when_available() -> None:
    state = reset_game()
    assert apply_action(state, get_legal_actions(state)[0])[1]
    deliveries = [action for action in get_legal_actions(state) if action.action_type == "deliver_good"]
    if not deliveries:
        raise AssertionError("Expected a legal delivery after first build.")

    action = GreedyDeliveryAgent(seed=1).choose_action(state)
    assert action.action_type == "deliver_good"


def test_greedy_expansion_agent_returns_legal_action() -> None:
    state = reset_game()
    agent = GreedyExpansionAgent(seed=1)
    action = agent.choose_action(state)
    assert action in get_legal_actions(state)


def test_run_episode_returns_required_metrics() -> None:
    result = run_episode(GreedyDeliveryAgent(seed=2), seed=2, max_steps=200)
    required_keys = {
        "agent",
        "seed",
        "final_score",
        "raw_score",
        "bonds",
        "money",
        "deliveries",
        "built_edges",
        "major_line_bonus",
        "rail_baron_bonus",
        "operation_card_bonus",
        "empty_markers",
        "turns",
        "actions_taken",
        "runtime_seconds",
        "terminal",
    }
    assert required_keys.issubset(result)
    assert result["agent"] == "greedy_delivery"


def test_batch_runner_writes_csv() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output = Path(tmp_dir) / "agent_results.csv"
        results = run_batch("random", episodes=2, seed=5, output=output, max_steps=200)
        assert len(results) == 2
        assert output.exists()

        with output.open("r", newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        assert len(rows) == 2
        assert rows[0]["agent"] == "random"


def run_all() -> None:
    tests = [
        test_random_agent_returns_legal_action,
        test_greedy_delivery_agent_returns_delivery_when_available,
        test_greedy_expansion_agent_returns_legal_action,
        test_run_episode_returns_required_metrics,
        test_batch_runner_writes_csv,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} agent smoke tests passed.")


if __name__ == "__main__":
    run_all()
