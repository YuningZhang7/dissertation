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
APP_TITLE = "Railways AI Simulator"
APP_SUBTITLE = "Agent Replay and Strategy Analysis"
APP_DESCRIPTION = (
    "This interface uses the route-segment official-style simulator. Track "
    "construction is performed at segment level, deliveries require completed "
    "routes, and Major Line / Rail Baron objectives are evaluated on the "
    "completed-route network."
)
RECOMMENDED_AGENT = "lookahead_greedy"
PUBLIC_AGENT_OPTIONS = (
    "random",
    "greedy_delivery",
    "greedy_expansion",
    "objective_aware_greedy",
    "lookahead_greedy",
)
DEFAULT_MAP = "official_like"
DEFAULT_FRAME_MODE = "events"
DEFAULT_MAX_STEPS = 30
MAP_SELECTION_CAPTION = (
    "official_like is compact and easier to inspect; expanded_official_style "
    "provides a larger route-segment network with more objectives."
)
AGENT_SELECTION_CAPTION = (
    "Select one of the five public agents. random, greedy_delivery, and "
    "greedy_expansion are included as simple baselines. objective_aware_greedy "
    "is the one-step heuristic baseline. lookahead_greedy is the "
    "balanced replay-friendly lookahead variant that "
    "prioritizes route completion and delivery before conservative urbanization."
)


def available_map_names() -> list[str]:
    return list(MAP_OPTIONS)


def available_agent_names() -> list[str]:
    registered_agents = set(list_agent_names())
    return [
        agent_name
        for agent_name in PUBLIC_AGENT_OPTIONS
        if agent_name in registered_agents
    ]


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
    score_label = "Terminal final score" if summary["terminal"] else "Truncated score"
    first_row = st.columns(4)
    first_row[0].metric(score_label, summary["final_score"])
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
    if not summary["terminal"]:
        st.caption(
            "The episode stopped at the maximum-step horizon before game over. "
            "The displayed value is a truncated score, not a terminal final score."
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
    st.subheader(APP_SUBTITLE)
    st.caption(APP_DESCRIPTION)

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
        agent_options = available_agent_names()
        default_agent_index = (
            agent_options.index(RECOMMENDED_AGENT)
            if RECOMMENDED_AGENT in agent_options
            else 0
        )
        agent_name = st.selectbox(
            "Agent", options=agent_options, index=default_agent_index
        )
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
            value=DEFAULT_MAX_STEPS,
            step=10,
            help=(
                "The 30-step default keeps an interactive replay responsive. "
                "Non-terminal runs are reported as truncated scores."
            ),
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
