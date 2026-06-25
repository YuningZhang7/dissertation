from __future__ import annotations

import json
from pathlib import Path

from railways.models import OperationCard


def load_cards(path: str | Path) -> dict[str, OperationCard]:
    """Load simplified operation-card definitions from JSON."""
    card_path = Path(path)
    with card_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    cards: dict[str, OperationCard] = {}
    for card_data in data.get("cards", []):
        card = OperationCard(
            id=str(card_data["id"]),
            name=str(card_data["name"]),
            card_type=str(card_data["card_type"]),
            description=str(card_data.get("description", "")),
            condition=dict(card_data.get("condition", {})),
            reward=dict(card_data.get("reward", {})),
            effect=dict(card_data.get("effect", {})),
        )
        if card.id in cards:
            raise ValueError(f"Duplicate operation card id: {card.id}")
        cards[card.id] = card

    return cards
