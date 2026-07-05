from __future__ import annotations

import math
from typing import Any

import networkx as nx

from agents.base_agent import BaseAgent
from railways.actions import Action
from railways.environment import apply_action, get_legal_actions
from railways.game_state import GameState
from railways.rules import get_legal_deliveries


MINIMUM_USEFUL_SCORE = 1.0


class ObjectiveAwareGreedyAgent(BaseAgent):
    """Deterministic one-step heuristic for official-style route maps."""

    name = "objective_aware_greedy"

    def choose_action(self, state: GameState) -> Action:
        legal_actions = get_legal_actions(state)
        if not legal_actions:
            return Action.pass_action()

        deliveries = [
            action
            for action in legal_actions
            if action.action_type == "deliver_good"
        ]
        if deliveries:
            return min(
                deliveries,
                key=lambda action: _delivery_sort_key(state, action),
            )

        before = _state_features(state)
        scored_actions: list[tuple[float, Action]] = []
        for action in legal_actions:
            if action.action_type == "build_track_segments":
                scored_actions.append(
                    (_score_build_action(state, action, before), action)
                )
            elif action.action_type == "upgrade_engine":
                scored_actions.append(
                    (_score_upgrade_action(state, action, before), action)
                )

        if scored_actions:
            best_score, best_action = min(
                scored_actions,
                key=lambda candidate: (-candidate[0], _action_sort_key(candidate[1])),
            )
            if best_score >= MINIMUM_USEFUL_SCORE:
                return best_action

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
        if next_turn is not None:
            return next_turn
        return min(legal_actions, key=_action_sort_key)


def _delivery_sort_key(
    state: GameState,
    action: Action,
) -> tuple[int, int, int, str, str, str, tuple[str, ...]]:
    source = str(action.params.get("source", ""))
    source_goods = len(state.cities[source].goods) if source in state.cities else 0
    return (
        -int(action.params.get("score", 0)),
        int(action.params.get("path_length", 0)),
        -source_goods,
        source,
        str(action.params.get("target", "")),
        str(action.params.get("good_color", "")),
        tuple(str(item) for item in action.params.get("path", [])),
    )


def _score_build_action(
    state: GameState,
    action: Action,
    before: dict[str, Any] | None = None,
) -> float:
    segment_ids = _segment_ids(action)
    if not segment_ids or any(
        segment_id not in state.segments for segment_id in segment_ids
    ):
        return float("-inf")

    before_features = before or _state_features(state)
    before_rail_distance = float(
        before_features["rail_baron_remaining_distance"]
    )
    candidate = state.copy()
    _, applied, _ = apply_action(candidate, action)
    if not applied:
        return float("-inf")

    after = _state_features(candidate)
    rail_progress = _distance_reduction(
        before_rail_distance,
        _rail_baron_remaining_distance(candidate),
    )
    major_progress = _major_line_progress_score(state, candidate)
    new_deliveries = max(
        0,
        after["legal_delivery_count"] - before_features["legal_delivery_count"],
    )
    new_bonds = max(0, after["bonds"] - before_features["bonds"])
    new_completed_routes = max(
        0,
        after["completed_routes_count"]
        - before_features["completed_routes_count"],
    )
    new_major_lines = max(
        0,
        after["claimed_major_lines_count"]
        - before_features["claimed_major_lines_count"],
    )
    new_rail_baron_claims = max(
        0,
        after["rail_baron_objectives_completed"]
        - before_features["rail_baron_objectives_completed"],
    )
    new_delivery_potential = max(
        0,
        after["goods_demand_potential"]
        - before_features["goods_demand_potential"],
    )
    new_network_cities = max(
        0,
        after["completed_network_city_count"]
        - before_features["completed_network_city_count"],
    )
    construction_cost = sum(state.segments[item].cost for item in segment_ids)

    # Large bonuses make direct objectives dominate. Progress terms reward useful
    # partial construction, while cost and debt keep unrelated builds unattractive.
    score = 0.0
    score += 1000.0 * new_rail_baron_claims
    score += 700.0 * new_major_lines
    score += 300.0 * new_deliveries
    score += 180.0 * new_completed_routes
    score += 120.0 * rail_progress
    # major_progress is already weighted by each line's bonus. A factor of ten
    # gives an eight-point line the suggested 80 points per distance unit.
    score += 10.0 * major_progress
    score += 50.0 * new_delivery_potential
    score += 20.0 * new_network_cities
    score -= 25.0 * new_bonds
    score -= 2.0 * construction_cost

    if _leaves_unfocused_incomplete_track(
        candidate,
        segment_ids,
        objective_progress=(
            rail_progress
            + major_progress
            + new_deliveries
            + new_completed_routes
            + new_delivery_potential
            + new_network_cities
        ),
    ):
        score -= 40.0
    return score


def _score_upgrade_action(
    state: GameState,
    action: Action,
    before: dict[str, Any] | None = None,
) -> float:
    before_features = before or _state_features(state)
    candidate = state.copy()
    _, applied, _ = apply_action(candidate, action)
    if not applied:
        return float("-inf")

    after = _state_features(candidate)
    new_deliveries = max(
        0,
        after["legal_delivery_count"] - before_features["legal_delivery_count"],
    )
    new_bonds = max(0, after["bonds"] - before_features["bonds"])
    frontier_paths = _upgrade_frontier_count(
        state,
        int(after["locomotive_level"]),
    )
    upgrade_cost = int(action.params.get("cost", 0))
    return (
        200.0 * new_deliveries
        + 50.0 * frontier_paths
        - 25.0 * new_bonds
        - upgrade_cost
    )


def _state_features(state: GameState) -> dict[str, Any]:
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
        "built_segments_count": sum(
            segment.built for segment in state.segments.values()
        ),
        "completed_segments_count": sum(
            segment.completed for segment in state.segments.values()
        ),
        "legal_delivery_count": len(get_legal_deliveries(state)),
        "rail_baron_remaining_distance": _rail_baron_remaining_distance(state),
        "goods_demand_potential": _goods_demand_potential(state),
        "completed_network_city_count": len(
            _completed_network_city_ids(state)
        ),
    }


def _rail_baron_remaining_distance(state: GameState) -> float:
    objective_id = state.active_rail_baron_objective_id
    if objective_id is None:
        return math.inf
    objective = state.rail_baron_objectives.get(objective_id)
    if objective is None:
        return math.inf
    if objective.claimed:
        return 0.0
    return _remaining_distance(state, objective.source, objective.target)


def _major_line_progress_score(before: GameState, after: GameState) -> float:
    progress = 0.0
    for line_id, before_line in before.major_lines.items():
        if before_line.claimed:
            continue
        after_line = after.major_lines.get(line_id)
        if after_line is None:
            continue
        before_distance = _remaining_distance(
            before,
            before_line.source,
            before_line.target,
        )
        after_distance = (
            0.0
            if after_line.claimed
            else _remaining_distance(after, after_line.source, after_line.target)
        )
        progress += (
            _distance_reduction(before_distance, after_distance)
            * before_line.bonus_points
        )
    return progress


def _remaining_distance(state: GameState, source: str, target: str) -> float:
    graph = _route_remaining_graph(state)
    try:
        return float(nx.shortest_path_length(graph, source, target, weight="weight"))
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return math.inf


def _route_remaining_graph(state: GameState) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(state.cities)
    for route in state.routes.values():
        remaining = 0 if route.completed else sum(
            not state.segments[segment_id].built
            for segment_id in route.segment_ids
            if segment_id in state.segments
        )
        weight = float(remaining)
        if graph.has_edge(route.city_a, route.city_b):
            weight = min(weight, float(graph[route.city_a][route.city_b]["weight"]))
        graph.add_edge(route.city_a, route.city_b, weight=weight)
    return graph


def _completed_route_graph(state: GameState) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(state.cities)
    for route in state.routes.values():
        if not route.completed:
            continue
        weight = max(1, len(route.segment_ids))
        if graph.has_edge(route.city_a, route.city_b):
            weight = min(weight, int(graph[route.city_a][route.city_b]["weight"]))
        graph.add_edge(route.city_a, route.city_b, weight=weight)
    return graph


def _goods_demand_potential(state: GameState) -> int:
    graph = _completed_route_graph(state)
    potential: set[tuple[str, str, str]] = set()
    for source in state.cities.values():
        for good in set(source.goods):
            for target in state.cities.values():
                if source.id == target.id or target.demand_color != good:
                    continue
                try:
                    if nx.has_path(graph, source.id, target.id):
                        potential.add((source.id, target.id, good))
                except (nx.NetworkXError, nx.NodeNotFound):
                    continue
    return len(potential)


def _completed_network_city_ids(state: GameState) -> set[str]:
    city_ids: set[str] = set()
    for route in state.routes.values():
        if route.completed:
            city_ids.update((route.city_a, route.city_b))
    return city_ids


def _upgrade_frontier_count(state: GameState, new_level: int) -> int:
    graph = _completed_route_graph(state)
    current_level = state.player.locomotive_level
    frontier: set[tuple[str, str, str]] = set()
    for source in state.cities.values():
        for good in set(source.goods):
            for target in state.cities.values():
                if source.id == target.id or target.demand_color != good:
                    continue
                try:
                    distance = int(
                        nx.shortest_path_length(
                            graph,
                            source.id,
                            target.id,
                            weight="weight",
                        )
                    )
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue
                if current_level < distance <= new_level:
                    frontier.add((source.id, target.id, good))
    return len(frontier)


def _distance_reduction(before: float, after: float) -> float:
    if not math.isfinite(before) or not math.isfinite(after):
        return 0.0
    return max(0.0, before - after)


def _leaves_unfocused_incomplete_track(
    state: GameState,
    segment_ids: list[str],
    objective_progress: float,
) -> bool:
    route_ids = {
        state.segments[segment_id].route_id
        for segment_id in segment_ids
        if segment_id in state.segments
    }
    return objective_progress <= 0 and any(
        route_id in state.routes and not state.routes[route_id].completed
        for route_id in route_ids
    )


def _segment_ids(action: Action) -> list[str]:
    value = action.params.get("segment_ids", [])
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _action_sort_key(
    action: Action,
) -> tuple[str, str, str, str, str, tuple[str, ...]]:
    return (
        action.action_type,
        "-".join(_segment_ids(action)),
        str(action.params.get("source", "")),
        str(action.params.get("target", "")),
        str(action.params.get("good_color", "")),
        tuple(str(item) for item in action.params.get("path", [])),
    )


def _first_action(actions: list[Action], action_type: str) -> Action | None:
    return next(
        (action for action in actions if action.action_type == action_type),
        None,
    )
