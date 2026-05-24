from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class City:
    id: str
    name: str
    x: float
    y: float
    demand_color: str
    goods: list[str] = field(default_factory=list)


@dataclass
class RailwayEdge:
    id: str
    source: str
    target: str
    cost: int
    built: bool = False


@dataclass
class PlayerState:
    money: int = 20
    score: int = 0
    bonds: int = 0
    locomotive_level: int = 1
    turn: int = 1
    max_turns: int = 10
    built_edges: set[str] = field(default_factory=set)
    delivered_goods_count: int = 0
    action_history: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GameConfig:
    starting_money: int = 20
    starting_score: int = 0
    starting_bonds: int = 0
    starting_locomotive_level: int = 1
    starting_turn: int = 1
    max_turns: int = 10
    bond_value: int = 5
    bond_penalty: int = 1
    upgrade_cost_multiplier: int = 4
    max_locomotive_level: int = 5
    minimum_delivery_score: int = 1

    def create_initial_player(self) -> PlayerState:
        return PlayerState(
            money=self.starting_money,
            score=self.starting_score,
            bonds=self.starting_bonds,
            locomotive_level=self.starting_locomotive_level,
            turn=self.starting_turn,
            max_turns=self.max_turns,
        )
