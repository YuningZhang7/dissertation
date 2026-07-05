from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit.testing.v1 import AppTest

from experiments import demo_agent_animation_app as demo_app


EXPECTED_PRESENTATION_AGENTS = [
    "random",
    "greedy_delivery",
    "greedy_expansion",
    "objective_aware_greedy",
]
NON_PRESENTATION_AGENTS = ("route_segment_greedy", "adaptive_objective_greedy")


def test_demo_app_imports() -> None:
    assert callable(demo_app.main)


def test_demo_options_are_discoverable() -> None:
    assert demo_app.available_map_names() == [
        "official_like",
        "expanded_official_style",
    ]
    assert demo_app.available_agent_names() == EXPECTED_PRESENTATION_AGENTS
    assert demo_app.FRAME_MODE_OPTIONS == ("all", "events")


def test_replay_interface_content_is_presentation_focused() -> None:
    assert demo_app.APP_TITLE == "Agent Replay Interface"
    assert demo_app.RECOMMENDED_AGENT == "objective_aware_greedy"
    assert demo_app.PRESENTATION_AGENT_OPTIONS == tuple(EXPECTED_PRESENTATION_AGENTS)
    source = Path(demo_app.__file__).read_text(encoding="utf-8")
    for removed_label in (
        "Simulator rule summary",
        "Recommended agent: objective_aware_greedy",
        "Benchmark status",
        "Show all agents",
    ):
        assert removed_label not in source


def test_demo_app_renders_run_configuration() -> None:
    app_path = PROJECT_ROOT / "experiments" / "demo_agent_animation_app.py"
    rendered = AppTest.from_file(str(app_path)).run(
        timeout=20,
    )
    assert not rendered.exception
    assert rendered.title[0].value == demo_app.APP_TITLE
    assert not rendered.expander
    selectors = {item.label: list(item.options) for item in rendered.selectbox}
    assert selectors["Map"] == ["official_like", "expanded_official_style"]
    assert selectors["Agent"] == EXPECTED_PRESENTATION_AGENTS
    assert not set(selectors["Agent"]).intersection(NON_PRESENTATION_AGENTS)
    assert selectors["Frame mode"] == ["all", "events"]
    assert rendered.selectbox[0].value == "official_like"
    assert rendered.selectbox[1].value == "objective_aware_greedy"
    assert rendered.selectbox[2].value == "events"
    assert not any(item.label == "Show all agents" for item in rendered.checkbox)
    assert any(item.label == "Seed" for item in rendered.number_input)
    assert any(item.label == "Max steps" for item in rendered.number_input)
    assert any(
        item.label == "Run agent and generate replay" for item in rendered.button
    )


def run_all() -> None:
    tests = [
        test_demo_app_imports,
        test_demo_options_are_discoverable,
        test_replay_interface_content_is_presentation_focused,
        test_demo_app_renders_run_configuration,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} agent animation app smoke tests passed.")


if __name__ == "__main__":
    run_all()
