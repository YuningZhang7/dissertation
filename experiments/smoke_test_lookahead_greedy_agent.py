from __future__ import annotations

from pathlib import Path
import random
import sys
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import agents.lookahead_greedy_agent as lookahead_module
from agents.lookahead_greedy_agent import CandidateAction, LookaheadGreedyAgent
from agents.registry import create_agent, list_agent_names
from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, is_terminal, reset_game


MAP_PATH = PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
CONFIG_PATH = PROJECT_ROOT / "data" / "official_single_player_rules_config.json"


def test_agent_is_registered() -> None:
    assert "lookahead_greedy" in list_agent_names()
    agent = create_agent("lookahead_greedy", seed=42)
    assert isinstance(agent, LookaheadGreedyAgent)


def test_agent_returns_legal_initial_action() -> None:
    random.seed(42)
    state = reset_game(MAP_PATH, CONFIG_PATH)
    action = create_agent("lookahead_greedy", seed=42).choose_action(state)
    assert action in get_legal_actions(state)


def test_agent_runs_several_steps_without_error() -> None:
    trace = _run_trace(max_steps=10)
    assert len(trace) == 10
    assert all(row["legal"] for row in trace)
    assert all(row["success"] for row in trace)


def test_early_game_urbanize_is_conservative() -> None:
    trace = _run_trace(max_steps=20)
    urbanize_count = sum(row["action_type"] == "urbanize" for row in trace)
    assert urbanize_count <= 1, trace


def test_no_action_returned_outside_legal_action_set() -> None:
    trace = _run_trace(max_steps=35)
    assert all(row["legal"] for row in trace)


def test_delivery_candidates_use_full_score_at_root_and_rollout() -> None:
    deliveries = [
        Action.deliver_good("A", "B", "red", [f"route-{index}"])
        for index in range(5)
    ]
    scores = {
        deliveries[0]: 10.0,
        deliveries[1]: 80.0,
        deliveries[2]: 30.0,
        deliveries[3]: 50.0,
        deliveries[4]: 100.0,
    }

    with patch.object(
        lookahead_module,
        "_score_delivery_action",
        side_effect=lambda _state, action: scores[action],
    ):
        root = lookahead_module._candidate_actions(object(), deliveries)
        rollout = lookahead_module._rollout_candidate_actions(object(), deliveries)

    assert [item.action for item in root] == [
        deliveries[4],
        deliveries[1],
        deliveries[3],
        deliveries[2],
    ]
    assert [item.action for item in rollout] == [deliveries[4], deliveries[1]]
    assert root[0].priority_score == rollout[0].priority_score == 100.0


def test_build_candidates_use_full_score_and_rollout_budget() -> None:
    builds = [Action.build_track_segments([f"segment-{index}"]) for index in range(5)]
    scores = {
        builds[0]: 20.0,
        builds[1]: 70.0,
        builds[2]: 10.0,
        builds[3]: 90.0,
        builds[4]: 50.0,
    }

    with patch.object(
        lookahead_module,
        "_score_build_action",
        side_effect=lambda _state, action: scores[action],
    ):
        root = lookahead_module._candidate_actions(object(), builds)
        rollout = lookahead_module._rollout_candidate_actions(object(), builds)

    assert [item.action for item in root] == [
        builds[3],
        builds[1],
        builds[4],
        builds[0],
    ]
    assert [item.action for item in rollout] == [builds[3], builds[1], builds[4]]
    assert root[0].priority_score == rollout[0].priority_score == 90.0


def test_upgrade_candidates_share_full_score() -> None:
    upgrade = Action.upgrade_engine()
    with patch.object(lookahead_module, "_score_upgrade_action", return_value=42.0):
        root = lookahead_module._candidate_actions(object(), [upgrade])
        rollout = lookahead_module._rollout_candidate_actions(object(), [upgrade])

    assert root == rollout == [CandidateAction(upgrade, upgrade, 42.0)]


def test_rollout_keeps_only_five_highest_scored_candidates() -> None:
    deliveries = [
        Action.deliver_good("A", "B", "red", [f"route-{index}"])
        for index in range(2)
    ]
    builds = [Action.build_track_segments([f"segment-{index}"]) for index in range(3)]
    upgrade = Action.upgrade_engine()
    actions = [*deliveries, *builds, upgrade]

    with (
        patch.object(lookahead_module, "_score_delivery_action", return_value=100.0),
        patch.object(lookahead_module, "_score_build_action", return_value=80.0),
        patch.object(lookahead_module, "_score_upgrade_action", return_value=10.0),
    ):
        rollout = lookahead_module._rollout_candidate_actions(object(), actions)

    assert len(rollout) == 5
    assert upgrade not in [item.action for item in rollout]


def test_rollout_reuses_candidate_priority_score() -> None:
    action = Action.pass_action()
    candidate = CandidateAction(action, action, 123.0)
    state = reset_game(MAP_PATH, CONFIG_PATH)

    with (
        patch.object(
            lookahead_module,
            "_rollout_candidate_actions",
            return_value=[candidate],
        ),
        patch.object(lookahead_module, "_simulate_action", return_value=(state, True)),
        patch.object(lookahead_module, "_evaluate_state", return_value=0.0),
    ):
        assert lookahead_module._rollout_value(state, 1) == 123.0

    assert not hasattr(lookahead_module, "_score_action_immediate")


def test_urbanize_candidate_scope_is_identical_at_root_and_rollout() -> None:
    delivery = Action(
        "deliver_good",
        {"source": "A", "target": "B", "good_color": "red", "score": 4},
    )
    urbanize = Action.urbanize("gray-city", "blue")
    observed_high_value_flags: list[bool] = []

    def fake_urbanize_candidates(
        _state: object,
        _actions: list[Action],
        *,
        high_value_delivery_available: bool,
    ) -> list[CandidateAction]:
        observed_high_value_flags.append(high_value_delivery_available)
        return [CandidateAction(urbanize, urbanize, 77.0, direct_new_deliveries=1)]

    with (
        patch.object(lookahead_module, "_score_delivery_action", return_value=10.0),
        patch.object(
            lookahead_module,
            "_urbanize_candidates",
            side_effect=fake_urbanize_candidates,
        ),
    ):
        root = lookahead_module._candidate_actions(object(), [delivery, urbanize])
        rollout = lookahead_module._rollout_candidate_actions(
            object(), [delivery, urbanize]
        )

    assert observed_high_value_flags == [True, True]
    assert next(item for item in root if item.action == urbanize).priority_score == 77.0
    assert next(item for item in rollout if item.action == urbanize).priority_score == 77.0


def test_choose_action_is_deterministic_and_does_not_mutate_input() -> None:
    random.seed(42)
    state = reset_game(MAP_PATH, CONFIG_PATH)
    snapshot = state.copy()
    first = create_agent("lookahead_greedy", seed=42).choose_action(state)
    second = create_agent("lookahead_greedy", seed=42).choose_action(state)

    assert first == second
    assert first in get_legal_actions(state)
    assert state.__dict__ == snapshot.__dict__


def _run_trace(max_steps: int, seed: int = 42) -> list[dict[str, object]]:
    random.seed(seed)
    state = reset_game(MAP_PATH, CONFIG_PATH)
    agent = create_agent("lookahead_greedy", seed=seed)
    trace: list[dict[str, object]] = []
    for step in range(1, max_steps + 1):
        if is_terminal(state):
            break
        legal_actions = get_legal_actions(state)
        action = agent.choose_action(state)
        legal = action in legal_actions
        _, success, message = apply_action(state, action)
        trace.append(
            {
                "step": step,
                "action_type": action.action_type,
                "legal": legal,
                "success": success,
                "message": message,
            }
        )
    return trace


def run_all() -> None:
    tests = [
        test_agent_is_registered,
        test_agent_returns_legal_initial_action,
        test_agent_runs_several_steps_without_error,
        test_early_game_urbanize_is_conservative,
        test_no_action_returned_outside_legal_action_set,
        test_delivery_candidates_use_full_score_at_root_and_rollout,
        test_build_candidates_use_full_score_and_rollout_budget,
        test_upgrade_candidates_share_full_score,
        test_rollout_keeps_only_five_highest_scored_candidates,
        test_rollout_reuses_candidate_priority_score,
        test_urbanize_candidate_scope_is_identical_at_root_and_rollout,
        test_choose_action_is_deterministic_and_does_not_mutate_input,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} lookahead greedy smoke tests passed.")


if __name__ == "__main__":
    run_all()
