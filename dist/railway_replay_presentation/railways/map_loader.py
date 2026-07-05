from __future__ import annotations

import json
from pathlib import Path

from railways.models import (
    City,
    GameConfig,
    MajorLine,
    RailBaronObjective,
    RailwayEdge,
    Route,
    TrackSegment,
)


def load_map(
    path: str | Path,
    *,
    include_routes: bool = False,
    include_rail_baron_objectives: bool = False,
) -> (
    tuple[dict[str, City], dict[str, RailwayEdge], dict[str, MajorLine]]
    | tuple[
        dict[str, City],
        dict[str, RailwayEdge],
        dict[str, MajorLine],
        dict[str, Route],
        dict[str, TrackSegment],
    ]
    | tuple[
        dict[str, City],
        dict[str, RailwayEdge],
        dict[str, MajorLine],
        dict[str, RailBaronObjective],
    ]
    | tuple[
        dict[str, City],
        dict[str, RailwayEdge],
        dict[str, MajorLine],
        dict[str, Route],
        dict[str, TrackSegment],
        dict[str, RailBaronObjective],
    ]
):
    """Load a route-segment map for the official-style runtime."""
    map_path = Path(path)
    with map_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    route_data_items = data.get("routes")
    if not isinstance(route_data_items, list) or not route_data_items:
        raise ValueError(
            "Route-segment runtime requires routes and track_segments. "
            "Legacy edge-only maps are not supported."
        )
    if any(not route_data.get("segments") for route_data in route_data_items):
        raise ValueError(
            "Route-segment runtime requires every route to contain track segments."
        )

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

    # RailwayEdge remains in the state model for serialized compatibility, but
    # edge data never drives construction or delivery in this runtime.
    edges: dict[str, RailwayEdge] = {}

    routes: dict[str, Route] = {}
    segments: dict[str, TrackSegment] = {}
    for route_data in route_data_items:
        route_id = str(route_data["id"])
        city_a = str(route_data["city_a"])
        city_b = str(route_data["city_b"])
        if route_id in routes:
            raise ValueError(f"Duplicate route ID: {route_id}")
        if city_a not in cities or city_b not in cities:
            raise ValueError(f"Route {route_id} references an unknown city.")
        segment_data_items = list(route_data.get("segments", []))
        segment_ids: list[str] = []

        for index, segment_data in enumerate(segment_data_items):
            segment_id = str(segment_data["id"])
            if segment_id in segments:
                raise ValueError(f"Duplicate track segment ID: {segment_id}")
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

    rail_baron_objectives: dict[str, RailBaronObjective] = {}
    for objective_data in data.get("rail_baron_objectives", []):
        objective_id = str(objective_data["id"])
        source = str(objective_data["source"])
        target = str(objective_data["target"])
        bonus_points = int(objective_data["bonus_points"])
        if objective_id in rail_baron_objectives:
            raise ValueError(f"Duplicate Rail Baron objective ID: {objective_id}")
        if source not in cities or target not in cities:
            raise ValueError(
                f"Rail Baron objective {objective_id} references an unknown city."
            )
        if bonus_points <= 0:
            raise ValueError(
                f"Rail Baron objective {objective_id} must have a positive bonus."
            )
        rail_baron_objectives[objective_id] = RailBaronObjective(
            id=objective_id,
            source=source,
            target=target,
            bonus_points=bonus_points,
            claimed=bool(objective_data.get("claimed", False)),
        )

    if include_routes:
        if include_rail_baron_objectives:
            return (
                cities,
                edges,
                major_lines,
                routes,
                segments,
                rail_baron_objectives,
            )
        return cities, edges, major_lines, routes, segments
    if include_rail_baron_objectives:
        return cities, edges, major_lines, rail_baron_objectives
    return cities, edges, major_lines


def load_config(path: str | Path) -> GameConfig:
    """Load game configuration from JSON."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return GameConfig(**data)
