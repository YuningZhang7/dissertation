from __future__ import annotations

import random

from railways.actions import Action
from railways.environment import get_legal_actions
from railways.game_state import GameState


def choose_random_action(
    state: GameState,
    rng: random.Random | None = None,
) -> Action:
    generator = rng or random.Random()
    legal_actions = get_legal_actions(state)
    if not legal_actions:
        return Action.pass_action()
    return generator.choice(legal_actions)
