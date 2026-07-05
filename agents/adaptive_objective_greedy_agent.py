from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from agents.base_agent import BaseAgent
from agents.objective_aware_greedy_agent import (
    _action_sort_key,
    _completed_network_city_ids,
    _distance_reduction,
    _first_action,
    _goods_demand_potential,
    _rail_baron_remaining_distance,
    _remaining_distance,
    _segment_ids,
    _upgrade_frontier_count,
)
from railways.actions import Action
from railways.environment import apply_action, get_legal_actions
from railways.game_state import GameState
from railways.rules import get_legal_deliveries


MINIMUM_USEFUL_SCORE = 1.0
LOOKAHEAD_DEPTH = 1
LOOKAHEAD_TOP_K = 5
LOOKAHEAD_DISCOUNT = 0.4
LOOKAHEAD_MAX_CANDIDATES = 30
# The one-ply implementation is available for controlled comparisons. It is off
# by default so expanded-map baseline runs remain lightweight.
LOOKAHEAD_ENABLED = False


@dataclass(frozen=True)
class AdaptiveWeights:
    delivery_score: float
    rail_baron_claim: float
    rail_baron_roi: float
    major_line_claim: float
    major_line_roi: float
    route_completion: float
    network_expansion: float
    delivery_value: float
    debt_penalty: float
    construction_cost: float
    incomplete_route_penalty: float
    upgrade_value: float


PHASE_WEIGHTS = {
    "early": AdaptiveWeights(30, 1200, 160, 800, 60, 200, 45, 50, 25, 2, 30, 30),
    "mid": AdaptiveWeights(45, 1400, 110, 1000, 70, 240, 25, 70, 35, 2.5, 40, 45),
    "late": AdaptiveWeights(70, 1700, 70, 1300, 45, 120, 5, 90, 55, 4, 60, 55),
}


class AdaptiveObjectiveGreedyAgent(BaseAgent):
    """Phase-aware deterministic heuristic with bounded one-ply lookahead."""

    name = "adaptive_objective_greedy"

    def choose_action(self, state: GameState) -> Action:
        legal_actions = get_legal_actions(state)
        if not legal_actions:
            return Action.pass_action()

        candidates = _candidate_actions(legal_actions)
        weights = _weights_for_state(state)
        before = _adaptive_features(state)
        scored = [
            (_score_action(state, action, before, weights), action)
            for action in candidates
        ]
        scored.sort(key=lambda item: (-item[0], _action_sort_key(item[1])))

        if (
            LOOKAHEAD_ENABLED
            and LOOKAHEAD_DEPTH
            and len(candidates) <= LOOKAHEAD_MAX_CANDIDATES
        ):
            scored = _apply_shallow_lookahead(state, scored)

        if scored and scored[0][0] >= MINIMUM_USEFUL_SCORE:
            return scored[0][1]

        pass_action = _first_action(legal_actions, "pass")
        if pass_action is not None:
            return pass_action
        fallback_actions = [
            action
            for action in legal_actions
            if action.action_type != "next_turn"
        ]
        if fallback_actions:
            return min(fallback_actions, key=_action_sort_key)
        next_turn = _first_action(legal_actions, "next_turn")
        return next_turn or min(legal_actions, key=_action_sort_key)


def _game_phase(state: GameState) -> str:
    completed = sum(route.completed for route in state.routes.values())
    if state.turn <= 5 or completed <= 3:
        return "early"
    if state.turn <= 15 or completed <= 10:
        return "mid"
    return "late"


def _weights_for_state(state: GameState) -> AdaptiveWeights:
    return PHASE_WEIGHTS[_game_phase(state)]


def _candidate_actions(actions: list[Action]) -> list[Action]:
    supported = {"deliver_good", "build_track_segments", "upgrade_engine"}
    return sorted(
        (action for action in actions if action.action_type in supported),
        key=_action_sort_key,
    )


def _adaptive_features(state: GameState) -> dict[str, Any]:
    deliveries = get_legal_deliveries(state)
    delivery_scores = sorted(
        (float(action.params.get("score", 0)) for action in deliveries),
        reverse=True,
    )
    return {
        "final_score": state.final_score(),
        "score": state.player.score,
        "money": state.player.money,
        "bonds": state.player.bonds,
        "locomotive_level": state.player.locomotive_level,
        "delivered_goods_count": state.player.delivered_goods_count,
        "major_line_bonus": state.player.major_line_bonus,
        "rail_baron_bonus": state.player.rail_baron_bonus,
        "rail_baron_objectives_completed": (
            state.player.rail_baron_objectives_completed
        ),
        "claimed_major_lines_count": sum(
            line.claimed for line in state.major_lines.values()
        ),
        "completed_routes_count": sum(
            route.completed for route in state.routes.values()
        ),
        "legal_delivery_count": len(deliveries),
        "delivery_value": sum(delivery_scores[:3]),
        "rail_baron_remaining_distance": _rail_baron_remaining_distance(state),
        "goods_demand_potential": _goods_demand_potential(state),
        "completed_network_city_count": len(
            _completed_network_city_ids(state)
        ),
        "goods_backlog": sum(len(city.goods) for city in state.cities.values()),
    }


def _score_action(
    state: GameState,
    action: Action,
    before_features: dict[str, Any],
    weights: AdaptiveWeights,
) -> float:
    candidate = state.copy()
    _, applied, _ = apply_action(candidate, action)
    if not applied:
        return float("-inf")
    after = _adaptive_features(candidate)

    if action.action_type == "deliver_good":
        return _score_delivery(state, action, before_features, after, weights)
    if action.action_type == "build_track_segments":
        return _score_build(state, candidate, action, before_features, after, weights)
    if action.action_type == "upgrade_engine":
        return _score_upgrade(state, action, before_features, after, weights)
    return float("-inf")


def _score_delivery(
    state: GameState,
    action: Action,
    before: dict[str, Any],
    after: dict[str, Any],
    weights: AdaptiveWeights,
) -> float:
    final_delta = after["final_score"] - before["final_score"]
    delivered_delta = after["delivered_goods_count"] - before["delivered_goods_count"]
    backlog_reduction = max(0, before["goods_backlog"] - after["goods_backlog"])
    new_bonds = max(0, after["bonds"] - before["bonds"])
    return (
        weights.delivery_score * int(action.params.get("score", 0))
        + 30.0 * final_delta
        + 10.0 * delivered_delta
        + 10.0 * backlog_reduction
        - _adaptive_debt_penalty(state, new_bonds, weights)
    )


def _score_build(
    state: GameState,
    candidate: GameState,
    action: Action,
    before: dict[str, Any],
    after: dict[str, Any],
    weights: AdaptiveWeights,
) -> float:
    segment_ids = _segment_ids(action)
    if not segment_ids or any(item not in state.segments for item in segment_ids):
        return float("-inf")

    new_rail_claims = max(
        0,
        after["rail_baron_objectives_completed"]
        - before["rail_baron_objectives_completed"],
    )
    new_major_lines = max(
        0,
        after["claimed_major_lines_count"] - before["claimed_major_lines_count"],
    )
    new_routes = max(
        0,
        after["completed_routes_count"] - before["completed_routes_count"],
    )
    future_delivery_delta = max(0.0, after["delivery_value"] - before["delivery_value"])
    potential_delta = max(
        0,
        after["goods_demand_potential"] - before["goods_demand_potential"],
    )
    new_network_cities = max(
        0,
        after["completed_network_city_count"]
        - before["completed_network_city_count"],
    )
    rail_roi = _rail_baron_roi_progress(state, candidate)
    major_roi = _major_line_roi_progress(state, candidate)
    construction_cost = sum(state.segments[item].cost for item in segment_ids)
    new_bonds = max(0, after["bonds"] - before["bonds"])

    score = (
        weights.rail_baron_claim * new_rail_claims
        + weights.major_line_claim * new_major_lines
        + weights.rail_baron_roi * rail_roi
        + weights.major_line_roi * major_roi
        + weights.route_completion * new_routes
        + weights.delivery_value * future_delivery_delta
        + 40.0 * potential_delta
        + weights.network_expansion * new_network_cities
        - weights.construction_cost * construction_cost
        - _adaptive_debt_penalty(state, new_bonds, weights)
    )

    if _action_completes_existing_incomplete_route(state, action):
        score += 80.0
    elif _action_extends_existing_incomplete_route(state, action):
        score += 30.0

    clear_progress = any(
        value > 0
        for value in (
            new_rail_claims,
            new_major_lines,
            rail_roi,
            major_roi,
            future_delivery_delta,
        )
    )
    if (
        _action_starts_new_route_while_incomplete_routes_exist(state, action)
        and not clear_progress
    ):
        score -= weights.incomplete_route_penalty
    if _game_phase(state) == "late" and not clear_progress and new_routes == 0:
        score -= 120.0
    return score


def _score_upgrade(
    state: GameState,
    action: Action,
    before: dict[str, Any],
    after: dict[str, Any],
    weights: AdaptiveWeights,
) -> float:
    future_delta = max(0.0, after["delivery_value"] - before["delivery_value"])
    new_deliveries = max(
        0,
        after["legal_delivery_count"] - before["legal_delivery_count"],
    )
    new_bonds = max(0, after["bonds"] - before["bonds"])
    frontier = _upgrade_frontier_count(state, int(after["locomotive_level"]))
    cost = int(action.params.get("cost", 0))
    score = (
        weights.upgrade_value * future_delta
        + 50.0 * frontier
        + 100.0 * new_deliveries
        - _adaptive_debt_penalty(state, new_bonds, weights)
        - cost
    )
    if _game_phase(state) == "early" and future_delta <= 0:
        score -= 100.0
    if _game_phase(state) == "late" and new_deliveries <= 0:
        score -= 150.0
    return score


def _delivery_value(state: GameState, top_k: int = 3) -> float:
    scores = sorted(
        (
            float(action.params.get("score", 0))
            for action in get_legal_deliveries(state)
        ),
        reverse=True,
    )
    return sum(scores[:top_k])


def _adaptive_debt_penalty(
    state: GameState,
    new_bonds: int,
    weights: AdaptiveWeights,
) -> float:
    multiplier = 1.0 + state.player.bonds / 5.0
    if _game_phase(state) == "late":
        multiplier *= 1.5
    return new_bonds * weights.debt_penalty * multiplier


def _rail_baron_roi_progress(before: GameState, after: GameState) -> float:
    objective_id = before.active_rail_baron_objective_id
    objective = before.rail_baron_objectives.get(objective_id or "")
    if objective is None or objective.claimed:
        return 0.0
    before_distance = _rail_baron_remaining_distance(before)
    after_distance = _rail_baron_remaining_distance(after)
    progress = _distance_reduction(before_distance, after_distance)
    return progress * objective.bonus_points / max(1.0, after_distance)


def _major_line_roi_progress(before: GameState, after: GameState) -> float:
    total = 0.0
    for line_id, line in before.major_lines.items():
        if line.claimed or line_id not in after.major_lines:
            continue
        before_distance = _remaining_distance(before, line.source, line.target)
        after_line = after.major_lines[line_id]
        after_distance = 0.0 if after_line.claimed else _remaining_distance(
            after,
            line.source,
            line.target,
        )
        progress = _distance_reduction(before_distance, after_distance)
        total += progress * line.bonus_points / max(1.0, after_distance)
    return total


def _action_route_id(state: GameState, action: Action) -> str | None:
    segment_ids = _segment_ids(action)
    if not segment_ids or segment_ids[0] not in state.segments:
        return None
    return state.segments[segment_ids[0]].route_id


def _route_has_incomplete_track(state: GameState, route_id: str) -> bool:
    route = state.routes.get(route_id)
    return bool(route) and not route.completed and any(
        state.segments[item].built
        for item in route.segment_ids
        if item in state.segments
    )


def _action_completes_existing_incomplete_route(
    state: GameState,
    action: Action,
) -> bool:
    route_id = _action_route_id(state, action)
    if route_id is None or not _route_has_incomplete_track(state, route_id):
        return False
    route = state.routes[route_id]
    action_ids = set(_segment_ids(action))
    return all(
        state.segments[item].built or item in action_ids
        for item in route.segment_ids
        if item in state.segments
    )


def _action_extends_existing_incomplete_route(state: GameState, action: Action) -> bool:
    route_id = _action_route_id(state, action)
    return bool(
        route_id
        and _route_has_incomplete_track(state, route_id)
        and not _action_completes_existing_incomplete_route(state, action)
    )


def _action_starts_new_route_while_incomplete_routes_exist(
    state: GameState,
    action: Action,
) -> bool:
    route_id = _action_route_id(state, action)
    if route_id is None:
        return False
    target_has_track = _route_has_incomplete_track(state, route_id)
    other_incomplete = any(
        _route_has_incomplete_track(state, item)
        for item in state.routes
        if item != route_id
    )
    return not target_has_track and other_incomplete


def _apply_shallow_lookahead(
    state: GameState,
    scored: list[tuple[float, Action]],
) -> list[tuple[float, Action]]:
    adjusted: list[tuple[float, Action]] = []
    top_actions = {
        _action_sort_key(action) for _, action in scored[:LOOKAHEAD_TOP_K]
    }
    for immediate, action in scored:
        total = immediate
        if _action_sort_key(action) in top_actions and math.isfinite(immediate):
            candidate = state.copy()
            _, applied, _ = apply_action(candidate, action)
            if applied:
                next_score = _best_immediate_next_score(candidate)
                total += LOOKAHEAD_DISCOUNT * max(0.0, next_score)
        adjusted.append((total, action))
    adjusted.sort(key=lambda item: (-item[0], _action_sort_key(item[1])))
    return adjusted


def _best_immediate_next_score(state: GameState) -> float:
    actions = _candidate_actions(get_legal_actions(state))
    if not actions:
        return 0.0
    before = _adaptive_features(state)
    weights = _weights_for_state(state)
    return max(_score_action(state, action, before, weights) for action in actions)
