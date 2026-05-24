from __future__ import annotations

import random

from railways.game_state import GameState
from railways.rules import Action, get_legal_build_actions, get_legal_deliveries


def choose_random_action(
    state: GameState,
    rng: random.Random | None = None,
) -> Action:
    generator = rng or random.Random()
    actions: list[Action] = []

    actions.extend(get_legal_deliveries(state))
    actions.extend(
        {"type": "build", "edge_id": edge.id} for edge in get_legal_build_actions(state)
    )

    if state.player.money >= state.player.locomotive_level * state.config.upgrade_cost_multiplier:
        if state.player.locomotive_level < state.config.max_locomotive_level:
            actions.append({"type": "upgrade_locomotive"})

    actions.append({"type": "issue_bond"})
    actions.append({"type": "next_turn"})

    return generator.choice(actions)
