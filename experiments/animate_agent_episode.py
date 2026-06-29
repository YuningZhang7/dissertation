from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import random
import re
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.registry import create_agent, list_agent_names
from railways.actions import Action
from railways.environment import (
    apply_action,
    get_legal_actions,
    is_terminal,
    reset_game,
)
from railways.rules import describe_action
from railways.visualization import render_game_state


MAP_PATHS = {
    "official_like": (
        PROJECT_ROOT / "data" / "official_like_route_segment_map.json"
    ),
    "expanded": (
        PROJECT_ROOT / "data" / "expanded_official_style_route_segment_map.json"
    ),
}
DEFAULT_CONFIG_PATH = (
    PROJECT_ROOT / "data" / "official_single_player_rules_config.json"
)
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT / "experiments" / "outputs" / "agent_animations"
)


def run_agent_episode_animation(
    map_name: str = "official_like",
    agent_name: str = "route_segment_greedy",
    seed: int = 42,
    max_steps: int = 60,
    map_path: str | Path | None = None,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    make_gif: bool = False,
    frame_duration_ms: int = 700,
) -> tuple[Path, dict[str, Any]]:
    if max_steps <= 0:
        raise ValueError("max_steps must be positive.")
    if frame_duration_ms <= 0:
        raise ValueError("frame_duration_ms must be positive.")
    available_agents = list_agent_names()
    if agent_name not in available_agents:
        raise ValueError(
            f"Unknown agent {agent_name!r}. Available agents: "
            f"{', '.join(available_agents)}"
        )
    if map_path is None and map_name not in MAP_PATHS:
        raise ValueError(
            f"Unknown map {map_name!r}. Available maps: {', '.join(MAP_PATHS)}"
        )

    selected_map_path = Path(map_path) if map_path is not None else MAP_PATHS[map_name]
    selected_config_path = Path(config_path)
    selected_map_name = selected_map_path.stem if map_path is not None else map_name
    run_name = (
        f"{_safe_name(selected_map_name)}_{_safe_name(agent_name)}_seed{seed}"
    )
    run_dir = Path(output_root) / run_name
    frames_dir = run_dir / "frames"
    _prepare_output_directory(run_dir, frames_dir)

    random.seed(seed)
    state = reset_game(
        map_path=selected_map_path,
        config_path=selected_config_path,
    )
    agent = create_agent(agent_name, seed=seed)
    frames: list[dict[str, Any]] = []
    log_entries: list[dict[str, Any]] = []
    steps_executed = 0
    fallback_actions = 0
    episode_success = True
    error = ""

    try:
        initial_path = frames_dir / "frame_000_initial.png"
        render_game_state(state, initial_path)
        frames.append(
            {
                "step": 0,
                "action_type": "initial",
                "description": "Initial state",
                "path": initial_path,
            }
        )

        while not is_terminal(state) and steps_executed < max_steps:
            legal_actions = get_legal_actions(state)
            if not legal_actions:
                break

            try:
                chosen_action = agent.choose_action(state)
            except Exception as exc:
                episode_success = False
                error = f"{type(exc).__name__}: {exc}"
                break

            chosen_type = (
                chosen_action.action_type
                if isinstance(chosen_action, Action)
                else "none"
            )
            chosen_params = (
                dict(chosen_action.params)
                if isinstance(chosen_action, Action)
                else {}
            )
            action = chosen_action
            fallback_note = ""
            if action is None or action not in legal_actions:
                fallback_actions += 1
                fallback = Action.pass_action()
                if fallback not in legal_actions:
                    episode_success = False
                    error = "Agent returned an illegal action and no pass fallback was legal."
                    break
                action = fallback
                fallback_note = "Agent action was None or illegal; used pass fallback. "

            _, applied, message = apply_action(state, action)
            if not applied:
                fallback_actions += 1
                failed_message = message
                fallback = Action.pass_action()
                if fallback not in get_legal_actions(state):
                    episode_success = False
                    error = (
                        "Action failed and no pass fallback was legal: "
                        f"{failed_message}"
                    )
                    break
                _, fallback_applied, fallback_message = apply_action(state, fallback)
                if not fallback_applied:
                    episode_success = False
                    error = f"Pass fallback failed: {fallback_message}"
                    break
                action = fallback
                applied = True
                message = (
                    f"Original action failed: {failed_message} "
                    f"Pass fallback: {fallback_message}"
                )
                fallback_note = "Used pass fallback after apply failure. "

            steps_executed += 1
            description = describe_action(action)
            frame_path = frames_dir / (
                f"frame_{steps_executed:03d}_{_safe_name(action.action_type)}.png"
            )
            render_game_state(state, frame_path)
            frames.append(
                {
                    "step": steps_executed,
                    "action_type": action.action_type,
                    "description": description,
                    "path": frame_path,
                }
            )
            log_entries.append(
                _episode_log_entry(
                    state=state,
                    step=steps_executed,
                    chosen_type=chosen_type,
                    chosen_params=chosen_params,
                    applied_action=action,
                    applied=applied,
                    message=f"{fallback_note}{message}".strip(),
                )
            )
    except Exception as exc:
        episode_success = False
        error = f"{type(exc).__name__}: {exc}"

    summary = _episode_summary(
        state=state,
        map_name=selected_map_name,
        map_path=selected_map_path,
        agent_name=agent_name,
        seed=seed,
        max_steps=max_steps,
        steps_executed=steps_executed,
        fallback_actions=fallback_actions,
        success=episode_success,
        error=error,
        frames_count=len(frames),
    )
    _write_episode_log(run_dir / "episode_log.txt", summary, log_entries)
    _write_summary(run_dir / "episode_summary.json", summary)
    _write_html_index(
        run_dir / "index.html",
        frames,
        summary,
        frame_duration_ms,
    )
    if make_gif and frames:
        gif_path = _try_write_gif(
            [frame["path"] for frame in frames],
            run_dir / "episode.gif",
            frame_duration_ms,
        )
        if gif_path is None:
            print("Warning: GIF generation was unavailable; PNG/HTML replay is complete.")

    return run_dir, summary


def _episode_log_entry(
    state,
    step: int,
    chosen_type: str,
    chosen_params: dict[str, Any],
    applied_action: Action,
    applied: bool,
    message: str,
) -> dict[str, Any]:
    return {
        "step": step,
        "turn": state.turn,
        "phase": state.phase,
        "actions_remaining": state.actions_remaining,
        "chosen_action_type": chosen_type,
        "chosen_action_params": chosen_params,
        "applied_action_type": applied_action.action_type,
        "applied_action_params": dict(applied_action.params),
        "apply_succeeded": bool(applied),
        "message": message,
        "score": state.player.score,
        "money": state.player.money,
        "bonds": state.player.bonds,
        "major_line_bonus": state.player.major_line_bonus,
        "rail_baron_bonus": state.player.rail_baron_bonus,
        "delivered_goods_count": state.player.delivered_goods_count,
        "completed_routes_count": sum(
            route.completed for route in state.routes.values()
        ),
    }


def _episode_summary(
    state,
    map_name: str,
    map_path: Path,
    agent_name: str,
    seed: int,
    max_steps: int,
    steps_executed: int,
    fallback_actions: int,
    success: bool,
    error: str,
    frames_count: int,
) -> dict[str, Any]:
    return {
        "map_name": map_name,
        "map_path": str(map_path),
        "agent_name": agent_name,
        "seed": seed,
        "max_steps": max_steps,
        "steps_executed": steps_executed,
        "terminal": is_terminal(state),
        "final_score": state.final_score(),
        "money": state.player.money,
        "bonds": state.player.bonds,
        "locomotive_level": state.player.locomotive_level,
        "delivered_goods_count": state.player.delivered_goods_count,
        "major_line_bonus": state.player.major_line_bonus,
        "rail_baron_bonus": state.player.rail_baron_bonus,
        "rail_baron_objectives_completed": (
            state.player.rail_baron_objectives_completed
        ),
        "claimed_major_lines_count": sum(
            line.claimed for line in state.major_lines.values()
        ),
        "completed_routes_count": sum(
            route.completed for route in state.routes.values()
        ),
        "built_segments_count": sum(
            segment.built for segment in state.segments.values()
        ),
        "completed_segments_count": sum(
            segment.completed for segment in state.segments.values()
        ),
        "fallback_actions": fallback_actions,
        "success": success,
        "error": error,
        "frames_count": frames_count,
    }


def _write_episode_log(
    path: Path,
    summary: dict[str, Any],
    entries: list[dict[str, Any]],
) -> None:
    lines = [
        f"map_name={summary['map_name']}",
        f"map_path={summary['map_path']}",
        f"agent_name={summary['agent_name']}",
        f"seed={summary['seed']}",
        f"max_steps={summary['max_steps']}",
        "",
    ]
    for entry in entries:
        lines.extend(
            [
                f"step={entry['step']}",
                (
                    f"  turn={entry['turn']} phase={entry['phase']} "
                    f"actions_remaining={entry['actions_remaining']}"
                ),
                (
                    f"  chosen={entry['chosen_action_type']} "
                    f"params={json.dumps(entry['chosen_action_params'], sort_keys=True)}"
                ),
                (
                    f"  applied={entry['applied_action_type']} "
                    f"params={json.dumps(entry['applied_action_params'], sort_keys=True)} "
                    f"success={entry['apply_succeeded']}"
                ),
                f"  message={entry['message']}",
                (
                    f"  score={entry['score']} money={entry['money']} "
                    f"bonds={entry['bonds']} major_line_bonus="
                    f"{entry['major_line_bonus']} rail_baron_bonus="
                    f"{entry['rail_baron_bonus']} deliveries="
                    f"{entry['delivered_goods_count']} completed_routes="
                    f"{entry['completed_routes_count']}"
                ),
                "",
            ]
        )
    lines.extend(
        [
            f"episode_success={summary['success']}",
            f"error={summary['error']}",
            f"final_score={summary['final_score']}",
            f"frames_count={summary['frames_count']}",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_html_index(
    path: Path,
    frames: list[dict[str, Any]],
    summary: dict[str, Any],
    frame_duration_ms: int,
) -> None:
    figures = "\n".join(
        (
            "<figure>"
            f'<img src="frames/{escape(frame["path"].name)}" '
            f'alt="step {frame["step"]}">'
            f"<figcaption>Step {frame['step']}: "
            f"{escape(frame['action_type'])} — "
            f"{escape(frame['description'])}</figcaption>"
            "</figure>"
        )
        for frame in frames
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Agent episode replay</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; background: #f7f8fa; }}
    .summary {{ padding: 1rem; background: white; border: 1px solid #bbb; }}
    figure {{ margin: 2rem 0; }}
    img {{ max-width: 100%; border: 1px solid #bbb; background: white; }}
    figcaption {{ margin-top: 0.4rem; font-weight: 600; }}
  </style>
</head>
<body>
  <h1>Agent episode replay</h1>
  <div class="summary">
    <strong>{escape(str(summary['map_name']))}</strong> ·
    {escape(str(summary['agent_name']))} · seed {summary['seed']} ·
    {summary['steps_executed']} steps · {frame_duration_ms} ms/frame ·
    success={str(summary['success']).lower()}
  </div>
  {figures}
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def _try_write_gif(
    frame_paths: list[Path],
    output_path: Path,
    frame_duration_ms: int,
) -> Path | None:
    try:
        from PIL import Image
    except ImportError:
        return None

    images = []
    try:
        for frame_path in frame_paths:
            with Image.open(frame_path) as source:
                images.append(source.convert("RGB"))
        if not images:
            return None
        target_size = images[0].size
        normalized = [
            image if image.size == target_size else image.resize(target_size)
            for image in images
        ]
        normalized[0].save(
            output_path,
            save_all=True,
            append_images=normalized[1:],
            duration=frame_duration_ms,
            loop=0,
        )
        return output_path
    except Exception as exc:
        print(f"Warning: GIF generation failed: {type(exc).__name__}: {exc}")
        return None
    finally:
        for image in images:
            image.close()


def _prepare_output_directory(run_dir: Path, frames_dir: Path) -> None:
    frames_dir.mkdir(parents=True, exist_ok=True)
    for frame in frames_dir.glob("frame_*.png"):
        frame.unlink()
    for filename in (
        "index.html",
        "episode_log.txt",
        "episode_summary.json",
        "episode.gif",
    ):
        artifact = run_dir / filename
        if artifact.exists():
            artifact.unlink()


def _safe_name(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return safe or "run"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a static visual replay of one automated agent episode."
    )
    parser.add_argument("--map", choices=sorted(MAP_PATHS), default="official_like")
    parser.add_argument("--map-path")
    parser.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument(
        "--agent",
        choices=list_agent_names(),
        default="route_segment_greedy",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-steps", type=int, default=60)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--make-gif", action="store_true")
    parser.add_argument("--frame-duration-ms", type=int, default=700)
    args = parser.parse_args()
    if args.max_steps <= 0:
        parser.error("--max-steps must be positive")
    if args.frame_duration_ms <= 0:
        parser.error("--frame-duration-ms must be positive")
    return args


def main() -> None:
    args = parse_args()
    run_dir, summary = run_agent_episode_animation(
        map_name=args.map,
        map_path=args.map_path,
        config_path=args.config_path,
        agent_name=args.agent,
        seed=args.seed,
        max_steps=args.max_steps,
        output_root=args.output_dir,
        make_gif=args.make_gif,
        frame_duration_ms=args.frame_duration_ms,
    )
    print(f"Animation output: {run_dir}")
    print(
        f"Episode: steps={summary['steps_executed']} "
        f"terminal={summary['terminal']} final_score={summary['final_score']} "
        f"fallbacks={summary['fallback_actions']} success={summary['success']}"
    )
    if summary["error"]:
        print(f"Episode error: {summary['error']}")


if __name__ == "__main__":
    main()
