from __future__ import annotations

import json
from pathlib import Path

from railways.models import City, GameConfig, RailwayEdge


def load_map(path: str | Path) -> tuple[dict[str, City], dict[str, RailwayEdge]]:
    """Load city and edge data from a JSON map file."""
    map_path = Path(path)
    with map_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    cities = {
        city_data["id"]: City(
            id=city_data["id"],
            name=city_data["name"],
            x=float(city_data["x"]),
            y=float(city_data["y"]),
            demand_color=city_data["demand_color"],
            goods=list(city_data.get("goods", [])),
        )
        for city_data in data["cities"]
    }

    edges = {
        edge_data["id"]: RailwayEdge(
            id=edge_data["id"],
            source=edge_data["source"],
            target=edge_data["target"],
            cost=int(edge_data["cost"]),
            built=bool(edge_data.get("built", False)),
        )
        for edge_data in data["edges"]
    }

    return cities, edges


def load_config(path: str | Path) -> GameConfig:
    """Load game configuration from JSON."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return GameConfig(**data)
