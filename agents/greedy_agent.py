from __future__ import annotations

from railways.actions import Action
from railways.environment import apply_action
from railways.game_state import GameState
from railways.rules import (
    get_legal_build_actions,
    get_legal_deliveries,
    get_legal_upgrade_action,
    get_legal_urbanize_actions,
)


def choose_greedy_action(state: GameState) -> Action:
    deliveries = get_legal_deliveries(state)
    if deliveries:
        return max(
            deliveries,
            key=lambda action: (
                action.params["score"],
                action.params["path_length"],
            ),
        )

    build_actions = _ranked_build_actions(state)
    if build_actions:
        return build_actions[0]

    upgrade_action = get_legal_upgrade_action(state)
    if upgrade_action is not None:
        return upgrade_action

    urbanize_actions = get_legal_urbanize_actions(state)
    if urbanize_actions:
        return urbanize_actions[0]

    if state.player.money < _cheapest_unbuilt_edge_cost(state):
        return Action.issue_bond()

    return Action.pass_action()


def _ranked_build_actions(state: GameState) -> list[Action]:
    candidates = []
    for action in get_legal_build_actions(state):
        simulated = state.copy()
        apply_action(simulated, action)
        deliveries_after_build = get_legal_deliveries(simulated)
        delivery_count = len(deliveries_after_build)
        best_delivery_score = max(
            (delivery.params["score"] for delivery in deliveries_after_build),
            default=0,
        )
        edge = state.edges[action.params["edge_id"]]

        candidates.append(
            {
                "action": action,
                "delivery_count": delivery_count,
                "best_delivery_score": best_delivery_score,
                "cost": edge.cost,
            }
        )

    candidates.sort(
        key=lambda item: (
            item["delivery_count"],
            item["best_delivery_score"],
            -item["cost"],
        ),
        reverse=True,
    )
    return [candidate["action"] for candidate in candidates]


def _cheapest_unbuilt_edge_cost(state: GameState) -> int:
    costs = [edge.cost for edge in state.edges.values() if not edge.built]
    return min(costs, default=0)
