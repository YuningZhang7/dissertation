from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.greedy_delivery_agent import GreedyDeliveryAgent
from agents.greedy_expansion_agent import GreedyExpansionAgent
from agents.mcts_agent import MCTSAgent
from agents.random_agent import RandomAgent


AGENT_CLASSES: dict[str, type[BaseAgent]] = {
    "random": RandomAgent,
    "greedy_delivery": GreedyDeliveryAgent,
    "greedy_expansion": GreedyExpansionAgent,
    "mcts": MCTSAgent,
}


def create_agent(name: str, seed: int | None = None) -> BaseAgent:
    if name not in AGENT_CLASSES:
        raise ValueError(f"Unknown agent: {name}")
    return AGENT_CLASSES[name](seed=seed)


def list_agent_names() -> list[str]:
    return list(AGENT_CLASSES)
