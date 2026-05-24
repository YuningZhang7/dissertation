from __future__ import annotations

from railways.models import GameConfig, PlayerState


def compute_delivery_score(path_length: int, config: GameConfig) -> int:
    return max(config.minimum_delivery_score, path_length)


def compute_final_score(player_state: PlayerState, config: GameConfig) -> int:
    return player_state.score - player_state.bonds * config.bond_penalty
