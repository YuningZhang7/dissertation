from __future__ import annotations

from agents.base_agent import BaseAgent
from railways.actions import Action
from railways.environment import get_legal_actions
from railways.game_state import GameState
from railways.models import TrackSegment


class RouteSegmentGreedyAgent(BaseAgent):
    """Deterministic heuristic agent for route-segment maps."""

    name = "route_segment_greedy"

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
            return sorted(deliveries, key=_delivery_sort_key)[0]

        build_actions = [
            action
            for action in legal_actions
            if action.action_type == "build_track_segments"
        ]
        scored_builds = [
            (_score_segment_build(state, action), action)
            for action in build_actions
        ]

        completing_builds = [
            candidate
            for candidate in scored_builds
            if _build_completes_route(state, candidate[1])
        ]
        if completing_builds:
            return _best_build(completing_builds)

        extending_builds = [
            candidate
            for candidate in scored_builds
            if _build_extends_incomplete_route(state, candidate[1])
        ]
        if extending_builds:
            return _best_build(extending_builds)

        useful_builds = [
            candidate for candidate in scored_builds if candidate[0] > 0
        ]
        if useful_builds:
            return _best_build(useful_builds)

        upgrade = _first_action(legal_actions, "upgrade_engine")
        if upgrade is not None:
            return upgrade

        pass_action = _first_action(legal_actions, "pass")
        if pass_action is not None:
            return pass_action

        non_bond_actions = [
            action
            for action in legal_actions
            if action.action_type not in {"issue_bond", "next_turn"}
        ]
        if non_bond_actions:
            return sorted(non_bond_actions, key=_action_sort_key)[0]

        next_turn = _first_action(legal_actions, "next_turn")
        if next_turn is not None:
            return next_turn

        return sorted(legal_actions, key=_action_sort_key)[0]


def _delivery_sort_key(
    action: Action,
) -> tuple[int, int, str, str, str, tuple[str, ...]]:
    return (
        -int(action.params.get("score", 0)),
        int(action.params.get("path_length", 0)),
        str(action.params.get("source", "")),
        str(action.params.get("target", "")),
        str(action.params.get("good_color", "")),
        tuple(str(item) for item in action.params.get("path", [])),
    )


def _score_segment_build(state: GameState, action: Action) -> float:
    segments = _action_segments(state, action)
    if not segments:
        return float("-inf")

    route = state.routes.get(segments[0].route_id)
    if route is None:
        return float("-inf")

    score = 0.0
    if _build_completes_route(state, action):
        score += 100.0
    if _build_extends_incomplete_route(state, action):
        score += 30.0

    endpoint_cities = [
        state.cities[city_id]
        for city_id in (route.city_a, route.city_b)
        if city_id in state.cities
    ]
    if any(city.goods for city in endpoint_cities):
        score += 20.0

    available_goods = {
        good
        for city in state.cities.values()
        for good in city.goods
    }
    if any(
        city.demand_color is not None and city.demand_color in available_goods
        for city in endpoint_cities
    ):
        score += 20.0

    score -= sum(segment.cost for segment in segments)
    score -= 0.1 * len(segments)
    return score


def _build_completes_route(state: GameState, action: Action) -> bool:
    segments = _action_segments(state, action)
    if not segments:
        return False
    route = state.routes.get(segments[0].route_id)
    if route is None or route.completed:
        return False
    action_segment_ids = {segment.id for segment in segments}
    return bool(route.segment_ids) and all(
        segment_id in state.segments
        and (state.segments[segment_id].built or segment_id in action_segment_ids)
        for segment_id in route.segment_ids
    )


def _build_extends_incomplete_route(state: GameState, action: Action) -> bool:
    segments = _action_segments(state, action)
    if not segments:
        return False
    route = state.routes.get(segments[0].route_id)
    if route is None or route.completed:
        return False
    return any(
        state.segments[segment_id].built
        and not state.segments[segment_id].completed
        for segment_id in route.segment_ids
        if segment_id in state.segments
    )


def _action_segments(state: GameState, action: Action) -> list[TrackSegment]:
    if action.action_type != "build_track_segments":
        return []
    segment_ids = action.params.get("segment_ids", [])
    if not isinstance(segment_ids, list):
        return []
    return [
        state.segments[segment_id]
        for segment_id in segment_ids
        if segment_id in state.segments
    ]


def _best_build(candidates: list[tuple[float, Action]]) -> Action:
    return sorted(
        candidates,
        key=lambda candidate: (-candidate[0], _action_sort_key(candidate[1])),
    )[0][1]


def _action_sort_key(action: Action) -> tuple[str, str]:
    segment_ids = action.params.get("segment_ids", [])
    return action.action_type, "-".join(str(item) for item in segment_ids)


def _first_action(actions: list[Action], action_type: str) -> Action | None:
    return next(
        (action for action in actions if action.action_type == action_type),
        None,
    )
