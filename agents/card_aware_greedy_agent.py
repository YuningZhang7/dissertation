from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.card_heuristics import (
    MIN_HIGH_VALUE_DELIVERY_SCORE,
    card_action_candidates,
    card_completion_candidates,
    ranked_card_related_build_actions,
    ranked_delivery_actions,
)
from railways.actions import Action
from railways.game_state import GameState
from railways.rules import (
    get_legal_deliveries,
    get_legal_upgrade_action,
    get_legal_urbanize_actions,
)


class CardAwareGreedyAgent(BaseAgent):
    name = "card_aware_greedy"

    def choose_action(self, state: GameState) -> Action:
        completing_actions = card_completion_candidates(state)
        if completing_actions:
            return completing_actions[0]

        deliveries = ranked_delivery_actions(get_legal_deliveries(state))
        if (
            deliveries
            and int(deliveries[0].params.get("score", 0))
            >= MIN_HIGH_VALUE_DELIVERY_SCORE
        ):
            return deliveries[0]

        card_candidates = card_action_candidates(state)
        if card_candidates:
            return card_candidates[0][1]

        build_actions = ranked_card_related_build_actions(state)
        if build_actions:
            return build_actions[0]

        if deliveries:
            return deliveries[0]

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
