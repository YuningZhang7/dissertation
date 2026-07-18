from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.greedy_delivery_agent import GreedyDeliveryAgent
from agents.greedy_expansion_agent import GreedyExpansionAgent
from agents.objective_aware_greedy_agent import ObjectiveAwareGreedyAgent
from agents.presentation_lookahead_greedy_agent import PresentationLookaheadGreedyAgent
from agents.random_agent import RandomAgent


AGENT_CLASSES: dict[str, type[BaseAgent]] = {
    "random": RandomAgent,
    "greedy_delivery": GreedyDeliveryAgent,
    "greedy_expansion": GreedyExpansionAgent,
    "objective_aware_greedy": ObjectiveAwareGreedyAgent,
    "presentation_lookahead_greedy": PresentationLookaheadGreedyAgent,
}


def create_agent(name: str, seed: int | None = None) -> BaseAgent:
    if name not in AGENT_CLASSES:
        raise ValueError(f"Unknown agent: {name}")
    return AGENT_CLASSES[name](seed=seed)


def list_agent_names() -> list[str]:
    return list(AGENT_CLASSES)
