from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit.testing.v1 import AppTest

from experiments import demo_agent_animation_app as demo_app


def test_demo_app_imports() -> None:
    assert callable(demo_app.main)


def test_demo_options_are_discoverable() -> None:
    assert demo_app.available_map_names() == ["official_like", "expanded"]
    assert demo_app.available_agent_names() == [
        "random",
        "greedy_delivery",
        "greedy_expansion",
        "route_segment_greedy",
        "objective_aware_greedy",
        "adaptive_objective_greedy",
    ]
    assert demo_app.FRAME_MODE_OPTIONS == ("all", "events")


def test_demo_app_renders_run_configuration() -> None:
    app_path = PROJECT_ROOT / "experiments" / "demo_agent_animation_app.py"
    rendered = AppTest.from_file(str(app_path)).run(
        timeout=20,
    )
    assert not rendered.exception
    selectors = {item.label: list(item.options) for item in rendered.selectbox}
    assert selectors["Map"] == ["official_like", "expanded"]
    assert selectors["Agent"] == demo_app.available_agent_names()
    assert selectors["Frame mode"] == ["all", "events"]
    assert any(item.label == "Seed" for item in rendered.number_input)
    assert any(item.label == "Max steps" for item in rendered.number_input)
    assert any(
        item.label == "Run agent and generate replay" for item in rendered.button
    )


def run_all() -> None:
    tests = [
        test_demo_app_imports,
        test_demo_options_are_discoverable,
        test_demo_app_renders_run_configuration,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} agent animation app smoke tests passed.")


if __name__ == "__main__":
    run_all()
