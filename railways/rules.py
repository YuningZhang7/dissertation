from __future__ import annotations

import math
import random

import networkx as nx

from railways.actions import Action
from railways.cards import (
    apply_card_on_select,
    get_legal_operation_card_actions,
    update_cards_after_build,
    update_cards_after_delivery,
)
from railways.game_state import GameState
from railways.models import PHASE_ACTION, PHASE_GAME_OVER, PHASE_INCOME
from railways.scoring import compute_delivery_score, compute_income


PLAYER_ID = "player"


def start_turn(state: GameState) -> None:
    if state.phase == PHASE_GAME_OVER:
        return
    state.phase = PHASE_ACTION
    state.actions_remaining = state.config.actions_per_turn
    state.record(f"Turn {state.turn}: action phase started.")


def consume_action(state: GameState) -> None:
    if state.phase != PHASE_ACTION:
        return
    state.actions_remaining = max(0, state.actions_remaining - 1)
    if state.actions_remaining == 0:
        run_income_phase(state)


def run_income_phase(state: GameState) -> None:
    if state.phase == PHASE_GAME_OVER:
        return

    state.phase = PHASE_INCOME
    income = compute_income(state)
    interest_due = state.player.bonds * state.config.bond_interest
    state.player.money += income

    if interest_due:
        paid, payment_message = pay_money(
            state,
            interest_due,
            allow_auto_bonds=state.config.auto_issue_bonds_when_needed,
        )
        if not paid:
            state.player.money -= interest_due
            payment_message = (
                f"Bond interest ${interest_due} exceeded cash; "
                f"cash balance is now ${state.player.money}."
            )
    else:
        payment_message = "No bond interest due."

    state.record(
        (
            f"Turn {state.turn}: income phase, income +${income}, "
            f"interest -${interest_due}. {payment_message}"
        )
    )
    check_end_condition(state)
    advance_turn(state)


def advance_turn(state: GameState) -> None:
    if state.phase == PHASE_GAME_OVER:
        return

    if state.end_triggered:
        if state.extra_turns_remaining <= 0:
            state.phase = PHASE_GAME_OVER
            state.actions_remaining = 0
            state.record(f"Game over after turn {state.turn}.")
            return
        state.extra_turns_remaining -= 1

    state.turn += 1
    start_turn(state)


def next_turn(state: GameState) -> tuple[bool, str]:
    if state.phase == PHASE_GAME_OVER:
        return False, "Game is already over."
    if state.phase == PHASE_ACTION:
        state.record(f"Turn {state.turn}: ended turn early.")
        state.actions_remaining = 0
        run_income_phase(state)
        return True, "Ended the current turn and ran income."
    if state.phase == PHASE_INCOME:
        advance_turn(state)
        return True, "Advanced from income phase."
    return False, f"Cannot advance from phase {state.phase}."


def build_track(state: GameState, edge_id: str) -> tuple[bool, str]:
    ok, message = _ensure_action_phase(state)
    if not ok:
        return False, message

    edge = state.get_edge(edge_id)
    if edge is None:
        return False, f"Edge {edge_id} does not exist."
    if edge.built:
        return False, f"Edge {edge_id} is already built."
    if not is_build_connected_to_player_network(state, edge_id):
        return (
            False,
            (
                f"Edge {edge_id} is not connected to the player's existing "
                "rail network."
            ),
        )

    paid, payment_message = pay_money(
        state,
        edge.cost,
        allow_auto_bonds=state.config.auto_issue_bonds_when_needed,
    )
    if not paid:
        return False, f"Cannot build {edge_id}: {payment_message}"

    edge.built = True
    edge.owner = PLAYER_ID
    state.player.built_edges.add(edge.id)
    state.record(
        f"Turn {state.turn}: built {edge.id} for ${edge.cost}. {payment_message}"
    )
    check_major_lines(state)
    update_cards_after_build(state)
    consume_action(state)
    return True, f"Built track {edge_id}."


def get_legal_build_actions(state: GameState) -> list[Action]:
    if state.phase != PHASE_ACTION:
        return []

    actions: list[Action] = []
    for edge in state.edges.values():
        if edge.built:
            continue
        if not is_build_connected_to_player_network(state, edge.id):
            continue
        if can_pay(state, edge.cost) or state.config.auto_issue_bonds_when_needed:
            actions.append(Action.build_track(edge.id))
    return actions


def get_player_network_city_ids(state: GameState) -> set[str]:
    city_ids: set[str] = set()
    for edge in state.edges.values():
        if edge.built and edge.owner == PLAYER_ID:
            city_ids.add(edge.source)
            city_ids.add(edge.target)
    return city_ids


def is_build_connected_to_player_network(
    state: GameState,
    edge_id: str,
) -> bool:
    if not state.config.require_connected_track_building:
        return True

    edge = state.get_edge(edge_id)
    if edge is None:
        return False

    network_cities = get_player_network_city_ids(state)
    if not network_cities:
        return True

    return edge.source in network_cities or edge.target in network_cities


def deliver_good(
    state: GameState,
    source_city_id: str,
    target_city_id: str,
    good_color: str,
    path: list[str] | None = None,
) -> tuple[bool, str]:
    ok, message = _ensure_action_phase(state)
    if not ok:
        return False, message

    if source_city_id == target_city_id:
        return False, "Source and target cities must be different."

    source_city = state.get_city(source_city_id)
    target_city = state.get_city(target_city_id)
    if source_city is None or target_city is None:
        return False, "Source or target city does not exist."
    if target_city.is_gray:
        return False, "Goods cannot be delivered to a gray city."
    if good_color not in source_city.goods:
        return False, f"{source_city.name} does not contain a {good_color} good."
    if target_city.demand_color != good_color:
        return False, f"{target_city.name} does not demand {good_color}."

    selected_path = path or find_shortest_built_path(state, source_city_id, target_city_id)
    if selected_path is None:
        return False, "No built route connects the source and target."

    valid_path, path_message = validate_delivery_path(
        state,
        selected_path,
        source_city_id,
        target_city_id,
        good_color,
    )
    if not valid_path:
        return False, path_message

    length = path_length(selected_path)
    delivery_score = compute_delivery_score(length, state.config)
    source_city.goods.remove(good_color)
    update_empty_city_marker(state, source_city_id)
    check_end_condition(state)
    state.player.score += delivery_score
    state.player.delivered_goods_count += 1
    state.record(
        (
            f"Turn {state.turn}: delivered {good_color} from {source_city_id} "
            f"to {target_city_id} via {'-'.join(selected_path)} (+{delivery_score})."
        )
    )
    update_cards_after_delivery(
        state,
        source_city_id,
        target_city_id,
        good_color,
    )
    consume_action(state)
    return True, f"Delivered {good_color} from {source_city_id} to {target_city_id}."


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
    source: str,
    target: str,
) -> list[str] | None:
    graph = get_built_graph(state)
    try:
        return nx.shortest_path(graph, source=source, target=target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def find_all_legal_delivery_paths(
    state: GameState,
    source: str,
    target: str,
    good_color: str,
) -> list[list[str]]:
    if source == target:
        return []

    graph = get_built_graph(state)
    if source not in graph or target not in graph:
        return []

    paths: list[list[str]] = []
    cutoff = state.player.locomotive_level
    try:
        candidate_paths = nx.all_simple_paths(
            graph,
            source=source,
            target=target,
            cutoff=cutoff,
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []

    for candidate_path in candidate_paths:
        valid, _ = validate_delivery_path(
            state,
            list(candidate_path),
            source,
            target,
            good_color,
        )
        if valid:
            paths.append(list(candidate_path))

    paths.sort(key=lambda route: (path_length(route), route))
    return paths


def path_length(path: list[str]) -> int:
    return max(0, len(path) - 1)


def path_skips_matching_city(
    state: GameState,
    path: list[str],
    good_color: str,
) -> bool:
    for city_id in path[1:-1]:
        city = state.cities[city_id]
        if city.demand_color == good_color:
            return True
    return False


def validate_delivery_path(
    state: GameState,
    path: list[str],
    source: str,
    target: str,
    good_color: str,
) -> tuple[bool, str]:
    if not path:
        return False, "Delivery path is empty."
    if path[0] != source or path[-1] != target:
        return False, "Delivery path must start at source and end at target."

    length = path_length(path)
    if length <= 0:
        return False, "Delivery path must use at least one link."
    if length > state.player.locomotive_level:
        return (
            False,
            (
                f"Route length {length} exceeds locomotive level "
                f"{state.player.locomotive_level}."
            ),
        )

    graph = get_built_graph(state)
    for city_id in path:
        if city_id not in state.cities:
            return False, f"City {city_id} in the delivery path does not exist."
    for first, second in zip(path, path[1:]):
        if not graph.has_edge(first, second):
            return False, f"Path segment {first}-{second} is not built."

    if path_skips_matching_city(state, path, good_color):
        return False, "Delivery path skips an intermediate city demanding that color."

    return True, "Delivery path is valid."


def get_legal_deliveries(state: GameState) -> list[Action]:
    if state.phase != PHASE_ACTION:
        return []

    deliveries: list[Action] = []
    for source_city in state.cities.values():
        for good_color in sorted(set(source_city.goods)):
            for target_city in state.cities.values():
                if source_city.id == target_city.id:
                    continue
                if target_city.is_gray:
                    continue
                if target_city.demand_color != good_color:
                    continue

                for path in find_all_legal_delivery_paths(
                    state,
                    source_city.id,
                    target_city.id,
                    good_color,
                ):
                    length = path_length(path)
                    deliveries.append(
                        Action(
                            "deliver_good",
                            {
                                "source": source_city.id,
                                "target": target_city.id,
                                "good_color": good_color,
                                "path": path,
                                "path_length": length,
                                "score": compute_delivery_score(length, state.config),
                            },
                        )
                    )
    return deliveries


def upgrade_engine(state: GameState) -> tuple[bool, str]:
    ok, message = _ensure_action_phase(state)
    if not ok:
        return False, message

    next_level = state.player.locomotive_level + 1
    if next_level > state.config.max_locomotive_level:
        return False, "Locomotive is already at maximum level."

    cost = get_engine_upgrade_cost(state, next_level)
    paid, payment_message = pay_money(
        state,
        cost,
        allow_auto_bonds=state.config.auto_issue_bonds_when_needed,
    )
    if not paid:
        return False, f"Cannot upgrade engine: {payment_message}"

    state.player.locomotive_level = next_level
    state.record(
        f"Turn {state.turn}: upgraded engine to level {next_level} for ${cost}."
    )
    consume_action(state)
    return True, f"Upgraded engine to level {next_level}."


def get_engine_upgrade_cost(state: GameState, next_level: int) -> int:
    return int(
        state.config.engine_upgrade_costs.get(
            str(next_level),
            next_level * 5,
        )
    )


def get_legal_upgrade_action(state: GameState) -> Action | None:
    if state.phase != PHASE_ACTION:
        return None
    next_level = state.player.locomotive_level + 1
    if next_level > state.config.max_locomotive_level:
        return None
    cost = get_engine_upgrade_cost(state, next_level)
    if can_pay(state, cost) or state.config.auto_issue_bonds_when_needed:
        return Action("upgrade_engine", {"next_level": next_level, "cost": cost})
    return None


def issue_bond(state: GameState) -> tuple[bool, str]:
    """Voluntarily issue one bond without consuming a player action."""
    ok, message = _ensure_action_phase(state)
    if not ok:
        return False, message
    if not state.config.allow_voluntary_bonds:
        return (
            False,
            "Voluntary bond issue is not a legal player action when disabled.",
        )

    state.player.money += state.config.bond_value
    state.player.bonds += 1
    state.record(
        f"Turn {state.turn}: issued one bond (+${state.config.bond_value})."
    )
    return True, "Issued one bond."


def can_pay(state: GameState, amount: int) -> bool:
    return state.player.money >= amount


def pay_money(
    state: GameState,
    amount: int,
    allow_auto_bonds: bool = False,
) -> tuple[bool, str]:
    if amount <= 0:
        return True, "No payment required."

    issued_certificates = 0
    if state.player.money < amount and allow_auto_bonds:
        shortfall = amount - state.player.money
        bonds_needed = math.ceil(shortfall / state.config.bond_value)
        financing_value = bonds_needed * state.config.bond_value
        state.player.money += financing_value
        state.player.bonds += bonds_needed
        issued_certificates = bonds_needed
        state.record(
            (
                f"Turn {state.turn}: issued {bonds_needed} financing "
                f"certificate(s) automatically to cover payment shortfall "
                f"(+${financing_value})."
            )
        )

    if state.player.money < amount:
        return False, f"Need ${amount}, but only ${state.player.money} is available."

    state.player.money -= amount
    if issued_certificates:
        return (
            True,
            (
                f"Issued {issued_certificates} financing certificate(s) "
                f"automatically. Paid ${amount}."
            ),
        )
    return True, f"Paid ${amount}."


def urbanize(
    state: GameState,
    city_id: str,
    demand_color: str | None = None,
) -> tuple[bool, str]:
    ok, message = _ensure_action_phase(state)
    if not ok:
        return False, message

    city = state.get_city(city_id)
    if city is None:
        return False, f"City {city_id} does not exist."
    if not city.is_gray:
        return False, f"{city.name} is not a gray city."

    chosen_color = demand_color or random.choice(state.config.allowed_good_colors)
    if chosen_color not in state.config.allowed_good_colors:
        return False, f"{chosen_color} is not an allowed goods color."

    paid, payment_message = pay_money(
        state,
        state.config.urbanize_cost,
        allow_auto_bonds=state.config.auto_issue_bonds_when_needed,
    )
    if not paid:
        return False, f"Cannot urbanize {city.name}: {payment_message}"

    city.demand_color = chosen_color
    city.is_gray = False
    city.is_urbanized = True
    city.empty_marker = False
    for _ in range(state.config.new_goods_on_urbanize):
        city.goods.append(random.choice(state.config.allowed_good_colors))

    state.record(
        (
            f"Turn {state.turn}: urbanized {city.name} with {chosen_color} demand "
            f"for ${state.config.urbanize_cost}. {payment_message}"
        )
    )
    consume_action(state)
    return True, f"Urbanized {city.name}."


def get_legal_urbanize_actions(state: GameState) -> list[Action]:
    if state.phase != PHASE_ACTION:
        return []
    if not (
        can_pay(state, state.config.urbanize_cost)
        or state.config.auto_issue_bonds_when_needed
    ):
        return []
    return [
        Action.urbanize(city.id)
        for city in state.cities.values()
        if city.is_gray
    ]


def pass_action(state: GameState) -> tuple[bool, str]:
    ok, message = _ensure_action_phase(state)
    if not ok:
        return False, message
    state.record(f"Turn {state.turn}: passed one action.")
    consume_action(state)
    return True, "Passed one action."


def select_operation_card(state: GameState, card_id: str) -> tuple[bool, str]:
    ok, message = _ensure_action_phase(state)
    if not ok:
        return False, message
    selected, select_message = apply_card_on_select(state, card_id)
    if not selected:
        return False, select_message
    consume_action(state)
    return True, select_message


def update_empty_city_marker(state: GameState, city_id: str) -> None:
    city = state.get_city(city_id)
    if city is None:
        return
    if not city.goods and not city.empty_marker:
        city.empty_marker = True
        state.record(f"Turn {state.turn}: {city.name} received an empty city marker.")


def count_empty_city_markers(state: GameState) -> int:
    return sum(1 for city in state.cities.values() if city.empty_marker)


def check_end_condition(state: GameState) -> None:
    if state.end_triggered:
        return

    triggered = False
    if state.config.end_condition == "fixed_turns":
        triggered = state.turn >= state.config.max_turns
    elif state.config.end_condition == "empty_city_markers":
        triggered = count_empty_city_markers(state) >= state.config.empty_city_marker_limit

    if not triggered:
        return

    state.end_triggered = True
    state.extra_turns_remaining = (
        1 if state.config.extra_turn_after_end_trigger else 0
    )
    state.record(
        (
            f"Turn {state.turn}: end condition triggered "
            f"({state.config.end_condition})."
        )
    )


def is_terminal(state: GameState) -> bool:
    return state.phase == PHASE_GAME_OVER


def check_major_lines(state: GameState) -> None:
    for line in state.major_lines.values():
        if line.claimed:
            continue
        path = find_shortest_built_path(state, line.source, line.target)
        if path is None:
            continue
        line.claimed = True
        state.player.major_line_bonus += line.bonus_points
        state.record(
            (
                f"Turn {state.turn}: claimed major line {line.id} "
                f"(+{line.bonus_points})."
            )
        )


def apply_action(state: GameState, action: Action) -> tuple[bool, str]:
    if action.action_type == "build_track":
        return build_track(state, str(action.params["edge_id"]))
    if action.action_type == "deliver_good":
        return deliver_good(
            state,
            str(action.params["source"]),
            str(action.params["target"]),
            str(action.params["good_color"]),
            action.params.get("path"),
        )
    if action.action_type == "upgrade_engine":
        return upgrade_engine(state)
    if action.action_type == "urbanize":
        return urbanize(
            state,
            str(action.params["city_id"]),
            action.params.get("demand_color"),
        )
    if action.action_type == "issue_bond":
        return issue_bond(state)
    if action.action_type == "select_operation_card":
        return select_operation_card(state, str(action.params["card_id"]))
    if action.action_type == "pass":
        return pass_action(state)
    if action.action_type == "next_turn":
        return next_turn(state)
    return False, f"Unknown action type: {action.action_type}."


def describe_action(action: Action | None) -> str:
    if action is None:
        return "No action."
    if action.action_type == "build_track":
        return f"Build track {action.params['edge_id']}"
    if action.action_type == "deliver_good":
        return (
            f"Deliver {action.params['good_color']} from "
            f"{action.params['source']} to {action.params['target']}"
        )
    if action.action_type == "upgrade_engine":
        return "Upgrade engine"
    if action.action_type == "urbanize":
        return f"Urbanize city {action.params['city_id']}"
    if action.action_type == "issue_bond":
        return "Issue one bond"
    if action.action_type == "select_operation_card":
        return f"Select operation card {action.params.get('card_id', '')}"
    if action.action_type == "pass":
        return "Pass"
    if action.action_type == "next_turn":
        return "End turn"
    return str(action)


def _ensure_action_phase(state: GameState) -> tuple[bool, str]:
    if state.phase == PHASE_GAME_OVER:
        return False, "Game is over."
    if state.phase != PHASE_ACTION:
        return False, f"Current phase is {state.phase}, not action."
    if state.actions_remaining <= 0:
        return False, "No actions remaining this turn."
    return True, "Action phase is active."
