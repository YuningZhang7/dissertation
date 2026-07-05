from __future__ import annotations

from pathlib import Path

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from railways.game_state import GameState
from railways.rules import get_active_rail_baron_objective, get_route_segments

DEMAND_COLORS = {
    "red": "#d62728",
    "blue": "#1f77b4",
    "yellow": "#f2c94c",
    "green": "#2ca02c",
    "black": "#303030",
    "purple": "#9467bd",
    None: "#9aa0a6",
}

TRACK_STYLES = {
    "unbuilt": {"color": "#c9cdd2", "linewidth": 1.2, "linestyle": "--"},
    "incomplete": {"color": "#f28e2b", "linewidth": 3.0, "linestyle": "-"},
    "completed": {"color": "#174a7e", "linewidth": 3.8, "linestyle": "-"},
}


def render_game_state(
    state: GameState,
    output_path: str | Path,
    show_routes: bool = True,
    show_segments: bool = True,
    show_major_lines: bool = True,
    show_rail_baron: bool = True,
    show_goods: bool = True,
) -> Path:
    """Render a stable, presentation-friendly PNG snapshot of ``state``."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    figure = Figure(figsize=(15, 9), facecolor="#f7f8fa")
    FigureCanvasAgg(figure)
    axis = figure.add_subplot(111)
    axis.set_facecolor("#f7f8fa")
    axis.set_aspect("equal", adjustable="box")
    axis.axis("off")

    if show_major_lines:
        _draw_major_lines(axis, state)
    if show_routes:
        _draw_routes(axis, state, show_segments=show_segments)
    if show_rail_baron:
        _draw_rail_baron(axis, state)
    _draw_cities(axis, state, show_goods=show_goods)
    _draw_summary(axis, state, show_rail_baron=show_rail_baron)
    _draw_legend(axis, show_major_lines, show_rail_baron)
    _set_map_bounds(axis, state)

    figure.savefig(path, dpi=160, bbox_inches="tight", facecolor=figure.get_facecolor())
    return path


def _draw_routes(axis, state: GameState, *, show_segments: bool) -> None:
    label_routes = len(state.routes) <= 20
    for route in state.routes.values():
        segments = get_route_segments(state, route.id)
        if not segments:
            continue
        points = _interpolated_route_points(
            state,
            route.city_a,
            route.city_b,
            len(segments),
        )
        if show_segments:
            for index, segment in enumerate(segments):
                status = _segment_status(segment)
                axis.plot(
                    [points[index][0], points[index + 1][0]],
                    [points[index][1], points[index + 1][1]],
                    zorder=2,
                    solid_capstyle="round",
                    **TRACK_STYLES[status],
                )
        else:
            status = _route_status(route, segments)
            axis.plot(
                [points[0][0], points[-1][0]],
                [points[0][1], points[-1][1]],
                zorder=2,
                solid_capstyle="round",
                **TRACK_STYLES[status],
            )

        if label_routes:
            midpoint = points[len(points) // 2]
            axis.text(
                midpoint[0],
                midpoint[1],
                route.id,
                fontsize=6,
                color="#5f6368",
                ha="center",
                va="center",
                zorder=3,
                bbox={
                    "boxstyle": "round,pad=0.15",
                    "facecolor": "#f7f8fa",
                    "edgecolor": "none",
                    "alpha": 0.82,
                },
            )


def _draw_major_lines(axis, state: GameState) -> None:
    for line in state.major_lines.values():
        source = state.cities.get(line.source)
        target = state.cities.get(line.target)
        if source is None or target is None:
            continue
        color = "#2e8b57" if line.claimed else "#7b61a8"
        axis.plot(
            [source.x, target.x],
            [source.y, target.y],
            color=color,
            linewidth=1.5 if line.claimed else 1.0,
            linestyle=":",
            alpha=0.75,
            zorder=1,
        )
        axis.text(
            (source.x + target.x) / 2,
            (source.y + target.y) / 2 + 0.012,
            f"ML {line.id} +{line.bonus_points}",
            fontsize=5.5,
            color=color,
            ha="center",
            va="bottom",
            zorder=1,
        )


def _draw_rail_baron(axis, state: GameState) -> None:
    objective = get_active_rail_baron_objective(state)
    if objective is None:
        return
    source = state.cities.get(objective.source)
    target = state.cities.get(objective.target)
    if source is None or target is None:
        return
    color = "#16825d" if objective.claimed else "#c2185b"
    axis.plot(
        [source.x, target.x],
        [source.y, target.y],
        color=color,
        linewidth=2.2,
        linestyle="-.",
        alpha=0.9,
        zorder=3,
    )
    axis.scatter(
        [source.x, target.x],
        [source.y, target.y],
        s=650,
        facecolors="none",
        edgecolors=color,
        linewidths=2.2,
        zorder=5,
    )


def _draw_cities(axis, state: GameState, *, show_goods: bool) -> None:
    for city in state.cities.values():
        face_color = (
            DEMAND_COLORS.get(city.demand_color, "#7f8c8d")
            if not city.is_gray or city.is_urbanized
            else "#b8bdc3"
        )
        axis.scatter(
            [city.x],
            [city.y],
            s=330 if city.is_gray else 270,
            marker="s" if city.is_gray else "o",
            c=[face_color],
            edgecolors="#202124",
            linewidths=1.5,
            zorder=4,
        )
        axis.text(
            city.x,
            city.y + 0.022,
            f"{city.id}  {city.name}",
            fontsize=7,
            fontweight="bold",
            color="#202124",
            ha="center",
            va="bottom",
            zorder=6,
        )
        demand = city.demand_color or "none"
        status = "gray" if city.is_gray and not city.is_urbanized else f"D:{demand}"
        if city.is_gray and city.is_urbanized:
            status = f"urbanized D:{demand}"
        if show_goods:
            goods = ",".join(city.goods) if city.goods else "none"
            status = f"{status} | G:{goods}"
        if city.empty_marker:
            status += " | EMPTY"
        axis.text(
            city.x,
            city.y - 0.022,
            status,
            fontsize=5.7,
            color="#3c4043",
            ha="center",
            va="top",
            zorder=6,
            bbox={
                "boxstyle": "round,pad=0.12",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.72,
            },
        )


def _draw_summary(axis, state: GameState, *, show_rail_baron: bool) -> None:
    summary = (
        f"Turn {state.turn} | phase {state.phase} | actions {state.actions_remaining}\n"
        f"money ${state.player.money} | bonds {state.player.bonds} | "
        f"score {state.player.score} | engine {state.player.locomotive_level}\n"
        f"deliveries {state.player.delivered_goods_count} | "
        f"major bonus {state.player.major_line_bonus} | "
        f"Rail Baron bonus {state.player.rail_baron_bonus}"
    )
    axis.text(
        0.01,
        0.99,
        summary,
        transform=axis.transAxes,
        fontsize=8,
        ha="left",
        va="top",
        zorder=10,
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": "white",
            "edgecolor": "#aeb4ba",
            "alpha": 0.93,
        },
    )

    if not show_rail_baron:
        return
    objective = get_active_rail_baron_objective(state)
    if objective is None:
        objective_text = "Rail Baron: none"
        edge_color = "#aeb4ba"
    else:
        claimed = "CLAIMED" if objective.claimed else "active"
        objective_text = (
            f"Rail Baron: {objective.id} ({claimed})\n"
            f"{objective.source} → {objective.target} | +{objective.bonus_points}"
        )
        edge_color = "#16825d" if objective.claimed else "#c2185b"
    axis.text(
        0.99,
        0.99,
        objective_text,
        transform=axis.transAxes,
        fontsize=8,
        ha="right",
        va="top",
        zorder=10,
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": "white",
            "edgecolor": edge_color,
            "alpha": 0.93,
        },
    )


def _draw_legend(axis, show_major_lines: bool, show_rail_baron: bool) -> None:
    handles = [
        Line2D([0], [0], label="unbuilt", **TRACK_STYLES["unbuilt"]),
        Line2D([0], [0], label="built incomplete", **TRACK_STYLES["incomplete"]),
        Line2D([0], [0], label="completed", **TRACK_STYLES["completed"]),
    ]
    if show_major_lines:
        handles.append(
            Line2D(
                [0],
                [0],
                color="#7b61a8",
                linewidth=1.2,
                linestyle=":",
                label="major line",
            )
        )
    if show_rail_baron:
        handles.append(
            Line2D(
                [0],
                [0],
                color="#c2185b",
                linewidth=2.0,
                linestyle="-.",
                label="Rail Baron",
            )
        )
    axis.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=len(handles),
        frameon=True,
        framealpha=0.92,
        fontsize=7,
    )


def _set_map_bounds(axis, state: GameState) -> None:
    xs = [city.x for city in state.cities.values()]
    ys = [city.y for city in state.cities.values()]
    if not xs or not ys:
        axis.set_xlim(0, 1)
        axis.set_ylim(0, 1)
        return
    x_padding = max(0.08, (max(xs) - min(xs)) * 0.12)
    y_padding = max(0.08, (max(ys) - min(ys)) * 0.15)
    axis.set_xlim(min(xs) - x_padding, max(xs) + x_padding)
    axis.set_ylim(min(ys) - y_padding, max(ys) + y_padding)


def _interpolated_route_points(
    state: GameState,
    source_id: str,
    target_id: str,
    segment_count: int,
) -> list[tuple[float, float]]:
    source = state.cities[source_id]
    target = state.cities[target_id]
    return [
        (
            source.x + (target.x - source.x) * index / segment_count,
            source.y + (target.y - source.y) * index / segment_count,
        )
        for index in range(segment_count + 1)
    ]


def _segment_status(segment) -> str:
    if segment.built and segment.completed:
        return "completed"
    if segment.built:
        return "incomplete"
    return "unbuilt"


def _route_status(route, segments) -> str:
    if route.completed:
        return "completed"
    if any(segment.built for segment in segments):
        return "incomplete"
    return "unbuilt"
