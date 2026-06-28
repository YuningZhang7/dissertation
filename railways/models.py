from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


PHASE_ACTION = "action"
PHASE_INCOME = "income"
PHASE_GAME_OVER = "game_over"


@dataclass
class City:
    id: str
    name: str
    x: float
    y: float
    demand_color: str | None
    goods: list[str] = field(default_factory=list)
    is_gray: bool = False
    is_urbanized: bool = True
    empty_marker: bool = False


@dataclass
class RailwayEdge:
    id: str
    source: str
    target: str
    cost: int
    built: bool = False
    owner: str | None = None


@dataclass
class TrackSegment:
    id: str
    route_id: str
    index: int
    source_node: str
    target_node: str
    terrain: str
    cost: int
    built: bool = False
    owner: str | None = None
    completed: bool = False


@dataclass
class Route:
    id: str
    city_a: str
    city_b: str
    segment_ids: list[str] = field(default_factory=list)
    completed: bool = False


@dataclass
class MajorLine:
    id: str
    source: str
    target: str
    bonus_points: int
    claimed: bool = False


@dataclass
class OperationCard:
    id: str
    name: str
    card_type: str
    description: str
    condition: dict[str, Any] = field(default_factory=dict)
    reward: dict[str, Any] = field(default_factory=dict)
    effect: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlayerCardState:
    card_id: str
    status: str
    progress: int = 0
    awarded_points: int = 0


@dataclass
class PlayerState:
    money: int = 20
    score: int = 0
    bonds: int = 0
    locomotive_level: int = 1
    delivered_goods_count: int = 0
    built_edges: set[str] = field(default_factory=set)
    major_line_bonus: int = 0
    rail_baron_bonus: int = 0
    operation_card_bonus: int = 0
    owned_operation_cards: list[str] = field(default_factory=list)
    active_operation_cards: dict[str, PlayerCardState] = field(default_factory=dict)
    completed_operation_cards: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class GameConfig:
    initial_money: int = 20
    initial_score: int = 0
    initial_bonds: int = 0
    initial_locomotive_level: int = 1
    initial_turn: int = 1
    actions_per_turn: int = 3
    bond_value: int = 5
    bond_interest: int = 1
    bond_final_penalty: int = 1
    allow_voluntary_bonds: bool = False
    auto_issue_bonds_when_needed: bool = True
    require_connected_track_building: bool = True
    max_locomotive_level: int = 6
    engine_upgrade_costs: dict[str, int] = field(default_factory=dict)
    urbanize_cost: int = 10
    new_goods_on_urbanize: int = 2
    allowed_good_colors: list[str] = field(
        default_factory=lambda: ["red", "blue", "yellow", "green"]
    )
    delivery_score_mode: str = "path_length"
    minimum_delivery_score: int = 1
    income_mode: str = "score_based"
    income_table: dict[str, int] = field(default_factory=dict)
    end_condition: str = "fixed_turns"
    max_turns: int = 10
    empty_city_marker_limit: int = 10
    extra_turn_after_end_trigger: bool = True

    def create_initial_player(self) -> PlayerState:
        return PlayerState(
            money=self.initial_money,
            score=self.initial_score,
            bonds=self.initial_bonds,
            locomotive_level=self.initial_locomotive_level,
        )
