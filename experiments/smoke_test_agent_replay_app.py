from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit.testing.v1 import AppTest

from experiments import agent_replay_app as replay_app


EXPECTED_PUBLIC_AGENTS = [
    "random",
    "greedy_delivery",
    "greedy_expansion",
    "objective_aware_greedy",
    "lookahead_greedy",
]


def test_replay_app_imports() -> None:
    assert callable(replay_app.main)


def test_replay_options_are_discoverable() -> None:
    assert replay_app.available_map_names() == [
        "official_like",
        "expanded_official_style",
    ]
    assert replay_app.available_agent_names() == EXPECTED_PUBLIC_AGENTS
    assert replay_app.FRAME_MODE_OPTIONS == ("all", "events")
    assert replay_app.DEFAULT_MAX_STEPS == 30


def test_replay_interface_uses_formal_product_naming() -> None:
    assert replay_app.APP_TITLE == "Railways AI Simulator"
    assert replay_app.APP_SUBTITLE == "Agent Replay and Strategy Analysis"
    assert replay_app.RECOMMENDED_AGENT == "lookahead_greedy"
    assert replay_app.PUBLIC_AGENT_OPTIONS == tuple(EXPECTED_PUBLIC_AGENTS)
    source = Path(replay_app.__file__).read_text(encoding="utf-8")
    for removed_label in (
        "Simulator" + " rule summary",
        "Recommended agent:" + " objective_aware_greedy",
        "Benchmark" + " status",
        "Show all" + " agents",
        "meeting" + " replay",
        "presentation" + " agents",
    ):
        assert removed_label not in source
    assert "Terminal final score" in source
    assert "Truncated score" in source


def test_replay_app_renders_run_configuration() -> None:
    app_path = PROJECT_ROOT / "experiments" / "agent_replay_app.py"
    rendered = AppTest.from_file(str(app_path)).run(
        timeout=20,
    )
    assert not rendered.exception
    assert rendered.title[0].value == replay_app.APP_TITLE
    assert rendered.subheader[0].value == replay_app.APP_SUBTITLE
    assert not rendered.expander
    selectors = {item.label: list(item.options) for item in rendered.selectbox}
    assert selectors["Map"] == ["official_like", "expanded_official_style"]
    assert selectors["Agent"] == EXPECTED_PUBLIC_AGENTS
    assert selectors["Frame mode"] == ["all", "events"]
    assert rendered.selectbox[0].value == "official_like"
    assert rendered.selectbox[1].value == "lookahead_greedy"
    assert rendered.selectbox[2].value == "events"
    assert not any(item.label == "Show all agents" for item in rendered.checkbox)
    number_inputs = {item.label: item.value for item in rendered.number_input}
    assert "Seed" in number_inputs
    assert number_inputs["Max steps"] == 30
    assert any(
        item.label == "Run agent and generate replay" for item in rendered.button
    )


def run_all() -> None:
    tests = [
        test_replay_app_imports,
        test_replay_options_are_discoverable,
        test_replay_interface_uses_formal_product_naming,
        test_replay_app_renders_run_configuration,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} agent replay app smoke tests passed.")


if __name__ == "__main__":
    run_all()
