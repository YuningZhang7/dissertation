from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from railways.map_loader import load_config, load_map
from railways.models import City, GameConfig, PlayerState, RailwayEdge
from railways.scoring import compute_final_score


class GameState:
    """Mutable game state for one single-player simulation."""

    def __init__(
        self,
        cities: dict[str, City],
        edges: dict[str, RailwayEdge],
        config: GameConfig | None = None,
        player: PlayerState | None = None,
    ) -> None:
        self.config = config or GameConfig()
        self._initial_cities = deepcopy(cities)
        self._initial_edges = deepcopy(edges)
        self.cities = deepcopy(cities)
        self.edges = deepcopy(edges)
        self.player = deepcopy(player) if player else self.config.create_initial_player()
        self._sync_built_edges()

    @classmethod
    def from_files(
        cls,
        map_path: str | Path,
        config_path: str | Path,
    ) -> "GameState":
        cities, edges = load_map(map_path)
        config = load_config(config_path)
        return cls(cities=cities, edges=edges, config=config)

    def reset(self) -> None:
        self.cities = deepcopy(self._initial_cities)
        self.edges = deepcopy(self._initial_edges)
        self.player = self.config.create_initial_player()
        self._sync_built_edges()

    def copy(self) -> "GameState":
        return deepcopy(self)

    def is_terminal(self) -> bool:
        return self.player.turn > self.player.max_turns

    def final_score(self) -> int:
        return compute_final_score(self.player, self.config)

    def get_city(self, city_id: str) -> City | None:
        return self.cities.get(city_id)

    def get_edge(self, edge_id: str) -> RailwayEdge | None:
        return self.edges.get(edge_id)

    def _sync_built_edges(self) -> None:
        self.player.built_edges = {
            edge_id for edge_id, edge in self.edges.items() if edge.built
        }
