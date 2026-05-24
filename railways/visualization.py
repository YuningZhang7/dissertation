from __future__ import annotations

import plotly.graph_objects as go

from railways.game_state import GameState

DEMAND_COLORS = {
    "red": "#d62728",
    "blue": "#1f77b4",
    "yellow": "#f2c94c",
    "green": "#2ca02c",
}


def draw_map(state: GameState) -> go.Figure:
    fig = go.Figure()

    for edge in state.edges.values():
        source = state.cities[edge.source]
        target = state.cities[edge.target]
        line_color = "#1f77b4" if edge.built else "#c7c7c7"
        line_width = 5 if edge.built else 2
        line_dash = "solid" if edge.built else "dash"
        status = "built" if edge.built else "available"

        fig.add_trace(
            go.Scatter(
                x=[source.x, target.x],
                y=[source.y, target.y],
                mode="lines",
                line=dict(color=line_color, width=line_width, dash=line_dash),
                hoverinfo="text",
                text=f"{edge.id}<br>Cost: {edge.cost}<br>Status: {status}",
                showlegend=False,
            )
        )

        fig.add_annotation(
            x=(source.x + target.x) / 2,
            y=(source.y + target.y) / 2,
            text=str(edge.cost),
            showarrow=False,
            font=dict(size=11, color="#4a4a4a"),
            bgcolor="rgba(255,255,255,0.75)",
            borderpad=2,
        )

    city_ids = list(state.cities.keys())
    cities = [state.cities[city_id] for city_id in city_ids]
    hover_text = [
        (
            f"{city.name} ({city.id})<br>"
            f"Demand: {city.demand_color}<br>"
            f"Goods: {', '.join(city.goods) if city.goods else 'none'}"
        )
        for city in cities
    ]
    node_text = [
        f"{city.id}<br>{'/'.join(city.goods) if city.goods else '-'}" for city in cities
    ]

    fig.add_trace(
        go.Scatter(
            x=[city.x for city in cities],
            y=[city.y for city in cities],
            mode="markers+text",
            text=node_text,
            textposition="top center",
            hovertext=hover_text,
            hoverinfo="text",
            marker=dict(
                size=34,
                color=[
                    DEMAND_COLORS.get(city.demand_color, "#888888") for city in cities
                ],
                line=dict(color="#242424", width=2),
            ),
            showlegend=False,
        )
    )

    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        height=620,
        plot_bgcolor="#fbfbfb",
        paper_bgcolor="#fbfbfb",
        xaxis=dict(visible=False, range=[0.0, 0.82]),
        yaxis=dict(visible=False, range=[0.08, 0.92]),
        hovermode="closest",
    )

    return fig
