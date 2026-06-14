from __future__ import annotations

from agents.base_agent import BaseAgent
from railways.actions import Action
from railways.environment import apply_action, copy_state
from railways.game_state import GameState
from railways.rules import (
    get_legal_build_actions,
    get_legal_deliveries,
    get_legal_upgrade_action,
    get_legal_urbanize_actions,
)


class GreedyExpansionAgent(BaseAgent):
    name = "greedy_expansion"

    def choose_action(self, state: GameState) -> Action:
        build_actions = _ranked_expansion_build_actions(state)
        if build_actions:
            return build_actions[0]

        deliveries = get_legal_deliveries(state)
        if deliveries:
            return max(deliveries, key=_delivery_rank)

        upgrade_action = get_legal_upgrade_action(state)
        if upgrade_action is not None:
            return upgrade_action

        urbanize_actions = get_legal_urbanize_actions(state)
        if urbanize_actions:
            return sorted(
                urbanize_actions,
                key=lambda action: str(action.params.get("city_id", "")),
            )[0]

        return Action.pass_action()


def _ranked_expansion_build_actions(state: GameState) -> list[Action]:
    candidates: list[tuple[float, str, Action]] = []
    current_cities = set(_connected_player_cities(state))
    current_major_bonus = state.player.major_line_bonus

    for action in get_legal_build_actions(state):
        edge = state.edges[action.params["edge_id"]]
        simulated = copy_state(state)
        _, success, _ = apply_action(simulated, action)
        if not success:
            continue

        deliveries_after_build = get_legal_deliveries(simulated)
        delivery_count = len(deliveries_after_build)
        best_delivery_score = max(
            (delivery.params.get("score", 0) for delivery in deliveries_after_build),
            default=0,
        )
        major_line_bonus_gain = (
            simulated.player.major_line_bonus - current_major_bonus
        )
        new_city_count = len(set(_connected_player_cities(simulated)) - current_cities)

        heuristic_score = (
            10 * major_line_bonus_gain
            + 3 * delivery_count
            + 2 * best_delivery_score
            + new_city_count
            - 0.2 * edge.cost
        )
        candidates.append((heuristic_score, str(action.params["edge_id"]), action))

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [candidate[2] for candidate in candidates]


def _connected_player_cities(state: GameState) -> set[str]:
    cities: set[str] = set()
    for edge in state.edges.values():
        if edge.built and edge.owner == "player":
            cities.add(edge.source)
            cities.add(edge.target)
    return cities


def _delivery_rank(action: Action) -> tuple[int, int, str, str, str]:
    path = action.params.get("path", [])
    return (
        int(action.params.get("score", 0)),
        -int(action.params.get("path_length", 0)),
        str(action.params.get("source", "")),
        str(action.params.get("target", "")),
        "-".join(path),
    )
