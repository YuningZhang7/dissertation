from __future__ import annotations

import json
from pathlib import Path

from railways.models import City, GameConfig, MajorLine, RailwayEdge


def load_map(
    path: str | Path,
) -> tuple[dict[str, City], dict[str, RailwayEdge], dict[str, MajorLine]]:
    """Load city, edge, and optional major-line data from a JSON map file."""
    map_path = Path(path)
    with map_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    cities = {
        city_data["id"]: City(
            id=city_data["id"],
            name=city_data["name"],
            x=float(city_data["x"]),
            y=float(city_data["y"]),
            demand_color=city_data.get("demand_color"),
            goods=list(city_data.get("goods", [])),
            is_gray=bool(city_data.get("is_gray", False)),
            is_urbanized=bool(city_data.get("is_urbanized", True)),
            empty_marker=bool(city_data.get("empty_marker", False)),
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
            owner=edge_data.get("owner"),
        )
        for edge_data in data["edges"]
    }

    major_lines = {
        line_data["id"]: MajorLine(
            id=line_data["id"],
            source=line_data["source"],
            target=line_data["target"],
            bonus_points=int(line_data["bonus_points"]),
            claimed=bool(line_data.get("claimed", False)),
        )
        for line_data in data.get("major_lines", [])
    }

    return cities, edges, major_lines


def load_config(path: str | Path) -> GameConfig:
    """Load game configuration from JSON."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return GameConfig(**data)
