from __future__ import annotations

from dataclasses import dataclass, field
import math

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
from railways.rules import describe_action


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

    def expand(self, rng) -> MCTSNode:
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
            untried_actions=get_legal_actions(child_state),
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
    ) -> None:
        super().__init__(seed=seed)
        self.iterations = iterations
        self.exploration_constant = exploration_constant
        self.rollout_depth_limit = rollout_depth_limit
        self.rollout_policy = rollout_policy

    def choose_action(self, state: GameState) -> Action:
        legal_actions = get_legal_actions(state)
        if not legal_actions:
            return Action.pass_action()
        if len(legal_actions) == 1:
            return legal_actions[0]

        root_state = copy_state(state)
        root = MCTSNode(
            state=root_state,
            untried_actions=get_legal_actions(root_state),
        )

        for _ in range(max(1, self.iterations)):
            node = self._select(root)
            if not is_terminal(node.state) and node.untried_actions:
                node = node.expand(self.rng)
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
        return best_node.action or Action.pass_action()

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

            legal_actions = get_legal_actions(state)
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

            fallback_actions = get_legal_actions(state)
            if not fallback_actions:
                break
            _, fallback_success, _ = apply_action(
                state,
                self.rng.choice(fallback_actions),
            )
            if not fallback_success:
                break

        return float(final_score(state))

    @staticmethod
    def _backpropagate(node: MCTSNode | None, reward: float) -> None:
        while node is not None:
            node.update(reward)
            node = node.parent


def _action_key(action: Action | None) -> str:
    return describe_action(action)
