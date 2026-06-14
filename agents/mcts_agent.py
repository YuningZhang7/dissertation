from __future__ import annotations

from dataclasses import dataclass, field
import math

import networkx as nx

from agents.base_agent import BaseAgent
from agents.greedy_delivery_agent import GreedyDeliveryAgent
from railways.actions import Action
from railways.environment import (
    apply_action,
    copy_state,
    final_score,
    get_legal_actions,
    is_terminal,
)
from railways.game_state import GameState
from railways.rules import (
    describe_action,
    get_built_graph,
    get_legal_build_actions,
    get_legal_upgrade_action,
    get_legal_urbanize_actions,
    path_length,
    validate_delivery_path,
)
from railways.scoring import compute_delivery_score


@dataclass
class MCTSNode:
    state: GameState
    parent: MCTSNode | None = None
    action: Action | None = None
    children: list[MCTSNode] = field(default_factory=list)
    untried_actions: list[Action] = field(default_factory=list)
    visits: int = 0
    total_reward: float = 0.0

    def is_fully_expanded(self) -> bool:
        return not self.untried_actions

    def best_child(self, exploration_constant: float = 1.414) -> MCTSNode:
        if not self.children:
            raise ValueError("Cannot select a best child from a leaf node.")

        parent_visits = max(1, self.visits)

        def score(child: MCTSNode) -> tuple[float, str]:
            if child.visits == 0:
                return (float("inf"), _action_key(child.action))
            average_reward = child.total_reward / child.visits
            exploration = exploration_constant * math.sqrt(
                math.log(parent_visits) / child.visits
            )
            return (average_reward + exploration, _action_key(child.action))

        return max(self.children, key=score)

    def expand(self, rng, action_provider) -> MCTSNode:
        if not self.untried_actions:
            raise ValueError("Cannot expand a fully expanded node.")

        action_index = rng.randrange(len(self.untried_actions))
        action = self.untried_actions.pop(action_index)
        child_state = copy_state(self.state)
        _, success, _ = apply_action(child_state, action)

        if not success:
            fallback = Action.pass_action()
            _, fallback_success, _ = apply_action(child_state, fallback)
            if fallback_success:
                action = fallback

        child = MCTSNode(
            state=child_state,
            parent=self,
            action=action,
            untried_actions=action_provider(child_state),
        )
        self.children.append(child)
        return child

    def update(self, reward: float) -> None:
        self.visits += 1
        self.total_reward += reward


class MCTSAgent(BaseAgent):
    name = "mcts"

    def __init__(
        self,
        seed: int | None = None,
        iterations: int = 100,
        exploration_constant: float = 1.414,
        rollout_depth_limit: int = 80,
        rollout_policy: str = "random",
        action_generation: str = "fast",
        max_candidate_actions: int = 24,
        evaluation_mode: str = "final_score",
        major_line_weight: float = 1.0,
        delivery_weight: float = 0.2,
        network_weight: float = 0.1,
    ) -> None:
        super().__init__(seed=seed)
        self.iterations = iterations
        self.exploration_constant = exploration_constant
        self.rollout_depth_limit = rollout_depth_limit
        self.rollout_policy = rollout_policy
        self.action_generation = action_generation
        self.max_candidate_actions = max_candidate_actions
        self.evaluation_mode = evaluation_mode
        self.major_line_weight = major_line_weight
        self.delivery_weight = delivery_weight
        self.network_weight = network_weight

    def choose_action(self, state: GameState) -> Action:
        full_legal_actions = get_legal_actions(state)
        if not full_legal_actions:
            return Action.pass_action()
        if len(full_legal_actions) == 1:
            return full_legal_actions[0]

        legal_actions = self._get_candidate_actions(state) or full_legal_actions

        root_state = copy_state(state)
        root_actions = self._get_candidate_actions(root_state) or get_legal_actions(root_state)
        root = MCTSNode(
            state=root_state,
            untried_actions=root_actions,
        )

        for _ in range(max(1, self.iterations)):
            node = self._select(root)
            if not is_terminal(node.state) and node.untried_actions:
                node = node.expand(self.rng, self._get_candidate_actions)
            reward = self._rollout(copy_state(node.state))
            self._backpropagate(node, reward)

        if not root.children:
            return self.rng.choice(legal_actions)

        best_node = max(
            root.children,
            key=lambda child: (
                child.visits,
                child.total_reward / child.visits if child.visits else float("-inf"),
                _action_key(child.action),
            ),
        )
        selected = best_node.action or Action.pass_action()
        if selected not in full_legal_actions:
            fallback_actions = [
                action for action in legal_actions if action in full_legal_actions
            ]
            return self.rng.choice(fallback_actions or full_legal_actions)
        return selected

    def _select(self, node: MCTSNode) -> MCTSNode:
        while (
            not is_terminal(node.state)
            and node.is_fully_expanded()
            and node.children
        ):
            node = node.best_child(self.exploration_constant)
        return node

    def _rollout(self, state: GameState) -> float:
        greedy_agent: GreedyDeliveryAgent | None = None
        if self.rollout_policy == "greedy_delivery":
            greedy_agent = GreedyDeliveryAgent(seed=self.rng.randrange(2**31))

        for _ in range(max(0, self.rollout_depth_limit)):
            if is_terminal(state):
                break

            legal_actions = self._get_candidate_actions(state)
            if not legal_actions:
                break

            if greedy_agent is not None:
                action = greedy_agent.choose_action(state)
                if action not in legal_actions:
                    action = self.rng.choice(legal_actions)
            else:
                action = self.rng.choice(legal_actions)

            _, success, _ = apply_action(state, action)
            if success:
                continue

            fallback_actions = self._get_candidate_actions(state)
            if not fallback_actions:
                break
            _, fallback_success, _ = apply_action(
                state,
                self.rng.choice(fallback_actions),
            )
            if not fallback_success:
                break

        return self._evaluate_state(state)

    def _get_candidate_actions(self, state: GameState) -> list[Action]:
        if self.action_generation == "full":
            return get_legal_actions(state)

        if is_terminal(state):
            return []

        delivery_actions = _fast_delivery_actions(state)
        build_actions = sorted(
            get_legal_build_actions(state),
            key=lambda action: (
                state.edges[action.params["edge_id"]].cost,
                str(action.params["edge_id"]),
            ),
        )

        actions: list[Action] = []
        actions.extend(delivery_actions[:8])
        actions.extend(build_actions[:8])

        upgrade_action = get_legal_upgrade_action(state)
        if upgrade_action is not None:
            actions.append(upgrade_action)

        actions.extend(
            sorted(
                get_legal_urbanize_actions(state),
                key=lambda action: str(action.params.get("city_id", "")),
            )[:4]
        )

        actions.append(Action.pass_action())
        actions.append(Action.next_turn())
        return actions[: self.max_candidate_actions]

    @staticmethod
    def _backpropagate(node: MCTSNode | None, reward: float) -> None:
        while node is not None:
            node.update(reward)
            node = node.parent

    def _evaluate_state(self, state: GameState) -> float:
        if self.evaluation_mode == "final_score":
            return float(final_score(state))
        if self.evaluation_mode != "major_line_aware":
            raise ValueError(f"Unknown MCTS evaluation mode: {self.evaluation_mode}")

        return (
            float(final_score(state))
            + self.major_line_weight * estimate_major_line_progress(state)
            + self.delivery_weight * len(_fast_delivery_actions(state))
            + self.network_weight * len(state.player.built_edges)
        )


def _action_key(action: Action | None) -> str:
    return describe_action(action)


def _fast_delivery_actions(state: GameState) -> list[Action]:
    deliveries: list[Action] = []
    graph = get_built_graph(state)

    for source_city in sorted(state.cities.values(), key=lambda city: city.id):
        for good_color in sorted(set(source_city.goods)):
            for target_city in sorted(state.cities.values(), key=lambda city: city.id):
                if source_city.id == target_city.id:
                    continue
                if target_city.demand_color != good_color:
                    continue
                if source_city.id not in graph or target_city.id not in graph:
                    continue

                try:
                    route = nx.shortest_path(graph, source_city.id, target_city.id)
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue

                if path_length(route) > state.player.locomotive_level:
                    continue

                valid, _ = validate_delivery_path(
                    state,
                    route,
                    source_city.id,
                    target_city.id,
                    good_color,
                )
                if not valid:
                    continue

                length = path_length(route)
                deliveries.append(
                    Action(
                        "deliver_good",
                        {
                            "source": source_city.id,
                            "target": target_city.id,
                            "good_color": good_color,
                            "path": route,
                            "path_length": length,
                            "score": compute_delivery_score(length, state.config),
                        },
                    )
                )

    return sorted(
        deliveries,
        key=lambda action: (
            -int(action.params.get("score", 0)),
            int(action.params.get("path_length", 0)),
            str(action.params.get("source", "")),
            str(action.params.get("target", "")),
            "-".join(action.params.get("path", [])),
        ),
    )


def estimate_major_line_progress(state: GameState) -> float:
    """Estimate unclaimed major-line progress without mutating game state."""
    if not state.major_lines:
        return 0.0

    built_segments = {
        frozenset((edge.source, edge.target))
        for edge in state.edges.values()
        if edge.built
    }

    all_graph = nx.Graph()
    for city_id in state.cities:
        all_graph.add_node(city_id)
    for edge in state.edges.values():
        all_graph.add_edge(edge.source, edge.target, edge_id=edge.id)

    built_graph = get_built_graph(state)
    progress = 0.0

    for major_line in state.major_lines.values():
        if major_line.claimed:
            continue

        try:
            if nx.has_path(built_graph, major_line.source, major_line.target):
                progress += major_line.bonus_points
                continue
        except (nx.NetworkXError, nx.NodeNotFound):
            pass

        try:
            path = nx.shortest_path(
                all_graph,
                source=major_line.source,
                target=major_line.target,
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue

        length = path_length(path)
        if length <= 0:
            continue

        built_on_path = sum(
            1
            for first, second in zip(path, path[1:])
            if frozenset((first, second)) in built_segments
        )
        progress += major_line.bonus_points * (built_on_path / length)

    return progress
