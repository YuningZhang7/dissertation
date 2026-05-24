from __future__ import annotations

from typing import TYPE_CHECKING

from railways.models import GameConfig

if TYPE_CHECKING:
    from railways.game_state import GameState


def compute_delivery_score(path_length: int, config: GameConfig) -> int:
    if config.delivery_score_mode == "path_length":
        return max(config.minimum_delivery_score, path_length)
    if config.delivery_score_mode == "flat":
        return config.minimum_delivery_score
    raise ValueError(f"Unsupported delivery_score_mode: {config.delivery_score_mode}")


def compute_income(state: GameState) -> int:
    if state.config.income_mode != "score_based":
        return 0

    table = {
        int(score): income for score, income in state.config.income_table.items()
    }
    if not table:
        return state.player.score

    eligible_scores = [score for score in table if score <= state.player.score]
    if not eligible_scores:
        return table[min(table)]

    return table[max(eligible_scores)]


def compute_final_score(state: GameState) -> int:
    return (
        state.player.score
        - state.player.bonds * state.config.bond_final_penalty
        + state.player.major_line_bonus
        + state.player.rail_baron_bonus
        + state.player.operation_card_bonus
    )
