from __future__ import annotations

import json
from pathlib import Path

from railways.models import (
    City,
    GameConfig,
    MajorLine,
    RailwayEdge,
    Route,
    TrackSegment,
)


def load_map(
    path: str | Path,
    *,
    include_routes: bool = False,
) -> (
    tuple[dict[str, City], dict[str, RailwayEdge], dict[str, MajorLine]]
    | tuple[
        dict[str, City],
        dict[str, RailwayEdge],
        dict[str, MajorLine],
        dict[str, Route],
        dict[str, TrackSegment],
    ]
):
    """Load a legacy edge map or a route-segment map.

    The default three-item return preserves the original public API. Callers
    that need route data can pass ``include_routes=True`` for the extended
    five-item result.
    """
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
            owner=edge_data.get("owner") or ("player" if edge_data.get("built") else None),
        )
        for edge_data in data.get("edges", [])
    }

    routes: dict[str, Route] = {}
    segments: dict[str, TrackSegment] = {}
    for route_data in data.get("routes", []):
        route_id = str(route_data["id"])
        city_a = str(route_data["city_a"])
        city_b = str(route_data["city_b"])
        segment_data_items = list(route_data.get("segments", []))
        segment_ids: list[str] = []

        for index, segment_data in enumerate(segment_data_items):
            segment_id = str(segment_data["id"])
            generated_source = city_a if index == 0 else f"{route_id}:n{index}"
            generated_target = (
                city_b
                if index == len(segment_data_items) - 1
                else f"{route_id}:n{index + 1}"
            )
            segments[segment_id] = TrackSegment(
                id=segment_id,
                route_id=route_id,
                index=index,
                source_node=str(segment_data.get("source_node", generated_source)),
                target_node=str(segment_data.get("target_node", generated_target)),
                terrain=str(segment_data.get("terrain", "plain")),
                cost=int(segment_data["cost"]),
                built=bool(segment_data.get("built", False)),
                owner=segment_data.get("owner"),
                completed=bool(segment_data.get("completed", False)),
            )
            segment_ids.append(segment_id)

        routes[route_id] = Route(
            id=route_id,
            city_a=city_a,
            city_b=city_b,
            segment_ids=segment_ids,
            completed=bool(route_data.get("completed", False)),
        )

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

    if include_routes:
        return cities, edges, major_lines, routes, segments
    return cities, edges, major_lines


def load_config(path: str | Path) -> GameConfig:
    """Load game configuration from JSON."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return GameConfig(**data)
