# Meeting 1 Summary

The dissertation direction is to build a local, visual, single-player simulator for a simplified version of Railways of the World.

The first milestone focuses on the visual game environment and core rule logic rather than advanced AI. The simulator should later support heuristic search, reinforcement learning, genetic algorithms, Monte Carlo Tree Search, or other optimisation approaches.

Initial implementation priorities:

- Build a small toy map.
- Represent the game as a graph.
- Implement track building, goods delivery, bonds, locomotive upgrades, and turn progression.
- Provide a local Streamlit interface.
- Keep rule logic modular so agents can call it directly.
