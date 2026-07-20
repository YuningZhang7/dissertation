from __future__ import annotations

import hashlib
import random

from agents.objective_aware_greedy_agent import (
    _completed_network_city_ids,
    _state_features,
)
from railways.actions import Action
from railways.environment import apply_action
from railways.game_state import GameState


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
