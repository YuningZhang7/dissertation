from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from railways.card_loader import load_cards
from railways.map_loader import load_config, load_map
from railways.models import (
    City,
    GameConfig,
    MajorLine,
    OperationCard,
    PHASE_ACTION,
    PHASE_GAME_OVER,
    PlayerState,
    RailwayEdge,
    Route,
    TrackSegment,
)
from railways.scoring import compute_final_score


class GameState:
    """Mutable state for one single-player rules simulation."""

    def __init__(
        self,
        cities: dict[str, City],
        edges: dict[str, RailwayEdge],
        config: GameConfig | None = None,
        player: PlayerState | None = None,
        major_lines: dict[str, MajorLine] | None = None,
        operation_cards: dict[str, OperationCard] | None = None,
        available_operation_cards: list[str] | None = None,
        turn: int | None = None,
        phase: str = PHASE_ACTION,
        actions_remaining: int | None = None,
        end_triggered: bool = False,
        extra_turns_remaining: int = 0,
        action_history: list[str] | None = None,
        routes: dict[str, Route] | None = None,
        segments: dict[str, TrackSegment] | None = None,
    ) -> None:
        self.config = config or GameConfig()
        self._initial_cities = deepcopy(cities)
        self._initial_edges = deepcopy(edges)
        self._initial_routes = deepcopy(routes or {})
        self._initial_segments = deepcopy(segments or {})
        self._initial_major_lines = deepcopy(major_lines or {})
        self._initial_operation_cards = deepcopy(operation_cards or {})
        self._initial_available_operation_cards = list(
            available_operation_cards
            if available_operation_cards is not None
            else sorted((operation_cards or {}).keys())
        )
        self.cities = deepcopy(cities)
        self.edges = deepcopy(edges)
        self.routes = deepcopy(routes or {})
        self.segments = deepcopy(segments or {})
        self.major_lines = deepcopy(major_lines or {})
        self.operation_cards = deepcopy(operation_cards or {})
        self.available_operation_cards = list(self._initial_available_operation_cards)
        self.player = deepcopy(player) if player else self.config.create_initial_player()
        self.turn = turn if turn is not None else self.config.initial_turn
        self.phase = phase
        self.actions_remaining = (
            actions_remaining
            if actions_remaining is not None
            else self.config.actions_per_turn
        )
        self.end_triggered = end_triggered
        self.extra_turns_remaining = extra_turns_remaining
        self.action_history = list(action_history or [])
        self._sync_built_edges()

    @classmethod
    def from_files(
        cls,
        map_path: str | Path,
        config_path: str | Path,
        card_path: str | Path | None = None,
    ) -> "GameState":
        cities, edges, major_lines, routes, segments = load_map(
            map_path,
            include_routes=True,
        )
        config = load_config(config_path)
        operation_cards = load_cards(card_path) if card_path is not None else {}
        return cls(
            cities=cities,
            edges=edges,
            major_lines=major_lines,
            routes=routes,
            segments=segments,
            config=config,
            operation_cards=operation_cards,
        )

    def reset(self) -> None:
        self.cities = deepcopy(self._initial_cities)
        self.edges = deepcopy(self._initial_edges)
        self.routes = deepcopy(self._initial_routes)
        self.segments = deepcopy(self._initial_segments)
        self.major_lines = deepcopy(self._initial_major_lines)
        self.operation_cards = deepcopy(self._initial_operation_cards)
        self.available_operation_cards = list(self._initial_available_operation_cards)
        self.player = self.config.create_initial_player()
        self.turn = self.config.initial_turn
        self.phase = PHASE_ACTION
        self.actions_remaining = self.config.actions_per_turn
        self.end_triggered = False
        self.extra_turns_remaining = 0
        self.action_history = []
        self._sync_built_edges()

    def copy(self) -> "GameState":
        return deepcopy(self)

    def is_terminal(self) -> bool:
        return self.phase == PHASE_GAME_OVER

    def final_score(self) -> int:
        return compute_final_score(self)

    def get_city(self, city_id: str) -> City | None:
        return self.cities.get(city_id)

    def get_edge(self, edge_id: str) -> RailwayEdge | None:
        return self.edges.get(edge_id)

    def record(self, message: str) -> None:
        self.action_history.append(message)

    def _sync_built_edges(self) -> None:
        self.player.built_edges = {
            edge_id for edge_id, edge in self.edges.items() if edge.built
        }
