from __future__ import annotations

from typing import Any

import networkx as nx

from railways.game_state import GameState
from railways.models import RailwayEdge
from railways.scoring import compute_delivery_score

Action = dict[str, Any]


def build_track(state: GameState, edge_id: str) -> bool:
    if state.is_terminal():
        return False

    edge = state.get_edge(edge_id)
    if edge is None or edge.built:
        return False

    if state.player.money < edge.cost:
        return False

    state.player.money -= edge.cost
    edge.built = True
    state.player.built_edges.add(edge.id)
    _record(state, f"Turn {state.player.turn}: built {edge.id} for ${edge.cost}.")
    return True


def issue_bond(state: GameState) -> None:
    if state.is_terminal():
        return

    state.player.money += state.config.bond_value
    state.player.bonds += 1
    _record(
        state,
        f"Turn {state.player.turn}: issued bond (+${state.config.bond_value}).",
    )


def upgrade_locomotive(state: GameState) -> bool:
    if state.is_terminal():
        return False

    if state.player.locomotive_level >= state.config.max_locomotive_level:
        return False

    upgrade_cost = state.player.locomotive_level * state.config.upgrade_cost_multiplier
    if state.player.money < upgrade_cost:
        return False

    state.player.money -= upgrade_cost
    state.player.locomotive_level += 1
    _record(
        state,
        (
            f"Turn {state.player.turn}: upgraded locomotive to "
            f"level {state.player.locomotive_level} for ${upgrade_cost}."
        ),
    )
    return True


def deliver_good(
    state: GameState,
    source_city_id: str,
    target_city_id: str,
    good_color: str,
) -> bool:
    if state.is_terminal() or source_city_id == target_city_id:
        return False

    source_city = state.get_city(source_city_id)
    target_city = state.get_city(target_city_id)
    if source_city is None or target_city is None:
        return False

    if good_color not in source_city.goods:
        return False

    if target_city.demand_color != good_color:
        return False

    path = find_shortest_built_path(state, source_city_id, target_city_id)
    if path is None:
        return False

    path_length = len(path) - 1
    if path_length <= 0 or path_length > state.player.locomotive_level:
        return False

    delivery_score = compute_delivery_score(path_length, state.config)
    source_city.goods.remove(good_color)
    state.player.score += delivery_score
    state.player.delivered_goods_count += 1
    _record(
        state,
        (
            f"Turn {state.player.turn}: delivered {good_color} from "
            f"{source_city_id} to {target_city_id} via {'-'.join(path)} "
            f"(+{delivery_score} score)."
        ),
    )
    return True


def next_turn(state: GameState) -> None:
    if state.player.turn <= state.player.max_turns:
        state.player.turn += 1
        _record(state, f"Advanced to turn {state.player.turn}.")


def get_built_graph(state: GameState) -> nx.Graph:
    graph = nx.Graph()
    for city_id, city in state.cities.items():
        graph.add_node(city_id, city=city)

    for edge in state.edges.values():
        if edge.built:
            graph.add_edge(edge.source, edge.target, edge_id=edge.id, cost=edge.cost)

    return graph


def find_shortest_built_path(
    state: GameState,
    source_city_id: str,
    target_city_id: str,
) -> list[str] | None:
    graph = get_built_graph(state)
    try:
        return nx.shortest_path(graph, source=source_city_id, target=target_city_id)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def get_legal_build_actions(state: GameState) -> list[RailwayEdge]:
    if state.is_terminal():
        return []

    return [
        edge
        for edge in state.edges.values()
        if not edge.built and state.player.money >= edge.cost
    ]


def get_legal_deliveries(state: GameState) -> list[Action]:
    if state.is_terminal():
        return []

    deliveries: list[Action] = []
    for source_city in state.cities.values():
        for good_color in source_city.goods:
            for target_city in state.cities.values():
                if source_city.id == target_city.id:
                    continue
                if target_city.demand_color != good_color:
                    continue

                path = find_shortest_built_path(state, source_city.id, target_city.id)
                if path is None:
                    continue

                path_length = len(path) - 1
                if 0 < path_length <= state.player.locomotive_level:
                    deliveries.append(
                        {
                            "type": "deliver",
                            "source": source_city.id,
                            "target": target_city.id,
                            "good_color": good_color,
                            "path": path,
                            "path_length": path_length,
                            "score": compute_delivery_score(path_length, state.config),
                        }
                    )

    return deliveries


def apply_action(state: GameState, action: Action) -> bool:
    action_type = action.get("type")

    if action_type == "build":
        return build_track(state, str(action["edge_id"]))

    if action_type == "deliver":
        return deliver_good(
            state,
            str(action["source"]),
            str(action["target"]),
            str(action["good_color"]),
        )

    if action_type == "issue_bond":
        issue_bond(state)
        return True

    if action_type == "upgrade_locomotive":
        return upgrade_locomotive(state)

    if action_type == "next_turn":
        next_turn(state)
        return True

    return False


def describe_action(action: Action | None) -> str:
    if action is None:
        return "No action."

    action_type = action.get("type")
    if action_type == "build":
        return f"Build track {action['edge_id']}"
    if action_type == "deliver":
        return (
            f"Deliver {action['good_color']} from "
            f"{action['source']} to {action['target']}"
        )
    if action_type == "issue_bond":
        return "Issue bond"
    if action_type == "upgrade_locomotive":
        return "Upgrade locomotive"
    if action_type == "next_turn":
        return "Next turn"
    return str(action)


def _record(state: GameState, message: str) -> None:
    state.player.action_history.append(message)
