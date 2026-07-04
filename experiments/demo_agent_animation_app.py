from __future__ import annotations

import base64
from pathlib import Path
import re
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import streamlit.components.v1 as components

from agents.registry import list_agent_names
from experiments.animate_agent_episode import (
    MAP_PATHS,
    run_agent_episode_animation,
)

MAP_OPTIONS = tuple(MAP_PATHS)
FRAME_MODE_OPTIONS = ("all", "events")
APP_TITLE = "Agent Replay Interface"
APP_DESCRIPTION = (
    "Choose a map and agent, then generate an automatic replay with rendered "
    "frames, summary metrics, and action history."
)
RECOMMENDED_AGENT = "objective_aware_greedy"
DEFAULT_MAP = "official_like"
DEFAULT_FRAME_MODE = "events"
MAP_SELECTION_CAPTION = (
    "official_like is compact and easier to inspect; expanded provides a larger "
    "route-segment network with more objectives."
)
AGENT_SELECTION_CAPTION = (
    "objective_aware_greedy is the current recommended heuristic based on "
    "development benchmark diagnostics. Other agents are available for baseline "
    "and experimental comparison."
)
RULE_SUMMARY_TEXT = (
    "The current simulator is an official-compatible single-player abstraction. "
    "It focuses on route-segment construction, route completion, completed-route "
    "delivery, Major Line scoring, Rail Baron objectives, bonds, and final-score "
    "calculation. It is not intended to reproduce every official multiplayer rule."
)
RULE_SUMMARY_BULLETS = (
    "route-segment construction",
    "route completion",
    "completed-route delivery",
    "Major Line bonus",
    "Rail Baron objective",
    "bonds and final score",
    "official_like and expanded route-segment maps",
)
RECOMMENDED_AGENT_EXPLANATION = (
    "objective_aware_greedy is a deterministic heuristic agent. It evaluates "
    "candidate actions by simulating them on copied states and scoring their "
    "contribution to delivery opportunities, route completion, Rail Baron progress, "
    "Major Line progress, construction cost, and debt. It is intended as an "
    "interpretable heuristic baseline rather than an optimal planner."
)
BENCHMARK_STATUS_TEXT = (
    "Development benchmark diagnostics currently favour objective_aware_greedy "
    "over the simpler route_segment_greedy baseline and the more complex "
    "adaptive_objective_greedy variant. These diagnostics guide the default "
    "interface settings, but longer multi-seed evaluations are still needed before "
    "making final dissertation-level claims."
)


def available_map_names() -> list[str]:
    return list(MAP_OPTIONS)


def available_agent_names(show_all: bool) -> list[str]:
    registered_agents = list_agent_names()
    if show_all:
        return registered_agents
    return [RECOMMENDED_AGENT] if RECOMMENDED_AGENT in registered_agents else []


def _resolve_custom_map_path(value: str) -> Path | None:
    if not value.strip():
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def _embed_replay_html(index_path: Path) -> str:
    """Inline generated PNGs so the replay works inside a Streamlit iframe."""
    html = index_path.read_text(encoding="utf-8")
    run_dir = index_path.parent.resolve()

    def replace_image(match: re.Match[str]) -> str:
        relative_path = match.group(0)
        image_path = (run_dir / relative_path).resolve()
        if not image_path.is_relative_to(run_dir) or not image_path.is_file():
            return relative_path
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    return re.sub(r"frames/[^\"'<>\s]+\.png", replace_image, html)


def _render_summary(summary: dict[str, Any]) -> None:
    st.subheader("Episode summary")
    first_row = st.columns(4)
    first_row[0].metric("Final score", summary["final_score"])
    first_row[1].metric("Money", summary["money"])
    first_row[2].metric("Bonds", summary["bonds"])
    first_row[3].metric("Deliveries", summary["delivered_goods_count"])

    second_row = st.columns(4)
    second_row[0].metric("Steps", summary["steps_executed"])
    second_row[1].metric("Rendered frames", summary["frames_count"])
    second_row[2].metric("Major Line bonus", summary["major_line_bonus"])
    second_row[3].metric("Rail Baron bonus", summary["rail_baron_bonus"])

    st.caption(
        f"Map: {summary['map_name']} · Agent: {summary['agent_name']} · "
        f"Seed: {summary['seed']} · Frame mode: {summary['frame_mode']} · "
        f"Terminal: {summary['terminal']} · Success: {summary['success']}"
    )
    if summary["error"]:
        st.error(summary["error"])


def _render_result(run_dir: Path, summary: dict[str, Any]) -> None:
    index_path = run_dir / "index.html"
    st.success("Agent episode and replay generated.")
    st.write("Output directory")
    st.code(str(run_dir), language=None)
    _render_summary(summary)

    st.subheader("Replay access")
    st.markdown(f"[Open generated index.html]({index_path.as_uri()})")
    st.caption(
        "The replay is embedded below. You can also copy the path above and open "
        "index.html directly in a browser."
    )
    components.html(
        _embed_replay_html(index_path),
        height=900,
        scrolling=True,
    )


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
    )
    st.title(APP_TITLE)
    st.caption(APP_DESCRIPTION)

    with st.expander("Simulator rule summary"):
        st.write(RULE_SUMMARY_TEXT)
        st.markdown("\n".join(f"- {item}" for item in RULE_SUMMARY_BULLETS))

    with st.expander(f"Recommended agent: {RECOMMENDED_AGENT}"):
        st.write(RECOMMENDED_AGENT_EXPLANATION)

    with st.expander("Benchmark status"):
        st.write(BENCHMARK_STATUS_TEXT)

    selector_col, agent_col = st.columns(2)
    with selector_col:
        map_options = available_map_names()
        map_name = st.selectbox(
            "Map", options=map_options, index=map_options.index(DEFAULT_MAP)
        )
        st.caption(MAP_SELECTION_CAPTION)
        custom_map_value = st.text_input(
            "Custom map path (optional)",
            help="When supplied, this JSON map overrides the selected built-in map.",
        )
    with agent_col:
        show_all_agents = st.checkbox("Show all agents", value=False)
        agent_options = available_agent_names(show_all_agents)
        agent_name = st.selectbox("Agent", options=agent_options, index=0)
        st.caption(AGENT_SELECTION_CAPTION)
        frame_mode = st.selectbox(
            "Frame mode",
            options=FRAME_MODE_OPTIONS,
            index=FRAME_MODE_OPTIONS.index(DEFAULT_FRAME_MODE),
        )

    settings = st.columns(3)
    seed = int(settings[0].number_input("Seed", value=42, step=1))
    max_steps = int(
        settings[1].number_input(
            "Max steps",
            min_value=1,
            max_value=5000,
            value=60,
            step=10,
        )
    )
    make_gif = settings[2].checkbox("Make GIF", value=False)

    if st.button("Run agent and generate replay", type="primary"):
        custom_map_path = _resolve_custom_map_path(custom_map_value)
        if custom_map_path is not None and not custom_map_path.is_file():
            st.error(f"Custom map file does not exist: {custom_map_path}")
        else:
            try:
                with st.spinner("Running the agent and rendering replay frames..."):
                    run_dir, summary = run_agent_episode_animation(
                        map_name=map_name,
                        map_path=custom_map_path,
                        agent_name=agent_name,
                        seed=seed,
                        max_steps=max_steps,
                        frame_mode=frame_mode,
                        make_gif=make_gif,
                    )
                st.session_state["agent_animation_result"] = {
                    "run_dir": str(run_dir.resolve()),
                    "summary": summary,
                }
            except Exception as exc:
                st.error(f"Replay generation failed: {type(exc).__name__}: {exc}")

    result = st.session_state.get("agent_animation_result")
    if result:
        _render_result(Path(result["run_dir"]), result["summary"])
    else:
        st.info("Configure the run above, then generate the replay.")


if __name__ == "__main__":
    main()
