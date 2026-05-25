from __future__ import annotations

import streamlit as st

from agents.registry import create_agent, list_agent_names
from railways.actions import Action
from railways.environment import apply_action, get_legal_actions, reset_game
from railways.game_state import GameState
from railways.rules import (
    count_empty_city_markers,
    describe_action,
    get_engine_upgrade_cost,
    get_legal_build_actions,
    get_legal_deliveries,
    get_legal_upgrade_action,
    get_legal_urbanize_actions,
)
from railways.visualization import draw_map


def create_game_state() -> GameState:
    return reset_game()


def initialise_session() -> None:
    if "game_state" not in st.session_state:
        st.session_state.game_state = create_game_state()
    if "last_message" not in st.session_state:
        st.session_state.last_message = "Game ready."


def submit_action(action: Action) -> None:
    state: GameState = st.session_state.game_state
    _, success, message = apply_action(state, action)
    prefix = "OK" if success else "Failed"
    st.session_state.last_message = f"{prefix}: {message}"
    st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="Railways of the World AI Simulator",
        layout="wide",
    )
    initialise_session()

    state: GameState = st.session_state.game_state

    st.title("Railways of the World AI Simulator")
    st.caption(
        "Single-player rule-development prototype. Advanced AI agents will be "
        "added after the rule engine is stabilised."
    )

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
    metric_col_a.metric("Turn", f"{state.turn} / {state.config.max_turns}")
    metric_col_b.metric("Phase", state.phase)
    metric_col_a.metric("Actions Left", state.actions_remaining)
    metric_col_b.metric("Money", state.player.money)
    metric_col_a.metric("Score", state.player.score)
    metric_col_b.metric("Final Estimate", state.final_score())
    metric_col_a.metric("Bonds", state.player.bonds)
    metric_col_b.metric(
        "Interest Due",
        state.player.bonds * state.config.bond_interest,
    )
    metric_col_a.metric("Engine Level", state.player.locomotive_level)
    metric_col_b.metric("Delivered", state.player.delivered_goods_count)
    metric_col_a.metric("Major Line Bonus", state.player.major_line_bonus)
    metric_col_b.metric("Empty Markers", count_empty_city_markers(state))


def render_manual_controls(state: GameState) -> None:
    st.subheader("Manual Actions")
    controls_disabled = state.is_terminal()

    render_build_controls(state, controls_disabled)
    st.divider()
    render_delivery_controls(state, controls_disabled)
    st.divider()
    render_upgrade_and_urbanize_controls(state, controls_disabled)
    st.divider()
    render_turn_controls(state, controls_disabled)


def render_agent_controls(state: GameState) -> None:
    st.subheader("Automated Agents")
    agent_name = st.selectbox("Agent", options=list_agent_names())
    agent_seed = st.number_input("Agent seed", value=0, step=1)
    max_steps = st.number_input("Max steps", min_value=1, max_value=2000, value=500, step=50)

    disabled = state.is_terminal()
    if st.button("Run One Agent Action", disabled=disabled):
        agent = create_agent(agent_name, seed=int(agent_seed))
        action = agent.choose_action(state)
        _, success, message = apply_action(state, action)
        st.session_state.last_message = (
            f"{agent.name} chose {describe_action(action)}: "
            f"{'OK' if success else 'failed'} ({message}). "
            f"Score: {state.final_score()}."
        )
        st.rerun()

    if st.button("Run Agent Until Game Over", disabled=disabled):
        summary = run_agent_until_terminal(state, agent_name, int(agent_seed), int(max_steps))
        st.session_state.last_message = (
            f"{agent_name} ran {summary['steps']} steps. "
            f"Final score: {state.final_score()}, "
            f"deliveries: {state.player.delivered_goods_count}, "
            f"invalid actions: {summary['invalid_actions']}."
        )
        st.rerun()

    if st.button("Reset and Run Full Simulation"):
        st.session_state.game_state = create_game_state()
        state = st.session_state.game_state
        summary = run_agent_until_terminal(state, agent_name, int(agent_seed), int(max_steps))
        st.session_state.last_message = (
            f"Reset and ran {agent_name} for {summary['steps']} steps. "
            f"Final score: {state.final_score()}, "
            f"deliveries: {state.player.delivered_goods_count}, "
            f"invalid actions: {summary['invalid_actions']}."
        )
        st.rerun()


def render_build_controls(state: GameState, controls_disabled: bool) -> None:
    build_actions = get_legal_build_actions(state)
    build_labels = {
        (
            f"{action.params['edge_id']}: "
            f"{state.edges[action.params['edge_id']].source}-"
            f"{state.edges[action.params['edge_id']].target}, "
            f"cost {state.edges[action.params['edge_id']].cost}"
        ): action
        for action in build_actions
    }

    selected_label = st.selectbox(
        "Build track",
        options=list(build_labels.keys()),
        disabled=controls_disabled or not build_labels,
    )
    if st.button("Build Track", disabled=controls_disabled or not build_labels):
        submit_action(build_labels[selected_label])


def render_delivery_controls(state: GameState, controls_disabled: bool) -> None:
    delivery_actions = get_legal_deliveries(state)
    delivery_labels = {
        (
            f"{action.params['good_color']} "
            f"{action.params['source']} -> {action.params['target']} "
            f"via {'-'.join(action.params['path'])} "
            f"(+{action.params['score']})"
        ): action
        for action in delivery_actions
    }

    selected_label = st.selectbox(
        "Legal delivery",
        options=list(delivery_labels.keys()),
        disabled=controls_disabled or not delivery_labels,
    )
    st.caption(f"Legal deliveries available: {len(delivery_actions)}")
    if st.button("Deliver Good", disabled=controls_disabled or not delivery_labels):
        submit_action(delivery_labels[selected_label])


def render_upgrade_and_urbanize_controls(
    state: GameState,
    controls_disabled: bool,
) -> None:
    upgrade_action = get_legal_upgrade_action(state)
    next_level = state.player.locomotive_level + 1
    upgrade_cost = get_engine_upgrade_cost(state, next_level)

    upgrade_col, urbanize_col = st.columns(2)
    with upgrade_col:
        if st.button(
            f"Upgrade Engine (${upgrade_cost})",
            disabled=controls_disabled or upgrade_action is None,
        ):
            submit_action(Action.upgrade_engine())

    urbanize_actions = get_legal_urbanize_actions(state)
    urbanize_labels = {
        f"{state.cities[action.params['city_id']].id}: "
        f"{state.cities[action.params['city_id']].name}": action
        for action in urbanize_actions
    }
    demand_color = st.selectbox(
        "Urbanize demand",
        options=state.config.allowed_good_colors,
        disabled=controls_disabled or not urbanize_labels,
    )
    with urbanize_col:
        selected_city = st.selectbox(
            "Urbanize city",
            options=list(urbanize_labels.keys()),
            disabled=controls_disabled or not urbanize_labels,
        )
        if st.button("Urbanize", disabled=controls_disabled or not urbanize_labels):
            base_action = urbanize_labels[selected_city]
            submit_action(
                Action.urbanize(
                    str(base_action.params["city_id"]),
                    demand_color=demand_color,
                )
            )


def render_turn_controls(state: GameState, controls_disabled: bool) -> None:
    bond_col, pass_col, end_col = st.columns(3)
    with bond_col:
        if st.button(
            "Issue Bond",
            disabled=controls_disabled or not state.config.allow_voluntary_bonds,
        ):
            submit_action(Action.issue_bond())
    with pass_col:
        if st.button("Pass Action", disabled=controls_disabled):
            submit_action(Action.pass_action())
    with end_col:
        if st.button("End Turn", disabled=state.is_terminal()):
            submit_action(Action.next_turn())

    if st.button("Reset Game"):
        st.session_state.game_state = create_game_state()
        st.session_state.last_message = "Game reset."
        st.rerun()


def render_history(state: GameState) -> None:
    st.subheader("Action History")
    previews = get_preview_actions(state)
    preview_text = ", ".join(describe_action(action) for action in previews) or "none"
    st.caption(
        "Recent actions from the rules engine. "
        f"Next legal-action examples: {preview_text}"
    )
    if not state.action_history:
        st.caption("No actions yet.")
        return

    for item in reversed(state.action_history[-14:]):
        st.write(item)


def run_agent_until_terminal(
    state: GameState,
    agent_name: str,
    seed: int,
    max_steps: int,
) -> dict[str, int]:
    agent = create_agent(agent_name, seed=seed)
    steps = 0
    invalid_actions = 0

    while not state.is_terminal() and steps < max_steps:
        action = agent.choose_action(state)
        legal_actions = get_legal_actions(state)
        if action not in legal_actions:
            invalid_actions += 1
            action = legal_actions[0] if legal_actions else Action.pass_action()

        _, success, _ = apply_action(state, action)
        if not success:
            invalid_actions += 1
            _, _, _ = apply_action(state, Action.pass_action())
        steps += 1

    return {"steps": steps, "invalid_actions": invalid_actions}


def get_preview_actions(state: GameState) -> list[Action]:
    if state.is_terminal():
        return []

    previews: list[Action] = []
    previews.extend(get_legal_build_actions(state)[:1])
    previews.extend(get_legal_deliveries(state)[:1])
    upgrade = get_legal_upgrade_action(state)
    if upgrade is not None:
        previews.append(upgrade)
    previews.extend(get_legal_urbanize_actions(state)[:1])
    previews.append(Action.pass_action())
    return previews[:4]


if __name__ == "__main__":
    main()
