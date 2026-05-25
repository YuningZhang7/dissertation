from __future__ import annotations

from agents.greedy_delivery_agent import GreedyDeliveryAgent
from railways.actions import Action
from railways.game_state import GameState


class GreedyAgent(GreedyDeliveryAgent):
    name = "greedy"


def choose_greedy_action(state: GameState) -> Action:
    return GreedyAgent().choose_action(state)
