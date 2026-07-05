from __future__ import annotations

from agents.base_agent import BaseAgent
from railways.actions import Action
from railways.game_state import GameState
from railways.rules import (
    get_legal_operation_card_actions,
    get_legal_build_segment_actions,
    get_legal_deliveries,
    get_legal_upgrade_action,
    get_legal_urbanize_actions,
)


class GreedyDeliveryAgent(BaseAgent):
    name = "greedy_delivery"

    def choose_action(self, state: GameState) -> Action:
        deliveries = get_legal_deliveries(state)
        if deliveries:
            return max(deliveries, key=_delivery_rank)

        build_actions = _ranked_simple_build_actions(state)
        if build_actions:
            return build_actions[0]

        upgrade_action = get_legal_upgrade_action(state)
        if upgrade_action is not None:
            return upgrade_action

        card_actions = get_legal_operation_card_actions(state)
        if card_actions:
            return sorted(
                card_actions,
                key=lambda action: str(action.params.get("card_id", "")),
            )[0]

        urbanize_actions = get_legal_urbanize_actions(state)
        if urbanize_actions:
            return sorted(
                urbanize_actions,
                key=lambda action: str(action.params.get("city_id", "")),
            )[0]

        return Action.pass_action()


def choose_greedy_delivery_action(state: GameState) -> Action:
    return GreedyDeliveryAgent().choose_action(state)


def _delivery_rank(action: Action) -> tuple[int, int, str, str, str]:
    path = action.params.get("path", [])
    return (
        int(action.params.get("score", 0)),
        -int(action.params.get("path_length", 0)),
        str(action.params.get("source", "")),
        str(action.params.get("target", "")),
        "-".join(path),
    )


def _ranked_simple_build_actions(state: GameState) -> list[Action]:
    actions = get_legal_build_segment_actions(state)
    return sorted(
        actions,
        key=lambda action: (
            sum(
                state.segments[segment_id].cost
                for segment_id in action.params["segment_ids"]
            ),
            tuple(action.params["segment_ids"]),
        ),
    )
