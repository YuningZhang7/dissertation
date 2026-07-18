from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from agents.base_agent import BaseAgent
from agents.objective_aware_greedy_agent import (
    _action_sort_key as _objective_action_sort_key,
    _completed_network_city_ids,
    _distance_reduction,
    _goods_demand_potential,
    _major_line_progress_score,
    _rail_baron_remaining_distance,
    _score_build_action,
    _score_upgrade_action,
    _state_features,
)
from agents.urbanization_aware_lookahead_greedy_agent import (
    _available_goods_count,
    _city_touches_built_or_completed_route,
    _city_touches_completed_network,
    _delivery_sort_key,
    _score_delivery_action,
    _simulate_action,
    _urbanized_city_network_bonus,
    _urbanized_city_objective_bonus,
)
from railways.actions import Action
from railways.environment import get_legal_actions
from railways.game_state import GameState


DEPTH = 2
TOP_K_BUILDS = 4
TOP_K_URBANIZE = 1
TOP_K_DELIVERIES = 4
ROLLOUT_TOP_K = 5
DISCOUNT = 0.55
MINIMUM_USEFUL_SCORE = 1.0


@dataclass(frozen=True)
class CandidateAction:
    action: Action
    return_action: Action
    priority_score: float
    direct_new_deliveries: int = 0


class PresentationLookaheadGreedyAgent(BaseAgent):
    """Replay-friendly lookahead heuristic with conservative urbanization."""

    name = "presentation_lookahead_greedy"

    def choose_action(self, state: GameState) -> Action:
        legal_actions = get_legal_actions(state)
        if not legal_actions:
            return Action.pass_action()

        candidates = _candidate_actions(state, legal_actions)
        if not candidates:
            return _fallback_action(legal_actions)

        scored: list[tuple[float, CandidateAction]] = []
        for candidate in candidates:
            simulated, applied = _simulate_action(state, candidate.action)
            if not applied:
                continue
            future = _rollout_value(simulated, DEPTH - 1)
            scored.append((candidate.priority_score + DISCOUNT * future, candidate))

        if scored:
            best_score, best_candidate = sorted(
                scored,
                key=lambda item: (
                    -item[0],
                    _candidate_sort_rank(item[1]),
                    _candidate_sort_key(item[1]),
                ),
            )[0]
            if best_score >= MINIMUM_USEFUL_SCORE:
                return best_candidate.return_action

        return _fallback_action(legal_actions)


def _candidate_actions(
    state: GameState,
    legal_actions: list[Action],
) -> list[CandidateAction]:
    candidates: list[CandidateAction] = []

    deliveries = [action for action in legal_actions if action.action_type == "deliver_good"]
    ranked_deliveries = sorted(deliveries, key=_delivery_sort_key)[:TOP_K_DELIVERIES]
    candidates.extend(
        CandidateAction(action, action, _score_delivery_action(state, action))
        for action in ranked_deliveries
    )
    high_value_delivery_available = any(
        float(action.params.get("score", 0)) >= 4.0 for action in deliveries
    )

    build_actions = [
        action for action in legal_actions if action.action_type == "build_track_segments"
    ]
    scored_builds = [
        (_score_build_action(state, action), action)
        for action in build_actions
    ]
    scored_builds = [item for item in scored_builds if math.isfinite(item[0])]
    scored_builds.sort(key=lambda item: (-item[0], _objective_action_sort_key(item[1])))
    candidates.extend(
        CandidateAction(action, action, score)
        for score, action in scored_builds[:TOP_K_BUILDS]
    )

    upgrade_actions = [
        action for action in legal_actions if action.action_type == "upgrade_engine"
    ]
    candidates.extend(
        CandidateAction(action, action, _score_upgrade_action(state, action))
        for action in upgrade_actions
    )

    candidates.extend(
        _urbanize_candidates(
            state,
            legal_actions,
            high_value_delivery_available=high_value_delivery_available,
        )
    )

    deduped: dict[tuple[str, str], CandidateAction] = {}
    for candidate in candidates:
        key = (_candidate_sort_key_text(candidate), _action_identity(candidate.action))
        existing = deduped.get(key)
        if existing is None or candidate.priority_score > existing.priority_score:
            deduped[key] = candidate

    return sorted(
        deduped.values(),
        key=lambda candidate: (-candidate.priority_score, _candidate_sort_key(candidate)),
    )


def _urbanize_candidates(
    state: GameState,
    legal_actions: list[Action],
    *,
    high_value_delivery_available: bool,
) -> list[CandidateAction]:
    legal_urbanize = [
        action for action in legal_actions if action.action_type == "urbanize"
    ]
    if not legal_urbanize:
        return []

    candidates: list[CandidateAction] = []
    for legal_action in sorted(legal_urbanize, key=_objective_action_sort_key):
        score, direct_new_deliveries = _score_urbanize_action(
            state,
            legal_action,
            high_value_delivery_available=high_value_delivery_available,
        )
        if not math.isfinite(score):
            continue
        candidates.append(
            CandidateAction(
                action=legal_action,
                return_action=legal_action,
                priority_score=score,
                direct_new_deliveries=direct_new_deliveries,
            )
        )
    candidates.sort(key=lambda item: (-item.priority_score, _candidate_sort_key(item)))
    return candidates[:TOP_K_URBANIZE]


def _score_urbanize_action(
    state: GameState,
    action: Action,
    *,
    high_value_delivery_available: bool,
) -> tuple[float, int]:
    city_id = str(action.params.get("city_id", ""))
    city = state.cities.get(city_id)
    if city is None or not city.is_gray:
        return float("-inf"), 0

    before = _state_features(state)
    before_rail_distance = float(before["rail_baron_remaining_distance"])
    candidate, applied = _simulate_action(state, action)
    if not applied:
        return float("-inf"), 0
    after = _state_features(candidate)

    new_bonds = max(0, after["bonds"] - before["bonds"])
    new_deliveries = max(0, after["legal_delivery_count"] - before["legal_delivery_count"])
    network_bonus = _urbanized_city_network_bonus(state, city_id)
    objective_bonus = _urbanized_city_objective_bonus(state, city_id)
    chosen_color = str(action.params.get("demand_color") or "")
    matching_goods = _available_goods_count(state, chosen_color, exclude_city=city_id)

    if high_value_delivery_available and new_deliveries <= 0 and objective_bonus <= 0:
        return float("-inf"), new_deliveries
    if not _is_urbanize_allowed_for_presentation(
        state,
        action,
        before,
        after,
        city_id,
        new_bonds=new_bonds,
        new_deliveries=new_deliveries,
        network_bonus=network_bonus,
        objective_bonus=objective_bonus,
        matching_goods=matching_goods,
    ):
        return float("-inf"), new_deliveries

    new_goods = max(0, len(candidate.cities[city_id].goods) - len(city.goods))
    potential_delta = max(
        0,
        after["goods_demand_potential"] - before["goods_demand_potential"],
    )
    rail_progress = _distance_reduction(
        before_rail_distance,
        _rail_baron_remaining_distance(candidate),
    )
    major_progress = max(0.0, _major_line_progress_score(state, candidate))

    score = (
        130.0 * min(1, matching_goods)
        + 70.0 * matching_goods
        + 280.0 * new_deliveries
        + 55.0 * potential_delta
        + 130.0 * network_bonus
        + 110.0 * objective_bonus
        + 120.0 * rail_progress
        + 16.0 * major_progress
        + 12.0 * new_goods
        - 75.0 * new_bonds
        - 2.4 * state.config.urbanize_cost
    )
    return score, new_deliveries


def _is_urbanize_allowed_for_presentation(
    state: GameState,
    action: Action,
    before: dict[str, Any],
    after: dict[str, Any],
    city_id: str,
    *,
    new_bonds: int,
    new_deliveries: int,
    network_bonus: float,
    objective_bonus: float,
    matching_goods: int,
) -> bool:
    touches_network = _city_touches_built_or_completed_route(state, city_id)
    if not touches_network:
        return False

    is_objective_endpoint = _is_active_objective_endpoint(state, city_id)
    if (
        before["completed_routes_count"] == 0
        and new_deliveries <= 0
        and not is_objective_endpoint
    ):
        return False

    has_near_term_value = (
        new_deliveries > 0
        or matching_goods > 0
        or network_bonus > 0
        or objective_bonus > 0
        or is_objective_endpoint
    )
    if not has_near_term_value:
        return False

    if before["bonds"] >= 4 and new_bonds > 0 and new_deliveries <= 0:
        return False

    if (
        _urbanized_city_count(state) >= 2
        and new_deliveries <= 0
        and objective_bonus <= 0
    ):
        return False

    return after["completed_routes_count"] >= before["completed_routes_count"]


def _rollout_value(state: GameState, depth: int) -> float:
    if state.is_terminal() or depth <= 0:
        return _evaluate_state(state)

    legal_actions = get_legal_actions(state)
    candidates = _rollout_candidate_actions(state, legal_actions)[:ROLLOUT_TOP_K]
    if not candidates:
        return _evaluate_state(state)

    best = _evaluate_state(state)
    for candidate in candidates:
        simulated, applied = _simulate_action(state, candidate.action)
        if not applied:
            continue
        immediate = _score_action_immediate(state, candidate.action)
        value = immediate + DISCOUNT * _rollout_value(simulated, depth - 1)
        best = max(best, value)
    return best


def _rollout_candidate_actions(
    state: GameState,
    legal_actions: list[Action],
) -> list[CandidateAction]:
    candidates: list[CandidateAction] = []

    deliveries = [action for action in legal_actions if action.action_type == "deliver_good"]
    candidates.extend(
        CandidateAction(action, action, _score_delivery_action(state, action))
        for action in sorted(deliveries, key=_delivery_sort_key)[:2]
    )

    build_actions = [
        action for action in legal_actions if action.action_type == "build_track_segments"
    ]
    ranked_builds = sorted(
        build_actions,
        key=lambda action: (-_simple_build_priority(state, action), _objective_action_sort_key(action)),
    )
    candidates.extend(
        CandidateAction(action, action, _simple_build_priority(state, action))
        for action in ranked_builds[:3]
    )

    candidates.extend(
        CandidateAction(action, action, _score_upgrade_action(state, action))
        for action in legal_actions
        if action.action_type == "upgrade_engine"
    )

    high_value_delivery_available = any(
        action.action_type == "deliver_good"
        and float(action.params.get("score", 0)) >= 4.0
        for action in legal_actions
    )
    candidates.extend(
        _urbanize_candidates(
            state,
            legal_actions,
            high_value_delivery_available=high_value_delivery_available,
        )[:1]
    )

    return sorted(
        candidates,
        key=lambda candidate: (-candidate.priority_score, _candidate_sort_key(candidate)),
    )


def _score_action_immediate(state: GameState, action: Action) -> float:
    if action.action_type == "deliver_good":
        return _score_delivery_action(state, action)
    if action.action_type == "build_track_segments":
        return _score_build_action(state, action)
    if action.action_type == "upgrade_engine":
        return _score_upgrade_action(state, action)
    if action.action_type == "urbanize":
        score, _ = _score_urbanize_action(
            state,
            action,
            high_value_delivery_available=False,
        )
        return score
    return float("-inf")


def _evaluate_state(state: GameState) -> float:
    features = _state_features(state)
    incomplete_segments = sum(
        segment.built and not segment.completed for segment in state.segments.values()
    )
    useful_urbanized = sum(
        (not city.is_gray)
        and city.is_urbanized
        and (
            city.id in _completed_network_city_ids(state)
            or _city_touches_completed_network(state, city.id)
        )
        for city in state.cities.values()
    )
    rail_distance = float(features["rail_baron_remaining_distance"])
    rail_distance_penalty = 0.0 if not math.isfinite(rail_distance) else rail_distance
    return (
        22.0 * float(features["final_score"])
        + 150.0 * float(features["delivered_goods_count"])
        + 220.0 * float(features["completed_routes_count"])
        + 55.0 * float(features["legal_delivery_count"])
        + 35.0 * float(features["goods_demand_potential"])
        + 40.0 * float(features["completed_network_city_count"])
        + 35.0 * useful_urbanized
        - 60.0 * float(features["bonds"])
        - 50.0 * incomplete_segments
        - 20.0 * rail_distance_penalty
    )


def _simple_build_priority(state: GameState, action: Action) -> float:
    segment_ids = [
        str(item) for item in action.params.get("segment_ids", [])
    ]
    segments = [
        state.segments[segment_id]
        for segment_id in segment_ids
        if segment_id in state.segments
    ]
    if not segments:
        return float("-inf")

    route = state.routes.get(segments[0].route_id)
    if route is None:
        return float("-inf")

    action_ids = {segment.id for segment in segments}
    completes_route = all(
        state.segments[segment_id].built or segment_id in action_ids
        for segment_id in route.segment_ids
        if segment_id in state.segments
    )
    extends_incomplete = any(
        state.segments[segment_id].built
        and not state.segments[segment_id].completed
        for segment_id in route.segment_ids
        if segment_id in state.segments
    )
    endpoint_bonus = _endpoint_goods_demand_bonus(state, route.city_a)
    endpoint_bonus += _endpoint_goods_demand_bonus(state, route.city_b)
    return (
        150.0 * completes_route
        + 25.0 * extends_incomplete
        + endpoint_bonus
        - 1.5 * sum(segment.cost for segment in segments)
    )


def _endpoint_goods_demand_bonus(state: GameState, city_id: str) -> float:
    city = state.cities.get(city_id)
    if city is None:
        return 0.0
    available_goods = {
        good for candidate in state.cities.values() for good in candidate.goods
    }
    return 12.0 * bool(city.goods) + 14.0 * (
        city.demand_color in available_goods if city.demand_color else False
    )


def _is_active_objective_endpoint(state: GameState, city_id: str) -> bool:
    objective_id = state.active_rail_baron_objective_id
    objective = state.rail_baron_objectives.get(objective_id or "")
    if objective is not None and city_id in {objective.source, objective.target}:
        return True
    return any(
        not line.claimed and city_id in {line.source, line.target}
        for line in state.major_lines.values()
    )


def _urbanized_city_count(state: GameState) -> int:
    return sum(city.is_urbanized for city in state.cities.values())


def _candidate_sort_key(
    candidate: CandidateAction,
) -> tuple[str, str, str, str, tuple[str, ...]]:
    action = candidate.action
    return (
        action.action_type,
        "-".join(str(item) for item in action.params.get("segment_ids", [])),
        str(action.params.get("city_id", "")),
        str(action.params.get("demand_color", "")),
        tuple(str(item) for item in action.params.get("path", [])),
    )


def _candidate_sort_key_text(candidate: CandidateAction) -> str:
    return "|".join(str(item) for item in _candidate_sort_key(candidate))


def _candidate_sort_rank(candidate: CandidateAction) -> int:
    order = {
        "deliver_good": 0,
        "build_track_segments": 1,
        "urbanize": 2,
        "upgrade_engine": 3,
    }
    return order.get(candidate.action.action_type, 9)


def _action_identity(action: Action) -> str:
    params = "|".join(f"{key}={action.params[key]}" for key in sorted(action.params))
    return f"{action.action_type}|{params}"


def _fallback_action(legal_actions: list[Action]) -> Action:
    useful_actions = [
        action
        for action in legal_actions
        if action.action_type not in {"pass", "next_turn"}
    ]
    if useful_actions:
        return min(useful_actions, key=_objective_action_sort_key)
    next_turn = next(
        (action for action in legal_actions if action.action_type == "next_turn"),
        None,
    )
    if next_turn is not None:
        return next_turn
    return min(legal_actions, key=_objective_action_sort_key)
