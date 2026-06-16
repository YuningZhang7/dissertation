from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.card_aware_greedy_agent import CardAwareGreedyAgent
from agents.mcts_agent import MCTSAgent
from experiments.simulation_runner import run_episode
from railways.actions import Action
from railways.environment import (
    DEFAULT_CARDS_PATH,
    apply_action,
    get_legal_actions,
    reset_game,
)


def test_card_aware_greedy_returns_legal_action_without_cards() -> None:
    state = reset_game(card_path=None)
    action = CardAwareGreedyAgent(seed=0).choose_action(state)
    assert action in get_legal_actions(state)


def test_card_aware_greedy_returns_legal_action_with_cards() -> None:
    state = reset_game(card_path=DEFAULT_CARDS_PATH)
    action = CardAwareGreedyAgent(seed=0).choose_action(state)
    assert action in get_legal_actions(state)


def test_card_aware_greedy_selects_card_in_card_enabled_episode() -> None:
    result = run_episode(
        CardAwareGreedyAgent(seed=0),
        seed=0,
        max_steps=100,
        card_path=DEFAULT_CARDS_PATH,
    )
    assert result["invalid_actions"] == 0
    assert result["cards_selected"] >= 1


def test_card_aware_greedy_run_episode_has_zero_invalid_actions() -> None:
    for card_path in (None, DEFAULT_CARDS_PATH):
        result = run_episode(
            CardAwareGreedyAgent(seed=1),
            seed=1,
            max_steps=100,
            card_path=card_path,
        )
        assert result["invalid_actions"] == 0


def test_mcts_card_aware_rollout_runs_with_cards_enabled() -> None:
    result = run_episode(
        MCTSAgent(
            seed=0,
            iterations=5,
            rollout_depth_limit=20,
            rollout_policy="card_aware",
        ),
        seed=0,
        max_steps=100,
        card_path=DEFAULT_CARDS_PATH,
    )
    assert result["invalid_actions"] == 0


def test_existing_mcts_rollout_policies_still_work() -> None:
    for policy in ("random", "greedy_delivery"):
        result = run_episode(
            MCTSAgent(
                seed=2,
                iterations=5,
                rollout_depth_limit=20,
                rollout_policy=policy,
            ),
            seed=2,
            max_steps=100,
            card_path=DEFAULT_CARDS_PATH,
        )
        assert result["invalid_actions"] == 0


def test_card_aware_greedy_prefers_matching_active_delivery_objective() -> None:
    state = reset_game(card_path=DEFAULT_CARDS_PATH)
    assert apply_action(state, Action.select_operation_card("deliver_red_1"))[1]
    assert apply_action(state, Action.build_track("A-B"))[1]

    action = CardAwareGreedyAgent(seed=0).choose_action(state)

    assert action in get_legal_actions(state)
    assert action.action_type == "deliver_good"
    assert action.params["good_color"] == "red"
    assert action.params["source"] == "B"
    assert action.params["target"] == "A"


def run_all() -> None:
    tests = [
        test_card_aware_greedy_returns_legal_action_without_cards,
        test_card_aware_greedy_returns_legal_action_with_cards,
        test_card_aware_greedy_selects_card_in_card_enabled_episode,
        test_card_aware_greedy_run_episode_has_zero_invalid_actions,
        test_mcts_card_aware_rollout_runs_with_cards_enabled,
        test_existing_mcts_rollout_policies_still_work,
        test_card_aware_greedy_prefers_matching_active_delivery_objective,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} card-aware agent smoke tests passed.")


if __name__ == "__main__":
    run_all()
