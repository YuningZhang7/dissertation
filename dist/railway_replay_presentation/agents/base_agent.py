from __future__ import annotations

from abc import ABC, abstractmethod
import random

from railways.actions import Action
from railways.game_state import GameState


class BaseAgent(ABC):
    name: str = "base"

    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed
        self.rng = random.Random(seed)

    @abstractmethod
    def choose_action(self, state: GameState) -> Action:
        raise NotImplementedError
