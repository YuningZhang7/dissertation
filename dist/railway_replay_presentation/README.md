# Railway Agent Replay Interface

This package is a focused macOS-ready presentation build of the single-player
railway simulator. It includes the simulator source, selected interpretable agents,
the recommended `objective_aware_greedy` agent, two route-segment maps, a Streamlit
replay interface, and a static HTML replay generator.

The simulator is an official-compatible single-player abstraction. It focuses on
route-segment construction, route completion, completed-route delivery, Major Line
scoring, Rail Baron objectives, bonds, and final-score calculation. It does not
claim to reproduce every official multiplayer rule.

This presentation runtime is route-segment-only. Construction uses
`build_track_segments`, deliveries require completed routes, and Major Line and
Rail Baron connectivity is evaluated on the completed-route network.

Bonds are not selectable actions. Financing certificates are issued automatically
only when a payment shortfall occurs, and they continue to affect interest and the
final score.

## Quick start on macOS

1. Copy or unzip this directory onto the Mac.
2. In Finder, Control-click `launch_replay_interface.command` and choose **Open**.
3. macOS may ask for permission the first time. The launcher creates a local
   `.venv`, installs the listed Python dependencies, and opens Streamlit.

Python 3.10 or newer is recommended. From Terminal, the equivalent command is:

```bash
chmod +x launch_replay_interface.command generate_static_replay.command
./launch_replay_interface.command
```

The interface defaults to:

- map: `official_like`
- agent: `objective_aware_greedy`
- frame mode: `events`
- seed: `42`
- maximum steps: `60`

The Agent dropdown directly provides the four presentation agents: `random`,
`greedy_delivery`, `greedy_expansion`, and `objective_aware_greedy`.

## Static replay backup

Double-click `generate_static_replay.command`, or run:

```bash
./generate_static_replay.command
```

The command generates PNG frames, `index.html`, `episode_log.txt`,
`episode_summary.json`, and `episode_history.json` under
`outputs/agent_animations/`. Open the generated `index.html` in any browser.

For custom settings:

```bash
.venv/bin/python replay/animate_agent_episode.py   --map expanded_official_style   --agent objective_aware_greedy   --seed 42   --max-steps 60   --frame-mode events
```

## Included source

- `railways/`: simulator rules, state, scoring, loaders, and rendering
- `agents/`: selected presentation agents and their registry
- `replay/`: Streamlit interface and static replay generator
- `data/`: the two presentation maps, cards, and single-player configuration

Development benchmarks, experiment tables, smoke tests, generated research
outputs, exact-solver utilities, and non-presentation agent variants are not part
of this package. They remain available in the full research repository.
