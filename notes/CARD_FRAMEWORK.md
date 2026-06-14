# Minimal Card Framework

## Purpose

Phase 4 adds a small, original card framework so the simulator can move from a basic-rule prototype toward fuller-rule modelling. It is designed for dissertation experiments, not as a complete implementation of the official Railways of the World card system.

## Implemented Card Types

- `immediate_cash`: applies a cash effect when selected, then marks the card used.
- `delivery_objective`: tracks matching deliveries and awards bonus points when the required count is reached.
- `network_objective`: awards bonus points after the player connects two specified cities through built links.
- `end_game_scoring`: contributes final-score points from a final-state metric such as built railway links.

The basic test deck is stored in `data/cards_basic.json`. The card names and effects are simplified original data and do not copy official card text.

## Action Model

Selecting a card is a normal player action:

```text
select_operation_card(card_id)
```

Financing remains separate from the action model. Issuing bonds/share certificates is still handled internally by payment rules and is not a legal player action.

## Experiment Scope

Cards are disabled by default in `reset_game` unless a `card_path` is supplied. This keeps existing card-free experiments and the `micro_map` exact benchmark comparable. The Streamlit app enables the basic card deck for interactive demonstration.

Exact-search memoisation includes card state when cards are enabled: available cards, owned cards, card progress, completed cards, and awarded operation-card bonus.

## Current Limitations

- The framework does not implement the full official operation-card deck.
- Rail Baron / Tycoon cards are still future work.
- Official card timing, multiplayer interactions, and opponent-related effects are not modelled.
- Existing agents can choose card actions through the legal-action interface, but they are not yet card-aware.
