from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx

from railways.actions import Action
from railways.models import PHASE_ACTION, PlayerCardState

if TYPE_CHECKING:
    from railways.game_state import GameState


def get_legal_operation_card_actions(state: GameState) -> list[Action]:
    if state.phase != PHASE_ACTION:
        return []
    return [
        Action.select_operation_card(card_id)
        for card_id in state.available_operation_cards
        if card_id in state.operation_cards
    ]


def apply_card_on_select(state: GameState, card_id: str) -> tuple[bool, str]:
    if card_id not in state.operation_cards:
        return False, f"Operation card {card_id} does not exist."
    if card_id not in state.available_operation_cards:
        return False, f"Operation card {card_id} is not available."
    if card_id in state.player.owned_operation_cards:
        return False, f"Operation card {card_id} is already owned."

    card = state.operation_cards[card_id]
    supported_types = {
        "immediate_cash",
        "delivery_objective",
        "network_objective",
        "end_game_scoring",
    }
    if card.card_type not in supported_types:
        return False, f"Unsupported operation card type: {card.card_type}."

    state.available_operation_cards.remove(card_id)
    state.player.owned_operation_cards.append(card_id)

    if card.card_type == "immediate_cash":
        cash = int(card.effect.get("cash", 0))
        state.player.money += cash
        state.player.active_operation_cards[card_id] = PlayerCardState(
            card_id=card_id,
            status="used",
        )
        state.player.completed_operation_cards.add(card_id)
        state.record(
            f"Turn {state.turn}: selected card {card.name}; gained ${cash}."
        )
        return True, f"Selected {card.name} and gained ${cash}."

    if card.card_type in {
        "delivery_objective",
        "network_objective",
        "end_game_scoring",
    }:
        state.player.active_operation_cards[card_id] = PlayerCardState(
            card_id=card_id,
            status="active",
        )
        state.record(f"Turn {state.turn}: selected card {card.name}.")
        if card.card_type == "network_objective":
            update_cards_after_build(state)
        return True, f"Selected {card.name}."


def update_cards_after_delivery(
    state: GameState,
    source: str,
    target: str,
    good_color: str,
) -> None:
    for card_id, card_state in list(state.player.active_operation_cards.items()):
        if card_state.status != "active":
            continue
        card = state.operation_cards.get(card_id)
        if card is None or card.card_type != "delivery_objective":
            continue
        condition = card.condition
        if condition.get("good_color") not in (None, good_color):
            continue
        if condition.get("source") not in (None, source):
            continue
        if condition.get("target") not in (None, target):
            continue

        card_state.progress += 1
        required_count = int(condition.get("required_count", 1))
        if card_state.progress >= required_count:
            _award_card_points(state, card_id)


def update_cards_after_build(state: GameState) -> None:
    for card_id, card_state in list(state.player.active_operation_cards.items()):
        if card_state.status != "active":
            continue
        card = state.operation_cards.get(card_id)
        if card is None or card.card_type != "network_objective":
            continue
        source = card.condition.get("source")
        target = card.condition.get("target")
        if not source or not target:
            continue
        if _has_built_path(state, str(source), str(target)):
            _award_card_points(state, card_id)


def compute_end_game_card_bonus(state: GameState) -> int:
    bonus = 0
    for card_id in state.player.owned_operation_cards:
        card = state.operation_cards.get(card_id)
        if card is None or card.card_type != "end_game_scoring":
            continue
        if card.condition.get("metric") == "built_edges":
            points_per_item = int(card.reward.get("points_per_item", 0))
            max_points = int(card.reward.get("max_points", 0))
            earned = len(state.player.built_edges) * points_per_item
            if max_points > 0:
                earned = min(earned, max_points)
            bonus += earned
    return bonus


def _award_card_points(state: GameState, card_id: str) -> None:
    card = state.operation_cards[card_id]
    card_state = state.player.active_operation_cards[card_id]
    if card_state.status == "completed":
        return

    points = int(card.reward.get("points", 0))
    card_state.status = "completed"
    card_state.awarded_points = points
    state.player.completed_operation_cards.add(card_id)
    state.player.operation_card_bonus += points
    state.record(
        f"Turn {state.turn}: completed card {card.name} (+{points})."
    )


def _has_built_path(state: GameState, source: str, target: str) -> bool:
    graph = nx.Graph()
    for city_id in state.cities:
        graph.add_node(city_id)
    for edge in state.edges.values():
        if edge.built:
            graph.add_edge(edge.source, edge.target)
    try:
        return nx.has_path(graph, source, target)
    except (nx.NetworkXError, nx.NodeNotFound):
        return False
