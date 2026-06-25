from __future__ import annotations

from pathlib import Path

import streamlit as st

from agents.registry import create_agent, list_agent_names
from railways.actions import Action
from railways.environment import (
    DEFAULT_CARDS_PATH,
    apply_action,
    get_legal_actions,
    reset_game,
)
from railways.game_state import GameState
from railways.rules import count_empty_city_markers, describe_action
from railways.visualization import draw_map


BASE_DIR = Path(__file__).parent
MAP_OPTIONS = {
    "toy_map": BASE_DIR / "data" / "toy_map.json",
    "toy_medium_map": BASE_DIR / "data" / "toy_medium_map.json",
    "semi_realistic_map": BASE_DIR / "data" / "semi_realistic_map.json",
}
AGENT_SEED = 0
MAX_STEPS = 500


def create_game_state(map_name: str | None = None) -> GameState:
    selected_map = map_name or st.session_state.get("selected_map", "toy_map")
    return reset_game(map_path=MAP_OPTIONS[selected_map], card_path=DEFAULT_CARDS_PATH)


def initialise_session() -> None:
    if "selected_map" not in st.session_state:
        st.session_state.selected_map = "toy_map"
    if "selected_agent" not in st.session_state:
        st.session_state.selected_agent = "random"
    if "game_state" not in st.session_state:
        st.session_state.game_state = create_game_state(st.session_state.selected_map)
    if "last_message" not in st.session_state:
        st.session_state.last_message = "Game ready."


def main() -> None:
    st.set_page_config(page_title="Railway Game", layout="wide")
    initialise_session()

    st.title("Railways of the World AI Simulator")
    st.caption("Meeting-ready railway simulator with three interpretable baseline agents.")

    state: GameState = st.session_state.game_state
    if state.is_terminal():
        st.warning(f"Game over. Final score: {state.final_score()}.")
    elif st.session_state.last_message:
        st.info(st.session_state.last_message)

    map_col, control_col = st.columns([2.2, 1])
    with map_col:
        st.plotly_chart(draw_map(state), use_container_width=True)

    with control_col:
        render_selectors()
        render_agent_controls(state)
        render_player_panel(state)
        render_history(state)


def render_selectors() -> None:
    st.subheader("Simulation")
    st.selectbox(
        "Map",
        options=list(MAP_OPTIONS),
        key="selected_map",
        on_change=reset_selected_map,
    )
    st.selectbox(
        "Agent",
        options=list_agent_names(),
        key="selected_agent",
    )


def render_agent_controls(state: GameState) -> None:
    disabled = state.is_terminal()
    if st.button("Run One Agent Action", disabled=disabled, use_container_width=True):
        agent = create_agent(st.session_state.selected_agent, seed=AGENT_SEED)
        action = agent.choose_action(state)
        _, success, message = apply_action(state, action)
        st.session_state.last_message = (
            f"{agent.name} chose {describe_action(action)}: "
            f"{'OK' if success else 'failed'} ({message})."
        )
        st.rerun()

    if st.button("Run Agent Until Game Over", disabled=disabled, use_container_width=True):
        summary = run_agent_until_terminal(
            state,
            st.session_state.selected_agent,
            seed=AGENT_SEED,
            max_steps=MAX_STEPS,
        )
        st.session_state.last_message = (
            f"{st.session_state.selected_agent} ran {summary['steps']} steps. "
            f"Final score: {state.final_score()}; "
            f"invalid actions: {summary['invalid_actions']}."
        )
        st.rerun()

    if st.button("Reset Game", use_container_width=True):
        reset_selected_map()
        st.rerun()


def render_player_panel(state: GameState) -> None:
    st.subheader("Player State")
    left, right = st.columns(2)
    left.metric("Turn", f"{state.turn} / {state.config.max_turns}")
    right.metric("Phase", state.phase)
    left.metric("Actions Left", state.actions_remaining)
    right.metric("Money", state.player.money)
    left.metric("Score", state.player.score)
    right.metric("Final Estimate", state.final_score())
    left.metric("Financing Certs", state.player.bonds)
    right.metric("Engine Level", state.player.locomotive_level)
    left.metric("Delivered Goods", state.player.delivered_goods_count)
    right.metric("Built Edges", len(state.player.built_edges))
    left.metric("Major Line Bonus", state.player.major_line_bonus)
    right.metric("Card Bonus", state.player.operation_card_bonus)
    left.metric("Empty Markers", count_empty_city_markers(state))


def render_history(state: GameState) -> None:
    st.subheader("Action History")
    if not state.action_history:
        st.caption("No actions yet.")
        return
    for item in reversed(state.action_history[-16:]):
        st.write(item)


def reset_selected_map() -> None:
    selected_map = st.session_state.get("selected_map", "toy_map")
    st.session_state.game_state = create_game_state(selected_map)
    st.session_state.last_message = f"Loaded {selected_map}."


def run_agent_until_terminal(
    state: GameState,
    agent_name: str,
    seed: int = AGENT_SEED,
    max_steps: int = MAX_STEPS,
) -> dict[str, int]:
    agent = create_agent(agent_name, seed=seed)
    steps = 0
    invalid_actions = 0

    while not state.is_terminal() and steps < max_steps:
        legal_actions = get_legal_actions(state)
        action = agent.choose_action(state)
        if action not in legal_actions:
            invalid_actions += 1
            action = legal_actions[0] if legal_actions else Action.pass_action()

        _, success, _ = apply_action(state, action)
        if not success:
            invalid_actions += 1
            _, _, _ = apply_action(state, Action.pass_action())
        steps += 1

    return {"steps": steps, "invalid_actions": invalid_actions}


if __name__ == "__main__":
    main()
