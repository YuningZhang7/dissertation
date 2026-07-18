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
from agents.objective_aware_greedy_agent import ObjectiveAwareGreedyAgent
from agents.presentation_lookahead_greedy_agent import PresentationLookaheadGreedyAgent
from agents.random_agent import RandomAgent
from agents.registry import AGENT_CLASSES, list_agent_names
from experiments.run_experiments import run_batch
from experiments.simulation_runner import run_episode
from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game


def test_random_agent_returns_legal_action() -> None:
    state = reset_game()
    agent = RandomAgent(seed=1)
    action = agent.choose_action(state)
    assert action in get_legal_actions(state)


def test_greedy_delivery_agent_returns_delivery_when_available() -> None:
    state = reset_game()
    assert apply_action(
        state,
        Action.build_track_segments(["A-H-1", "A-H-2"]),
    )[1]
    state.player.locomotive_level = 2
    deliveries = [
        action
        for action in get_legal_actions(state)
        if action.action_type == "deliver_good"
    ]
    if not deliveries:
        raise AssertionError("Expected a legal delivery after first build.")

    action = GreedyDeliveryAgent(seed=1).choose_action(state)
    assert action.action_type == "deliver_good"


def test_greedy_expansion_agent_returns_legal_action() -> None:
    state = reset_game()
    agent = GreedyExpansionAgent(seed=1)
    action = agent.choose_action(state)
    assert action in get_legal_actions(state)


def test_agents_do_not_choose_issue_bond() -> None:
    state = reset_game()
    agents = [
        RandomAgent(seed=1),
        GreedyDeliveryAgent(seed=1),
        GreedyExpansionAgent(seed=1),
        ObjectiveAwareGreedyAgent(seed=1),
        PresentationLookaheadGreedyAgent(seed=1),
    ]
    legal_actions = get_legal_actions(state)
    assert all(action.action_type != "issue_bond" for action in legal_actions)
    for agent in agents:
        assert agent.choose_action(state).action_type != "issue_bond"


def test_main_registry_exposes_registered_agents() -> None:
    expected = [
        "random",
        "greedy_delivery",
        "greedy_expansion",
        "objective_aware_greedy",
        "presentation_lookahead_greedy",
    ]
    assert list(AGENT_CLASSES) == expected
    assert list_agent_names() == expected


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
        "cards_enabled",
        "cards_selected",
        "cards_completed",
        "end_game_card_bonus",
        "financing_penalty",
        "score_delivery_raw",
        "score_major_line",
        "score_operation_cards",
        "score_end_game_cards",
        "score_financing_penalty",
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
        test_agents_do_not_choose_issue_bond,
        test_main_registry_exposes_registered_agents,
        test_run_episode_returns_required_metrics,
        test_batch_runner_writes_csv,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} agent smoke tests passed.")


if __name__ == "__main__":
    run_all()
