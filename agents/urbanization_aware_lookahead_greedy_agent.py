from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import random

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
from railways.actions import Action
from railways.environment import apply_action, get_legal_actions
from railways.game_state import GameState


DEPTH = 2
TOP_K_BUILDS = 4
TOP_K_URBANIZE = 3
TOP_K_DELIVERIES = 4
ROLLOUT_TOP_K = 5
DISCOUNT = 0.6
MINIMUM_USEFUL_SCORE = 1.0


@dataclass(frozen=True)
class CandidateAction:
    action: Action
    return_action: Action
    priority_score: float


class UrbanizationAwareLookaheadGreedyAgent(BaseAgent):
    """Deterministic bounded lookahead heuristic with explicit urbanize value."""

    name = "urbanization_aware_lookahead_greedy"

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
            immediate = candidate.priority_score
            future = _rollout_value(simulated, DEPTH - 1)
            scored.append((immediate + DISCOUNT * future, candidate))

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

    build_actions = [
        action for action in legal_actions if action.action_type == "build_track_segments"
    ]
    scored_builds = [
        (_score_build_action(state, action), action)
        for action in build_actions
    ]
    scored_builds = [
        item for item in scored_builds if math.isfinite(item[0])
    ]
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

    candidates.extend(_urbanize_candidates(state, legal_actions))

    deduped: dict[tuple[str, str], CandidateAction] = {}
    for candidate in candidates:
        key = (
            _candidate_sort_key_text(candidate),
            _action_identity(candidate.action),
        )
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
) -> list[CandidateAction]:
    legal_urbanize = [
        action for action in legal_actions if action.action_type == "urbanize"
    ]
    if not legal_urbanize:
        return []

    candidates: list[CandidateAction] = []
    for legal_action in sorted(legal_urbanize, key=_objective_action_sort_key):
        city_id = str(legal_action.params.get("city_id", ""))
        if city_id not in state.cities:
            continue
        score = _score_urbanize_action(state, legal_action)
        candidates.append(
            CandidateAction(
                action=legal_action,
                return_action=legal_action,
                priority_score=score,
            )
        )
    candidates.sort(key=lambda item: (-item.priority_score, _candidate_sort_key(item)))
    return candidates[:TOP_K_URBANIZE]


def _rollout_value(state: GameState, depth: int) -> float:
    if state.is_terminal():
        return _evaluate_state(state)
    if depth <= 0:
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
        CandidateAction(action, action, float(action.params.get("score", 0)))
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
        CandidateAction(action, action, 0.0)
        for action in legal_actions
        if action.action_type == "upgrade_engine"
    )

    urbanize_actions = [
        action for action in legal_actions if action.action_type == "urbanize"
    ]
    urbanize_candidates: list[CandidateAction] = []
    for legal_action in urbanize_actions:
        urbanize_candidates.append(
            CandidateAction(
                action=legal_action,
                return_action=legal_action,
                priority_score=_simple_urbanize_priority(state, legal_action),
            )
        )
    urbanize_candidates.sort(
        key=lambda item: (-item.priority_score, _candidate_sort_key(item))
    )
    candidates.extend(urbanize_candidates[:2])

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
        return _score_urbanize_action(state, action)
    return float("-inf")


def _score_delivery_action(state: GameState, action: Action) -> float:
    candidate, applied = _simulate_action(state, action)
    if not applied:
        return float("-inf")

    before = _state_features(state)
    after = _state_features(candidate)
    return (
        240.0 * float(action.params.get("score", 0))
        + 80.0 * max(0, after["delivered_goods_count"] - before["delivered_goods_count"])
        + 25.0 * max(0, after["final_score"] - before["final_score"])
        - 35.0 * max(0, after["bonds"] - before["bonds"])
    )


def _score_urbanize_action(state: GameState, action: Action) -> float:
    city_id = str(action.params.get("city_id", ""))
    city = state.cities.get(city_id)
    if city is None or not city.is_gray:
        return float("-inf")

    before = _state_features(state)
    before_rail_distance = float(before["rail_baron_remaining_distance"])
    candidate, applied = _simulate_action(state, action)
    if not applied:
        return float("-inf")
    after = _state_features(candidate)

    chosen_color = str(action.params.get("demand_color") or "")
    matching_goods = _available_goods_count(state, chosen_color, exclude_city=city_id)
    new_goods = max(0, len(candidate.cities[city_id].goods) - len(city.goods))
    new_bonds = max(0, after["bonds"] - before["bonds"])
    new_deliveries = max(0, after["legal_delivery_count"] - before["legal_delivery_count"])
    potential_delta = max(
        0,
        after["goods_demand_potential"] - before["goods_demand_potential"],
    )
    rail_progress = _distance_reduction(
        before_rail_distance,
        _rail_baron_remaining_distance(candidate),
    )
    major_progress = max(0.0, _major_line_progress_score(state, candidate))
    network_bonus = _urbanized_city_network_bonus(state, city_id)
    objective_bonus = _urbanized_city_objective_bonus(state, city_id)
    future_source_bonus = 20.0 * new_goods

    return (
        140.0 * min(1, matching_goods)
        + 60.0 * matching_goods
        + 220.0 * new_deliveries
        + 110.0 * potential_delta
        + 90.0 * network_bonus
        + 80.0 * objective_bonus
        + 120.0 * rail_progress
        + 12.0 * major_progress
        + future_source_bonus
        - 35.0 * new_bonds
        - 1.5 * state.config.urbanize_cost
    )


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
        20.0 * float(features["final_score"])
        + 120.0 * float(features["delivered_goods_count"])
        + 180.0 * float(features["completed_routes_count"])
        + 90.0 * float(features["legal_delivery_count"])
        + 55.0 * float(features["goods_demand_potential"])
        + 35.0 * float(features["completed_network_city_count"])
        + 25.0 * useful_urbanized
        - 45.0 * float(features["bonds"])
        - 30.0 * incomplete_segments
        - 20.0 * rail_distance_penalty
    )


def _simulate_action(state: GameState, action: Action) -> tuple[GameState, bool]:
    candidate = state.copy()
    if action.action_type != "urbanize":
        _, applied, _ = apply_action(candidate, action)
        return candidate, applied

    saved_random_state = random.getstate()
    try:
        random.seed(_stable_urbanize_seed(state, action))
        _, applied, _ = apply_action(candidate, action)
    finally:
        random.setstate(saved_random_state)
    return candidate, applied


def _stable_urbanize_seed(state: GameState, action: Action) -> int:
    city_id = str(action.params.get("city_id", ""))
    demand_color = str(action.params.get("demand_color", ""))
    city_signature = "|".join(
        f"{city.id}:{city.demand_color}:{','.join(city.goods)}:{city.is_gray}"
        for city in sorted(state.cities.values(), key=lambda item: item.id)
    )
    seed_material = (
        f"{state.turn}|{state.phase}|{state.actions_remaining}|"
        f"{city_id}|{demand_color}|{city_signature}"
    )
    digest = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _delivery_sort_key(action: Action) -> tuple[int, int, str, str, str, tuple[str, ...]]:
    return (
        -int(action.params.get("score", 0)),
        int(action.params.get("path_length", 0)),
        str(action.params.get("source", "")),
        str(action.params.get("target", "")),
        str(action.params.get("good_color", "")),
        tuple(str(item) for item in action.params.get("path", [])),
    )


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
    pass_action = next(
        (action for action in legal_actions if action.action_type == "pass"),
        None,
    )
    if pass_action is not None:
        return pass_action
    non_next_turn = [
        action for action in legal_actions if action.action_type != "next_turn"
    ]
    if non_next_turn:
        return min(non_next_turn, key=_objective_action_sort_key)
    next_turn = next(
        (action for action in legal_actions if action.action_type == "next_turn"),
        None,
    )
    return next_turn or min(legal_actions, key=_objective_action_sort_key)


def _available_goods_count(
    state: GameState,
    good_color: str,
    *,
    exclude_city: str,
) -> int:
    return sum(
        good == good_color
        for city in state.cities.values()
        if city.id != exclude_city
        for good in city.goods
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
        120.0 * completes_route
        + 35.0 * extends_incomplete
        + endpoint_bonus
        - sum(segment.cost for segment in segments)
    )


def _endpoint_goods_demand_bonus(state: GameState, city_id: str) -> float:
    city = state.cities.get(city_id)
    if city is None:
        return 0.0
    available_goods = {
        good for candidate in state.cities.values() for good in candidate.goods
    }
    return 10.0 * bool(city.goods) + 10.0 * (
        city.demand_color in available_goods if city.demand_color else False
    )


def _simple_urbanize_priority(state: GameState, action: Action) -> float:
    city_id = str(action.params.get("city_id", ""))
    city = state.cities.get(city_id)
    if city is None or not city.is_gray:
        return float("-inf")
    color = str(action.params.get("demand_color") or "")
    return (
        40.0 * _available_goods_count(state, color, exclude_city=city_id)
        + 50.0 * _urbanized_city_network_bonus(state, city_id)
        + 60.0 * _urbanized_city_objective_bonus(state, city_id)
        - state.config.urbanize_cost
    )


def _urbanized_city_network_bonus(state: GameState, city_id: str) -> float:
    bonus = 0.0
    if city_id in _completed_network_city_ids(state):
        bonus += 2.0
    if _city_touches_completed_network(state, city_id):
        bonus += 1.0
    if _city_touches_built_or_completed_route(state, city_id):
        bonus += 0.5
    return bonus


def _urbanized_city_objective_bonus(state: GameState, city_id: str) -> float:
    bonus = 0.0
    objective_id = state.active_rail_baron_objective_id
    objective = state.rail_baron_objectives.get(objective_id or "")
    if objective is not None and city_id in {objective.source, objective.target}:
        bonus += 2.0
    for line in state.major_lines.values():
        if not line.claimed and city_id in {line.source, line.target}:
            bonus += max(0.5, line.bonus_points / 5.0)
    return bonus


def _city_touches_completed_network(state: GameState, city_id: str) -> bool:
    completed_cities = _completed_network_city_ids(state)
    if not completed_cities:
        return False
    for route in state.routes.values():
        if city_id not in {route.city_a, route.city_b}:
            continue
        other = route.city_b if route.city_a == city_id else route.city_a
        if other in completed_cities:
            return True
    return False


def _city_touches_built_or_completed_route(state: GameState, city_id: str) -> bool:
    for route in state.routes.values():
        if city_id not in {route.city_a, route.city_b}:
            continue
        if route.completed:
            return True
        if any(
            state.segments[segment_id].built
            for segment_id in route.segment_ids
            if segment_id in state.segments
        ):
            return True
    return False
