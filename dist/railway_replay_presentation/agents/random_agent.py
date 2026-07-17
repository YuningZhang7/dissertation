from __future__ import annotations

import random

from agents.base_agent import BaseAgent
from railways.actions import Action
from railways.environment import get_legal_actions
from railways.game_state import GameState


class RandomAgent(BaseAgent):
    name = "random"

    def choose_action(self, state: GameState) -> Action:
        legal_actions = get_legal_actions(state)
        if not legal_actions:
            return Action.pass_action()
        return self.rng.choice(legal_actions)


def choose_random_action(
    state: GameState,
    rng: random.Random | None = None,
) -> Action:
    seed_agent = RandomAgent()
    if rng is not None:
        seed_agent.rng = rng
    return seed_agent.choose_action(state)
