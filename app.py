from __future__ import annotations

from pathlib import Path

import streamlit as st

from agents.greedy_agent import choose_greedy_action
from agents.random_agent import choose_random_action
from railways.game_state import GameState
from railways.rules import (
    apply_action,
    build_track,
    deliver_good,
    describe_action,
    get_legal_deliveries,
    issue_bond,
    next_turn,
    upgrade_locomotive,
)
from railways.visualization import draw_map

BASE_DIR = Path(__file__).parent
MAP_PATH = BASE_DIR / "data" / "toy_map.json"
CONFIG_PATH = BASE_DIR / "data" / "rules_config.json"


def create_game_state() -> GameState:
    return GameState.from_files(MAP_PATH, CONFIG_PATH)


def initialise_session() -> None:
    if "game_state" not in st.session_state:
        st.session_state.game_state = create_game_state()
    if "last_message" not in st.session_state:
        st.session_state.last_message = "Game ready."


def set_message(message: str) -> None:
    st.session_state.last_message = message


def main() -> None:
    st.set_page_config(
        page_title="Railways of the World AI Simulator",
        layout="wide",
    )
    initialise_session()

    state: GameState = st.session_state.game_state

    st.title("Railways of the World AI Simulator")
    st.caption("Simplified single-player visual prototype for dissertation experiments.")

    if state.is_terminal():
        st.warning(
            f"Game over. Final score: {state.final_score()} "
            f"(raw score {state.player.score}, bonds {state.player.bonds})."
        )
    elif st.session_state.last_message:
        st.info(st.session_state.last_message)

    map_col, side_col = st.columns([2.2, 1])

    with map_col:
        st.plotly_chart(draw_map(state), use_container_width=True)

    with side_col:
        render_player_panel(state)
        render_manual_controls(state)
        render_agent_controls(state)
        render_history(state)


def render_player_panel(state: GameState) -> None:
    st.subheader("Player State")
    metric_col_a, metric_col_b = st.columns(2)
    metric_col_a.metric("Turn", f"{state.player.turn} / {state.player.max_turns}")
    metric_col_b.metric("Money", state.player.money)
    metric_col_a.metric("Score", state.player.score)
    metric_col_b.metric("Final Estimate", state.final_score())
    metric_col_a.metric("Bonds", state.player.bonds)
    metric_col_b.metric("Locomotive", state.player.locomotive_level)
    st.metric("Delivered Goods", state.player.delivered_goods_count)


def render_manual_controls(state: GameState) -> None:
    st.subheader("Manual Actions")
    controls_disabled = state.is_terminal()

    unbuilt_edges = [edge for edge in state.edges.values() if not edge.built]
    edge_labels = {
        f"{edge.id}: {edge.source}-{edge.target}, cost {edge.cost}": edge.id
        for edge in unbuilt_edges
    }
    selected_edge_label = st.selectbox(
        "Build track",
        options=list(edge_labels.keys()),
        disabled=controls_disabled or not edge_labels,
    )
    if st.button("Build Track", disabled=controls_disabled or not edge_labels):
        edge_id = edge_labels[selected_edge_label]
        if build_track(state, edge_id):
            set_message(f"Built track {edge_id}.")
        else:
            set_message(f"Could not build track {edge_id}. Check money and status.")
        st.rerun()

    bond_col, upgrade_col = st.columns(2)
    with bond_col:
        if st.button("Issue Bond", disabled=controls_disabled):
            issue_bond(state)
            set_message("Issued one bond.")
            st.rerun()
    with upgrade_col:
        upgrade_cost = state.player.locomotive_level * state.config.upgrade_cost_multiplier
        if st.button(
            f"Upgrade (${upgrade_cost})",
            disabled=controls_disabled
            or state.player.locomotive_level >= state.config.max_locomotive_level,
        ):
            if upgrade_locomotive(state):
                set_message("Locomotive upgraded.")
            else:
                set_message("Could not upgrade locomotive.")
            st.rerun()

    st.divider()
    render_delivery_controls(state, controls_disabled)

    turn_col, reset_col = st.columns(2)
    with turn_col:
        if st.button("Next Turn", disabled=state.player.turn > state.player.max_turns):
            next_turn(state)
            set_message(f"Advanced to turn {state.player.turn}.")
            st.rerun()
    with reset_col:
        if st.button("Reset Game"):
            st.session_state.game_state = create_game_state()
            set_message("Game reset.")
            st.rerun()


def render_delivery_controls(state: GameState, controls_disabled: bool) -> None:
    city_labels = {
        f"{city.id}: {city.name}": city.id for city in state.cities.values()
    }
    source_label = st.selectbox(
        "Delivery source",
        options=list(city_labels.keys()),
        disabled=controls_disabled,
    )
    source_id = city_labels[source_label]
    source_city = state.cities[source_id]

    target_label = st.selectbox(
        "Delivery target",
        options=list(city_labels.keys()),
        disabled=controls_disabled,
    )
    target_id = city_labels[target_label]

    goods_options = sorted(set(source_city.goods))
    selected_good = st.selectbox(
        "Good color",
        options=goods_options,
        disabled=controls_disabled or not goods_options,
    )

    legal_deliveries = get_legal_deliveries(state)
    st.caption(f"Legal deliveries available: {len(legal_deliveries)}")

    if st.button("Deliver Good", disabled=controls_disabled or not goods_options):
        if deliver_good(state, source_id, target_id, selected_good):
            set_message(f"Delivered {selected_good} from {source_id} to {target_id}.")
        else:
            set_message(
                "Delivery failed. Check source goods, target demand, built path, "
                "and locomotive level."
            )
        st.rerun()


def render_agent_controls(state: GameState) -> None:
    st.subheader("Baseline Agents")
    controls_disabled = state.is_terminal()
    random_col, greedy_col = st.columns(2)

    with random_col:
        if st.button("Random Action", disabled=controls_disabled):
            action = choose_random_action(state)
            success = apply_action(state, action)
            set_message(
                f"Random agent chose: {describe_action(action)} "
                f"({'ok' if success else 'failed'})."
            )
            st.rerun()

    with greedy_col:
        if st.button("Greedy Action", disabled=controls_disabled):
            action = choose_greedy_action(state)
            success = apply_action(state, action)
            set_message(
                f"Greedy agent chose: {describe_action(action)} "
                f"({'ok' if success else 'failed'})."
            )
            st.rerun()

    if st.button("Run Greedy Until End", disabled=controls_disabled):
        steps = 0
        while not state.is_terminal() and steps < 200:
            action = choose_greedy_action(state)
            apply_action(state, action)
            steps += 1
        set_message(
            f"Greedy run finished in {steps} actions. Final score: {state.final_score()}."
        )
        st.rerun()


def render_history(state: GameState) -> None:
    st.subheader("Action History")
    if not state.player.action_history:
        st.caption("No actions yet.")
        return

    for item in reversed(state.player.action_history[-12:]):
        st.write(item)


if __name__ == "__main__":
    main()
