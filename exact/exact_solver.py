from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any

from railways.actions import Action
from railways.environment import apply_action, copy_state, final_score, get_legal_actions, is_terminal
from railways.game_state import GameState
from railways.rules import describe_action


@dataclass(frozen=True)
class ExactSolverSettings:
    # Reserved for future safe/admissible pruning. It is not used in Phase 3D.
    branch_and_bound: bool = False
    max_expanded_states: int | None = None


@dataclass
class ExactSolverResult:
    optimal_score: int
    optimal_actions: list[Action]
    expanded_states: int
    memo_hits: int
    pruned_states: int
    runtime_seconds: float
    settings: ExactSolverSettings


class ExactSolver:
    """Memoised exhaustive search over the existing legal-action interface."""

    def __init__(self, settings: ExactSolverSettings | None = None) -> None:
        self.settings = settings or ExactSolverSettings()
        self.memo: dict[tuple[Any, ...], tuple[int, tuple[Action, ...]]] = {}
        self.expanded_states = 0
        self.memo_hits = 0
        self.pruned_states = 0

    def solve(self, state: GameState) -> ExactSolverResult:
        self.memo.clear()
        self.expanded_states = 0
        self.memo_hits = 0
        self.pruned_states = 0

        start_time = time.perf_counter()
        score, actions = self._solve_state(copy_state(state))
        runtime_seconds = time.perf_counter() - start_time
        return ExactSolverResult(
            optimal_score=score,
            optimal_actions=list(actions),
            expanded_states=self.expanded_states,
            memo_hits=self.memo_hits,
            pruned_states=self.pruned_states,
            runtime_seconds=runtime_seconds,
            settings=self.settings,
        )

    def _solve_state(self, state: GameState) -> tuple[int, tuple[Action, ...]]:
        if is_terminal(state):
            return final_score(state), ()

        key = canonical_state_key(state)
        if key in self.memo:
            self.memo_hits += 1
            return self.memo[key]

        self.expanded_states += 1
        if (
            self.settings.max_expanded_states is not None
            and self.expanded_states > self.settings.max_expanded_states
        ):
            raise RuntimeError(
                f"Exact solver exceeded max_expanded_states="
                f"{self.settings.max_expanded_states}."
            )

        best_score = float("-inf")
        best_actions: tuple[Action, ...] = ()
        legal_actions = sorted(get_legal_actions(state), key=action_sort_key)

        if not legal_actions:
            result = (final_score(state), ())
            self.memo[key] = result
            return result

        for action in legal_actions:
            next_state = copy_state(state)
            _, success, _ = apply_action(next_state, action)
            if not success:
                continue

            score, suffix = self._solve_state(next_state)
            if score > best_score:
                best_score = score
                best_actions = (action, *suffix)

        if best_score == float("-inf"):
            result = (final_score(state), ())
        else:
            result = (int(best_score), best_actions)
        self.memo[key] = result
        return result


def canonical_state_key(state: GameState) -> tuple[Any, ...]:
    """Return a hashable state key containing rule-relevant mutable state."""
    city_state = tuple(
        sorted(
            (
                city_id,
                city.demand_color,
                tuple(city.goods),
                city.is_gray,
                city.is_urbanized,
                city.empty_marker,
            )
            for city_id, city in state.cities.items()
        )
    )
    edge_state = tuple(
        sorted(
            (edge_id, edge.built, edge.owner)
            for edge_id, edge in state.edges.items()
        )
    )
    major_line_state = tuple(
        sorted(
            (line_id, line.claimed)
            for line_id, line in state.major_lines.items()
        )
    )
    rail_baron_state = (
        state.active_rail_baron_objective_id,
        tuple(
            sorted(
                (objective_id, objective.claimed)
                for objective_id, objective in state.rail_baron_objectives.items()
            )
        ),
    )
    player_state = (
        state.player.money,
        state.player.score,
        state.player.bonds,
        state.player.locomotive_level,
        state.player.delivered_goods_count,
        tuple(sorted(state.player.built_edges)),
        state.player.major_line_bonus,
        state.player.rail_baron_bonus,
        state.player.rail_baron_objectives_completed,
        state.player.operation_card_bonus,
        tuple(state.player.owned_operation_cards),
        tuple(
            sorted(
                (
                    card_id,
                    card_state.status,
                    card_state.progress,
                    card_state.awarded_points,
                )
                for card_id, card_state in state.player.active_operation_cards.items()
            )
        ),
        tuple(sorted(state.player.completed_operation_cards)),
    )
    card_state = (
        tuple(sorted(state.operation_cards)),
        tuple(state.available_operation_cards),
    )
    return (
        state.turn,
        state.phase,
        state.actions_remaining,
        state.end_triggered,
        state.extra_turns_remaining,
        player_state,
        city_state,
        edge_state,
        major_line_state,
        rail_baron_state,
        card_state,
    )


def action_sort_key(action: Action) -> tuple[Any, ...]:
    return (action.action_type, _freeze_value(action.params))


def action_to_dict(action: Action) -> dict[str, Any]:
    return {
        "action_type": action.action_type,
        "params": action.params,
        "description": describe_action(action),
    }


def action_from_dict(data: dict[str, Any]) -> Action:
    return Action(str(data["action_type"]), dict(data.get("params", {})))


def replay_actions(initial_state: GameState, actions: list[Action]) -> tuple[GameState, bool, str]:
    state = copy_state(initial_state)
    for index, action in enumerate(actions, start=1):
        if action not in get_legal_actions(state):
            return state, False, f"Action {index} is not legal: {describe_action(action)}"
        _, success, message = apply_action(state, action)
        if not success:
            return state, False, f"Action {index} failed: {message}"
    return state, True, "Replay succeeded."


def result_to_dict(
    result: ExactSolverResult,
    map_path: str | Path,
    config_path: str | Path,
) -> dict[str, Any]:
    return {
        "map": Path(map_path).stem,
        "config": Path(config_path).stem,
        "optimal_final_score": result.optimal_score,
        "optimal_action_sequence": [
            action_to_dict(action) for action in result.optimal_actions
        ],
        "optimal_action_count": len(result.optimal_actions),
        "expanded_states": result.expanded_states,
        "memo_hits": result.memo_hits,
        "pruned_states": result.pruned_states,
        "runtime_seconds": result.runtime_seconds,
        "solver_settings": {
            "branch_and_bound": result.settings.branch_and_bound,
            "max_expanded_states": result.settings.max_expanded_states,
        },
    }


def _freeze_value(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple(sorted((key, _freeze_value(item)) for key, item in value.items()))
    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set):
        return tuple(sorted(_freeze_value(item) for item in value))
    return value
