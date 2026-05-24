from __future__ import annotations

from railways.game_state import GameState
from railways.rules import (
    Action,
    build_track,
    get_legal_build_actions,
    get_legal_deliveries,
)


def choose_greedy_action(state: GameState) -> Action:
    deliveries = get_legal_deliveries(state)
    if deliveries:
        return max(deliveries, key=lambda action: (action["score"], action["path_length"]))

    build_actions = _ranked_build_actions(state)
    if build_actions:
        return build_actions[0]

    upgrade_cost = state.player.locomotive_level * state.config.upgrade_cost_multiplier
    if (
        state.player.locomotive_level < state.config.max_locomotive_level
        and state.player.money >= upgrade_cost
    ):
        return {"type": "upgrade_locomotive"}

    if state.player.money < _cheapest_unbuilt_edge_cost(state):
        return {"type": "issue_bond"}

    return {"type": "next_turn"}


def _ranked_build_actions(state: GameState) -> list[Action]:
    candidates = []
    for edge in get_legal_build_actions(state):
        simulated = state.copy()
        build_track(simulated, edge.id)
        deliveries_after_build = get_legal_deliveries(simulated)
        delivery_count = len(deliveries_after_build)
        best_delivery_score = max(
            (delivery["score"] for delivery in deliveries_after_build),
            default=0,
        )

        candidates.append(
            {
                "action": {"type": "build", "edge_id": edge.id},
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
