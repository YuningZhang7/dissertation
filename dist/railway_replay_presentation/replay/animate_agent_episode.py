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
    PROJECT_ROOT / "outputs" / "agent_animations"
)


def run_agent_episode_animation(
    map_name: str = "official_like",
    agent_name: str = "objective_aware_greedy",
    seed: int = 42,
    max_steps: int = 60,
    map_path: str | Path | None = None,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    make_gif: bool = False,
    frame_duration_ms: int = 700,
    frame_mode: str = "all",
) -> tuple[Path, dict[str, Any]]:
    if max_steps <= 0:
        raise ValueError("max_steps must be positive.")
    if frame_duration_ms <= 0:
        raise ValueError("frame_duration_ms must be positive.")
    if frame_mode not in {"all", "events"}:
        raise ValueError("frame_mode must be 'all' or 'events'.")
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
    frame_entries: list[dict[str, Any]] = []
    action_history_entries: list[dict[str, Any]] = []
    steps_executed = 0
    fallback_actions = 0
    episode_success = True
    error = ""

    try:
        initial_path = frames_dir / "frame_000_initial.png"
        render_game_state(state, initial_path)
        frame_entries.append(
            {
                "frame_index": 0,
                "step": 0,
                "action_type": "initial",
                "description": "Initial state",
                "path": initial_path,
                "event_labels": [],
                "metrics": _state_metrics(state),
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

            before_metrics = _state_metrics(state)
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
            after_metrics = _state_metrics(state)
            event_labels = _detect_event_labels(before_metrics, after_metrics)
            history_entry = _episode_history_entry(
                state=state,
                step=steps_executed,
                chosen_type=chosen_type,
                chosen_params=chosen_params,
                applied_action=action,
                applied=applied,
                message=f"{fallback_note}{message}".strip(),
                description=description,
                event_labels=event_labels,
            )
            if _should_render_frame(frame_mode, event_labels):
                frame_path = frames_dir / (
                    f"frame_{steps_executed:03d}_"
                    f"{_safe_name(action.action_type)}.png"
                )
                render_game_state(state, frame_path)
                history_entry["frame_index"] = len(frame_entries)
                frame_entries.append(
                    _frame_entry(
                        frame_index=len(frame_entries),
                        step=steps_executed,
                        action_type=action.action_type,
                        description=description,
                        path=frame_path,
                        event_labels=event_labels,
                        metrics=after_metrics,
                    )
                )
            action_history_entries.append(history_entry)
    except Exception as exc:
        episode_success = False
        error = f"{type(exc).__name__}: {exc}"

    if action_history_entries:
        last_history = action_history_entries[-1]
        final_label = "terminal" if is_terminal(state) else "final"
        if final_label not in last_history["event_labels"]:
            last_history["event_labels"].append(final_label)
        if last_history["frame_index"] is not None:
            frame_entries[last_history["frame_index"]]["event_labels"] = list(
                last_history["event_labels"]
            )

    if (
        frame_mode == "events"
        and action_history_entries
        and action_history_entries[-1]["frame_index"] is None
    ):
        final_history = action_history_entries[-1]
        final_labels = list(final_history["event_labels"])
        final_path = frames_dir / f"frame_{steps_executed:03d}_final.png"
        try:
            render_game_state(state, final_path)
            final_history["frame_index"] = len(frame_entries)
            frame_entries.append(
                _frame_entry(
                    frame_index=len(frame_entries),
                    step=steps_executed,
                    action_type=final_history["action_type"],
                    description=final_history["description"],
                    path=final_path,
                    event_labels=final_labels,
                    metrics=_state_metrics(state),
                )
            )
        except Exception as exc:
            episode_success = False
            error = error or f"{type(exc).__name__}: {exc}"

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
        frames_count=len(frame_entries),
        frame_mode=frame_mode,
    )
    _write_episode_log(
        run_dir / "episode_log.txt",
        summary,
        action_history_entries,
    )
    _write_summary(run_dir / "episode_summary.json", summary)
    _write_history(
        run_dir / "episode_history.json",
        action_history_entries,
    )
    _write_html_index(
        run_dir / "index.html",
        frame_entries,
        action_history_entries,
        summary,
        frame_duration_ms,
    )
    if make_gif and frame_entries:
        gif_path = _try_write_gif(
            [frame["path"] for frame in frame_entries],
            run_dir / "episode.gif",
            frame_duration_ms,
        )
        if gif_path is None:
            print("Warning: GIF generation was unavailable; PNG/HTML replay is complete.")

    return run_dir, summary


def _state_metrics(state) -> dict[str, Any]:
    return {
        "score": state.player.score,
        "final_score": state.final_score(),
        "money": state.player.money,
        "bonds": state.player.bonds,
        "deliveries": state.player.delivered_goods_count,
        "completed_routes": sum(
            route.completed for route in state.routes.values()
        ),
        "major_line_bonus": state.player.major_line_bonus,
        "rail_baron_bonus": state.player.rail_baron_bonus,
        "terminal": is_terminal(state),
    }


def _detect_event_labels(
    before: dict[str, Any],
    after: dict[str, Any],
) -> list[str]:
    labels: list[str] = []
    comparisons = (
        ("deliveries", "+delivery"),
        ("major_line_bonus", "+major line"),
        ("rail_baron_bonus", "+Rail Baron"),
        ("completed_routes", "+route completed"),
        ("bonds", "+bonds"),
    )
    for metric, label in comparisons:
        if int(after[metric]) > int(before[metric]):
            labels.append(label)
    if bool(after["terminal"]) and not bool(before["terminal"]):
        labels.append("terminal")
    return labels


def _should_render_frame(frame_mode: str, event_labels: list[str]) -> bool:
    if frame_mode == "all":
        return True
    render_events = {
        "+delivery",
        "+major line",
        "+Rail Baron",
        "+route completed",
        "terminal",
    }
    return bool(render_events.intersection(event_labels))


def _frame_entry(
    frame_index: int,
    step: int,
    action_type: str,
    description: str,
    path: Path,
    event_labels: list[str],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "frame_index": frame_index,
        "step": step,
        "action_type": action_type,
        "description": description,
        "path": path,
        "event_labels": list(event_labels),
        "metrics": dict(metrics),
    }


def _episode_history_entry(
    state,
    step: int,
    chosen_type: str,
    chosen_params: dict[str, Any],
    applied_action: Action,
    applied: bool,
    message: str,
    description: str,
    event_labels: list[str],
) -> dict[str, Any]:
    metrics = _state_metrics(state)
    entry = {
        "step": step,
        "turn": state.turn,
        "phase": state.phase,
        "actions_remaining": state.actions_remaining,
        "action_type": applied_action.action_type,
        "description": description,
        "applied": bool(applied),
        "event_labels": list(event_labels),
        "frame_index": None,
        "chosen_action_type": chosen_type,
        "chosen_action_params": chosen_params,
        "applied_action_type": applied_action.action_type,
        "applied_action_params": dict(applied_action.params),
        "apply_succeeded": bool(applied),
        "message": message,
    }
    entry.update(metrics)
    return entry


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
    frame_mode: str,
) -> dict[str, Any]:
    return {
        "map_name": map_name,
        "map_path": str(map_path),
        "agent_name": agent_name,
        "seed": seed,
        "max_steps": max_steps,
        "frame_mode": frame_mode,
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
        f"frame_mode={summary['frame_mode']}",
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
                f"  events={','.join(entry['event_labels']) or 'none'}",
                (
                    f"  score={entry['score']} money={entry['money']} "
                    f"bonds={entry['bonds']} major_line_bonus="
                    f"{entry['major_line_bonus']} rail_baron_bonus="
                    f"{entry['rail_baron_bonus']} deliveries="
                    f"{entry['deliveries']} completed_routes="
                    f"{entry['completed_routes']}"
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


def _write_history(path: Path, entries: list[dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(entries, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_html_index(
    path: Path,
    frames: list[dict[str, Any]],
    history_entries: list[dict[str, Any]],
    summary: dict[str, Any],
    frame_duration_ms: int,
) -> None:
    frame_data = [
        {
            "frameIndex": frame["frame_index"],
            "step": frame["step"],
            "actionType": frame["action_type"],
            "description": frame["description"],
            "image": f"frames/{frame['path'].name}",
            "eventLabels": frame["event_labels"],
            "metrics": frame["metrics"],
        }
        for frame in frames
    ]
    history_data = _viewer_history_data(frames, history_entries)
    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent episode replay</title>
  <style>
    :root { color-scheme: light; font-family: Inter, system-ui, sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; color: #202124; background: #eef1f5; }
    .page { max-width: 1500px; margin: 0 auto; padding: 18px; }
    .header, .final-summary {
      display: flex; flex-wrap: wrap; gap: 10px 22px; align-items: center;
      padding: 14px 18px; background: #fff; border: 1px solid #c9cfd8;
      border-radius: 10px; box-shadow: 0 2px 8px rgba(31, 42, 55, .08);
    }
    .header h1 { width: 100%; margin: 0 0 2px; font-size: 20px; }
    .metric { white-space: nowrap; font-size: 14px; }
    .layout {
      display: grid; grid-template-columns: minmax(0, 3fr) minmax(300px, 1fr);
      gap: 16px; margin-top: 16px; align-items: start;
    }
    .viewer, .history-panel {
      background: #fff; border: 1px solid #c9cfd8; border-radius: 10px;
      box-shadow: 0 2px 8px rgba(31, 42, 55, .08); overflow: hidden;
    }
    .image-wrap { min-height: 420px; display: grid; place-items: center; background: #f7f8fa; }
    #viewerImage { display: block; width: 100%; max-height: 76vh; object-fit: contain; }
    .controls {
      display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
      padding: 10px 14px; border-top: 1px solid #d8dde5;
    }
    button {
      border: 1px solid #9aa5b1; border-radius: 6px; padding: 7px 12px;
      background: #fff; color: #202124; cursor: pointer;
    }
    button:hover { background: #edf3fa; }
    .caption { flex: 1 1 320px; font-size: 13px; color: #4b5563; }
    .history-panel h2 { margin: 0; padding: 14px; font-size: 16px; border-bottom: 1px solid #d8dde5; }
    #historyList { max-height: 78vh; overflow-y: auto; padding: 8px; }
    .history-row {
      width: 100%; display: block; text-align: left; margin: 0 0 6px;
      padding: 9px 10px; border: 1px solid transparent; border-left: 3px solid #c7ccd3;
      background: #f8f9fb;
    }
    .history-row.rendered { border-left-color: #1f5a91; }
    .history-row.selected { border-color: #1f5a91; background: #e9f2fb; }
    .history-title { display: block; font-weight: 700; font-size: 12px; }
    .history-description { display: block; margin-top: 3px; font-size: 12px; color: #3f4854; }
    .history-metrics { display: block; margin-top: 4px; font-size: 11px; color: #66717e; }
    .badges { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 5px; }
    .badge { padding: 2px 5px; border-radius: 10px; background: #e6edf6; color: #274b70; font-size: 10px; }
    .final-summary { margin-top: 16px; }
    .final-summary strong { width: 100%; }
    @media (max-width: 900px) {
      .layout { grid-template-columns: 1fr; }
      #historyList { max-height: 360px; }
    }
  </style>
</head>
<body>
<main class="page">
  <header class="header">
    <h1>Automated Agent Episode Replay</h1>
    <span class="metric"><strong>Map:</strong> __MAP_NAME__</span>
    <span class="metric"><strong>Agent:</strong> __AGENT_NAME__</span>
    <span class="metric"><strong>Seed:</strong> __SEED__</span>
    <span class="metric"><strong>Frame mode:</strong> __FRAME_MODE__</span>
    <span class="metric"><strong>Steps:</strong> __STEPS__ / __MAX_STEPS__</span>
  </header>
  <section class="layout">
    <div class="viewer">
      <div class="image-wrap"><img id="viewerImage" alt="Agent replay frame"></div>
      <div class="controls">
        <button id="previousButton" type="button">Previous</button>
        <button id="playButton" type="button">Play</button>
        <button id="nextButton" type="button">Next</button>
        <span id="frameCounter" class="metric"></span>
        <span id="frameCaption" class="caption"></span>
      </div>
    </div>
    <aside class="history-panel">
      <h2>Action History</h2>
      <div id="historyList"></div>
    </aside>
  </section>
  <footer class="final-summary">
    <strong>Final Episode Summary</strong>
    <span class="metric">score __FINAL_SCORE__</span>
    <span class="metric">money $__MONEY__</span>
    <span class="metric">bonds __BONDS__</span>
    <span class="metric">deliveries __DELIVERIES__</span>
    <span class="metric">major bonus __MAJOR_BONUS__</span>
    <span class="metric">Rail Baron bonus __RAIL_BARON_BONUS__</span>
    <span class="metric">completed routes __COMPLETED_ROUTES__</span>
    <span class="metric">terminal __TERMINAL__</span>
    <span class="metric">success __SUCCESS__</span>
  </footer>
</main>
<script>
  const frameData = __FRAME_DATA__;
  const historyData = __HISTORY_DATA__;
  const playbackInterval = __FRAME_DURATION__;
  let currentFrameIndex = 0;
  let selectedHistoryIndex = 0;
  let playbackTimer = null;

  const viewerImage = document.getElementById("viewerImage");
  const frameCounter = document.getElementById("frameCounter");
  const frameCaption = document.getElementById("frameCaption");
  const historyList = document.getElementById("historyList");
  const playButton = document.getElementById("playButton");

  function eventBadges(labels) {
    return labels.map(label => `<span class="badge">${escapeText(label)}</span>`).join("");
  }

  function escapeText(value) {
    const element = document.createElement("span");
    element.textContent = String(value);
    return element.innerHTML;
  }

  function renderHistory() {
    historyList.innerHTML = "";
    historyData.forEach((entry, index) => {
      const row = document.createElement("button");
      row.type = "button";
      row.className = `history-row${entry.rendered ? " rendered" : ""}`;
      row.dataset.historyIndex = index;
      row.innerHTML = `
        <span class="history-title">${entry.step}. ${escapeText(entry.actionType)}</span>
        <span class="history-description">${escapeText(entry.description)}</span>
        <span class="history-metrics">score ${entry.metrics.final_score} · money $${entry.metrics.money} · bonds ${entry.metrics.bonds} · deliveries ${entry.metrics.deliveries} · routes ${entry.metrics.completed_routes} · ML ${entry.metrics.major_line_bonus} · RB ${entry.metrics.rail_baron_bonus}</span>
        <span class="badges">${eventBadges(entry.eventLabels)}</span>`;
      row.addEventListener("click", () => setFrame(entry.displayFrameIndex, index));
      historyList.appendChild(row);
    });
  }

  function setFrame(index, historyIndex = null) {
    if (!frameData.length) return;
    currentFrameIndex = Math.max(0, Math.min(index, frameData.length - 1));
    const frame = frameData[currentFrameIndex];
    viewerImage.src = frame.image;
    viewerImage.alt = `Step ${frame.step}: ${frame.description}`;
    frameCounter.textContent = `Frame ${currentFrameIndex + 1} / ${frameData.length}`;
    frameCaption.textContent = `Step ${frame.step}: ${frame.actionType} — ${frame.description}`;
    if (historyIndex === null) {
      const exact = historyData.findIndex(item => item.exactFrameIndex === currentFrameIndex);
      if (exact >= 0) selectedHistoryIndex = exact;
    } else {
      selectedHistoryIndex = historyIndex;
    }
    document.querySelectorAll(".history-row").forEach((row, rowIndex) => {
      row.classList.toggle("selected", rowIndex === selectedHistoryIndex);
    });
    const selected = historyList.children[selectedHistoryIndex];
    if (selected) selected.scrollIntoView({ block: "nearest" });
  }

  function stopPlayback() {
    if (playbackTimer !== null) window.clearInterval(playbackTimer);
    playbackTimer = null;
    playButton.textContent = "Play";
  }

  function togglePlayback() {
    if (playbackTimer !== null) {
      stopPlayback();
      return;
    }
    playButton.textContent = "Pause";
    playbackTimer = window.setInterval(() => {
      if (currentFrameIndex >= frameData.length - 1) {
        stopPlayback();
        return;
      }
      setFrame(currentFrameIndex + 1);
    }, playbackInterval);
  }

  document.getElementById("previousButton").addEventListener("click", () => {
    stopPlayback();
    setFrame(currentFrameIndex - 1);
  });
  document.getElementById("nextButton").addEventListener("click", () => {
    stopPlayback();
    setFrame(currentFrameIndex + 1);
  });
  playButton.addEventListener("click", togglePlayback);

  renderHistory();
  setFrame(0, 0);
</script>
</body>
</html>
"""
    replacements = {
        "__MAP_NAME__": escape(str(summary["map_name"])),
        "__AGENT_NAME__": escape(str(summary["agent_name"])),
        "__SEED__": str(summary["seed"]),
        "__FRAME_MODE__": escape(str(summary["frame_mode"])),
        "__STEPS__": str(summary["steps_executed"]),
        "__MAX_STEPS__": str(summary["max_steps"]),
        "__FINAL_SCORE__": str(summary["final_score"]),
        "__MONEY__": str(summary["money"]),
        "__BONDS__": str(summary["bonds"]),
        "__DELIVERIES__": str(summary["delivered_goods_count"]),
        "__MAJOR_BONUS__": str(summary["major_line_bonus"]),
        "__RAIL_BARON_BONUS__": str(summary["rail_baron_bonus"]),
        "__COMPLETED_ROUTES__": str(summary["completed_routes_count"]),
        "__TERMINAL__": str(summary["terminal"]).lower(),
        "__SUCCESS__": str(summary["success"]).lower(),
        "__FRAME_DATA__": _json_for_script(frame_data),
        "__HISTORY_DATA__": _json_for_script(history_data),
        "__FRAME_DURATION__": str(frame_duration_ms),
    }
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)
    path.write_text(html, encoding="utf-8")


def _viewer_history_data(
    frames: list[dict[str, Any]],
    history_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not frames:
        return []
    entries = [
        {
            "step": 0,
            "actionType": "initial",
            "description": "Initial state",
            "eventLabels": [],
            "metrics": frames[0]["metrics"],
            "rendered": True,
            "exactFrameIndex": 0,
            "displayFrameIndex": 0,
        }
    ]
    for entry in history_entries:
        exact_frame_index = entry["frame_index"]
        display_frame_index = (
            exact_frame_index
            if exact_frame_index is not None
            else _nearest_frame_index(frames, int(entry["step"]))
        )
        entries.append(
            {
                "step": entry["step"],
                "actionType": entry["action_type"],
                "description": entry["description"],
                "eventLabels": entry["event_labels"],
                "metrics": {
                    "final_score": entry["final_score"],
                    "money": entry["money"],
                    "bonds": entry["bonds"],
                    "deliveries": entry["deliveries"],
                    "completed_routes": entry["completed_routes"],
                    "major_line_bonus": entry["major_line_bonus"],
                    "rail_baron_bonus": entry["rail_baron_bonus"],
                },
                "rendered": exact_frame_index is not None,
                "exactFrameIndex": exact_frame_index,
                "displayFrameIndex": display_frame_index,
            }
        )
    return entries


def _nearest_frame_index(frames: list[dict[str, Any]], step: int) -> int:
    return min(
        range(len(frames)),
        key=lambda index: (abs(int(frames[index]["step"]) - step), index),
    )


def _json_for_script(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False)
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


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
        "episode_history.json",
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
        default="objective_aware_greedy",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-steps", type=int, default=60)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--make-gif", action="store_true")
    parser.add_argument("--frame-duration-ms", type=int, default=700)
    parser.add_argument("--frame-mode", choices=("all", "events"), default="all")
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
        frame_mode=args.frame_mode,
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
