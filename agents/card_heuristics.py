from __future__ import annotations

import networkx as nx

from railways.actions import Action
from railways.game_state import GameState
from railways.rules import (
    get_built_graph,
    get_legal_build_actions,
    get_legal_deliveries,
    get_legal_operation_card_actions,
    get_legal_upgrade_action,
    get_legal_urbanize_actions,
)


MAX_ACTIVE_CARDS = 3
MIN_CARD_SCORE = 5.0
MIN_HIGH_VALUE_DELIVERY_SCORE = 2


def choose_card_aware_rollout_action(
    state: GameState,
    legal_actions: list[Action] | None = None,
) -> Action | None:
    """Choose a deterministic card-aware rollout action without mutating state."""
    actions = list(legal_actions or [])
    if not actions:
        return None

    completing_actions = card_completion_candidates(state, actions)
    if completing_actions:
        return completing_actions[0]

    deliveries = ranked_delivery_actions(
        [action for action in actions if action.action_type == "deliver_good"]
    )
    if deliveries and int(deliveries[0].params.get("score", 0)) >= MIN_HIGH_VALUE_DELIVERY_SCORE:
        return deliveries[0]

    card_candidates = card_action_candidates(state, actions)
    if card_candidates:
        return card_candidates[0][1]

    build_candidates = ranked_card_related_build_actions(state, actions)
    if build_candidates:
        return build_candidates[0]

    if deliveries:
        return deliveries[0]

    upgrade_action = _first_action(actions, "upgrade_engine")
    if upgrade_action is not None:
        return upgrade_action

    urbanize_actions = sorted(
        (action for action in actions if action.action_type == "urbanize"),
        key=lambda action: str(action.params.get("city_id", "")),
    )
    if urbanize_actions:
        return urbanize_actions[0]

    pass_action = _first_action(actions, "pass")
    if pass_action is not None:
        return pass_action
    return actions[0]


def ranked_delivery_actions(deliveries: list[Action] | None = None) -> list[Action]:
    return sorted(
        deliveries or [],
        key=lambda action: (
            -int(action.params.get("score", 0)),
            int(action.params.get("path_length", 0)),
            str(action.params.get("source", "")),
            str(action.params.get("target", "")),
            str(action.params.get("good_color", "")),
            "-".join(action.params.get("path", [])),
        ),
    )


def card_completion_candidates(
    state: GameState,
    legal_actions: list[Action] | None = None,
) -> list[Action]:
    actions = list(legal_actions) if legal_actions is not None else _core_actions(state)
    candidates = [
        action for action in actions if action_completes_active_card(state, action)
    ]
    return sorted(
        candidates,
        key=lambda action: (
            _action_group_rank(action),
            -_action_score_hint(state, action),
            _action_key(action),
        ),
    )


def action_completes_active_card(state: GameState, action: Action) -> bool:
    if action.action_type == "deliver_good":
        return _delivery_completes_objective(state, action)
    if action.action_type == "build_track":
        return _build_completes_network_objective(state, action)
    return False


def card_action_candidates(
    state: GameState,
    legal_actions: list[Action] | None = None,
) -> list[tuple[float, Action]]:
    if active_card_count(state) >= MAX_ACTIVE_CARDS:
        return []

    actions = (
        [action for action in legal_actions if action.action_type == "select_operation_card"]
        if legal_actions is not None
        else get_legal_operation_card_actions(state)
    )
    candidates = [
        (score_card_selection(state, action), action)
        for action in actions
    ]
    candidates = [
        (score, action)
        for score, action in candidates
        if score >= MIN_CARD_SCORE
    ]
    return sorted(
        candidates,
        key=lambda item: (-item[0], str(item[1].params.get("card_id", ""))),
    )


def score_card_selection(state: GameState, action: Action) -> float:
    card_id = str(action.params.get("card_id", ""))
    if (
        action.action_type != "select_operation_card"
        or card_id not in state.operation_cards
        or card_id not in state.available_operation_cards
        or card_id in state.player.owned_operation_cards
    ):
        return float("-inf")

    card = state.operation_cards[card_id]
    if card.card_type == "immediate_cash":
        score = float(card.effect.get("cash", 0))
        if state.player.money < 5:
            score += 3.0
        return score

    if card.card_type == "delivery_objective":
        good_color = card.condition.get("good_color")
        reward = float(card.reward.get("points", 0))
        score = reward
        if _matching_delivery_exists(state, str(good_color)):
            score += 10.0
        elif _matching_source_and_target_exist(state, str(good_color)):
            score += 5.0
        required_count = int(card.condition.get("required_count", 1))
        if required_count > 1:
            score -= float(required_count - 1)
        return score

    if card.card_type == "network_objective":
        source = str(card.condition.get("source", ""))
        target = str(card.condition.get("target", ""))
        if source not in state.cities or target not in state.cities:
            return float("-inf")
        reward = float(card.reward.get("points", 0))
        score = reward
        if _has_built_path(state, source, target):
            return score + 10.0
        network_cities = _player_network_cities(state)
        if source in network_cities or target in network_cities:
            score += 5.0
        distance = _shortest_available_path_length(state, source, target)
        if distance is None:
            return float("-inf")
        score -= 0.75 * distance
        return score

    if card.card_type == "end_game_scoring":
        if card.condition.get("metric") != "built_edges":
            return 0.0
        points_per_item = float(card.reward.get("points_per_item", 0))
        max_points = float(card.reward.get("max_points", 0))
        current_value = len(state.player.built_edges) * points_per_item
        if max_points > 0:
            current_value = min(current_value, max_points)
        future_value = min(max_points or current_value + 2.0, current_value + 2.0)
        return future_value

    return 0.0


def ranked_card_related_build_actions(
    state: GameState,
    legal_actions: list[Action] | None = None,
) -> list[Action]:
    actions = (
        [action for action in legal_actions if action.action_type == "build_track"]
        if legal_actions is not None
        else get_legal_build_actions(state)
    )
    candidates = [
        (score_card_related_build(state, action), str(action.params.get("edge_id", "")), action)
        for action in actions
    ]
    candidates = [item for item in candidates if item[0] > 0]
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in candidates]


def score_card_related_build(state: GameState, action: Action) -> float:
    if action.action_type != "build_track":
        return 0.0
    edge_id = str(action.params.get("edge_id", ""))
    edge = state.edges.get(edge_id)
    if edge is None:
        return 0.0

    score = -0.15 * edge.cost

    if _build_completes_network_objective(state, action):
        score += 20.0

    active_delivery_colors = _active_delivery_objective_colors(state)
    for color in active_delivery_colors:
        if color in state.cities[edge.source].goods:
            score += 2.0
        if color in state.cities[edge.target].goods:
            score += 2.0
        if state.cities[edge.source].demand_color == color:
            score += 2.0
        if state.cities[edge.target].demand_color == color:
            score += 2.0

    score += _major_line_endpoint_score(state, edge.source, edge.target)
    score += _network_objective_endpoint_score(state, edge.source, edge.target)

    delivery_score = _best_delivery_score_after_build(state, action)
    score += 2.0 * delivery_score
    return score


def best_card_aware_action(state: GameState) -> Action:
    legal_actions = _all_relevant_legal_actions(state)
    action = choose_card_aware_rollout_action(state, legal_actions)
    if action is not None:
        return action
    return Action.pass_action()


def active_card_count(state: GameState) -> int:
    return sum(
        1
        for card_state in state.player.active_operation_cards.values()
        if card_state.status == "active"
    )


def _core_actions(state: GameState) -> list[Action]:
    return get_legal_deliveries(state) + get_legal_build_actions(state)


def _all_relevant_legal_actions(state: GameState) -> list[Action]:
    actions: list[Action] = []
    actions.extend(get_legal_deliveries(state))
    actions.extend(get_legal_build_actions(state))
    actions.extend(get_legal_operation_card_actions(state))
    upgrade = get_legal_upgrade_action(state)
    if upgrade is not None:
        actions.append(upgrade)
    actions.extend(get_legal_urbanize_actions(state))
    actions.append(Action.pass_action())
    actions.append(Action.next_turn())
    return actions


def _delivery_completes_objective(state: GameState, action: Action) -> bool:
    good_color = str(action.params.get("good_color", ""))
    source = str(action.params.get("source", ""))
    target = str(action.params.get("target", ""))
    for card_id, card_state in state.player.active_operation_cards.items():
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
        required = int(condition.get("required_count", 1))
        if card_state.progress + 1 >= required:
            return True
    return False


def _build_completes_network_objective(state: GameState, action: Action) -> bool:
    edge_id = str(action.params.get("edge_id", ""))
    edge = state.edges.get(edge_id)
    if edge is None:
        return False

    graph = get_built_graph(state)
    graph.add_node(edge.source)
    graph.add_node(edge.target)
    graph.add_edge(edge.source, edge.target)
    for card_id, card_state in state.player.active_operation_cards.items():
        if card_state.status != "active":
            continue
        card = state.operation_cards.get(card_id)
        if card is None or card.card_type != "network_objective":
            continue
        source = str(card.condition.get("source", ""))
        target = str(card.condition.get("target", ""))
        if not source or not target:
            continue
        try:
            if nx.has_path(graph, source, target):
                return True
        except (nx.NetworkXError, nx.NodeNotFound):
            continue
    return False


def _matching_delivery_exists(state: GameState, good_color: str) -> bool:
    return any(
        action.params.get("good_color") == good_color
        for action in get_legal_deliveries(state)
    )


def _matching_source_and_target_exist(state: GameState, good_color: str) -> bool:
    if not good_color:
        return False
    has_source = any(good_color in city.goods for city in state.cities.values())
    has_target = any(city.demand_color == good_color for city in state.cities.values())
    return has_source and has_target


def _has_built_path(state: GameState, source: str, target: str) -> bool:
    try:
        return nx.has_path(get_built_graph(state), source, target)
    except (nx.NetworkXError, nx.NodeNotFound):
        return False


def _shortest_available_path_length(
    state: GameState,
    source: str,
    target: str,
) -> int | None:
    graph = nx.Graph()
    for city_id in state.cities:
        graph.add_node(city_id)
    for edge in state.edges.values():
        graph.add_edge(edge.source, edge.target)
    try:
        path = nx.shortest_path(graph, source, target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None
    return max(0, len(path) - 1)


def _player_network_cities(state: GameState) -> set[str]:
    cities: set[str] = set()
    for edge in state.edges.values():
        if edge.built and edge.owner == "player":
            cities.add(edge.source)
            cities.add(edge.target)
    return cities


def _active_delivery_objective_colors(state: GameState) -> set[str]:
    colors: set[str] = set()
    for card_id, card_state in state.player.active_operation_cards.items():
        if card_state.status != "active":
            continue
        card = state.operation_cards.get(card_id)
        if card is None or card.card_type != "delivery_objective":
            continue
        color = card.condition.get("good_color")
        if color:
            colors.add(str(color))
    return colors


def _major_line_endpoint_score(
    state: GameState,
    source: str,
    target: str,
) -> float:
    score = 0.0
    network_cities = _player_network_cities(state)
    for major_line in state.major_lines.values():
        if major_line.claimed:
            continue
        endpoints = {major_line.source, major_line.target}
        edge_cities = {source, target}
        if endpoints & edge_cities:
            score += 2.0
        if network_cities & endpoints and edge_cities & endpoints:
            score += 2.0
    return score


def _network_objective_endpoint_score(
    state: GameState,
    source: str,
    target: str,
) -> float:
    score = 0.0
    edge_cities = {source, target}
    network_cities = _player_network_cities(state)
    for card_id, card_state in state.player.active_operation_cards.items():
        if card_state.status != "active":
            continue
        card = state.operation_cards.get(card_id)
        if card is None or card.card_type != "network_objective":
            continue
        endpoints = {
            str(card.condition.get("source", "")),
            str(card.condition.get("target", "")),
        }
        if endpoints & edge_cities:
            score += 4.0
        if network_cities & endpoints and edge_cities & endpoints:
            score += 3.0
    return score


def _best_delivery_score_after_build(state: GameState, action: Action) -> int:
    edge_id = str(action.params.get("edge_id", ""))
    edge = state.edges.get(edge_id)
    if edge is None:
        return 0

    graph = get_built_graph(state)
    graph.add_edge(edge.source, edge.target)
    best_score = 0
    for source_city in state.cities.values():
        for good_color in sorted(set(source_city.goods)):
            for target_city in state.cities.values():
                if source_city.id == target_city.id:
                    continue
                if target_city.demand_color != good_color:
                    continue
                try:
                    path = nx.shortest_path(
                        graph,
                        source_city.id,
                        target_city.id,
                    )
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue
                path_length = max(0, len(path) - 1)
                if path_length <= state.player.locomotive_level:
                    best_score = max(best_score, path_length)
    return best_score


def _action_group_rank(action: Action) -> int:
    if action.action_type == "deliver_good":
        return 0
    if action.action_type == "build_track":
        return 1
    return 2


def _action_score_hint(state: GameState, action: Action) -> float:
    if action.action_type == "deliver_good":
        return float(action.params.get("score", 0))
    if action.action_type == "build_track":
        return score_card_related_build(state, action)
    if action.action_type == "select_operation_card":
        return score_card_selection(state, action)
    return 0.0


def _action_key(action: Action) -> str:
    return (
        f"{action.action_type}:"
        f"{action.params.get('edge_id', '')}:"
        f"{action.params.get('card_id', '')}:"
        f"{action.params.get('source', '')}:"
        f"{action.params.get('target', '')}:"
        f"{action.params.get('good_color', '')}"
    )


def _first_action(actions: list[Action], action_type: str) -> Action | None:
    for action in actions:
        if action.action_type == action_type:
            return action
    return None
