# Rules Coverage

## Implemented Rules

- Visual railway map using a graph of cities and links.
- Cities with demand colors, goods, urbanized status, gray-city support, and empty city markers.
- Railway links with fixed build costs, built status, and single-player ownership.
- Single-player turn structure with an action phase and income phase.
- Configurable actions per turn.
- Track construction as one city-to-city edge per action.
- Optional connected track-building restriction. With `require_connected_track_building = true`, the first track may start anywhere, then later track must touch the player's existing network.
- Goods delivery over built links only.
- Explicit route-based delivery actions with a selected `path` field.
- Locomotive level limiting delivery path length.
- Delivery scoring based on path length.
- Rule preventing a delivery from skipping an intermediate city that demands the delivered good color.
- Voluntary bonds, configurable bond value, and configurable final bond penalty.
- Bond interest during income phase.
- Score-based income using a configurable income table.
- Engine upgrades using configurable level-by-level costs.
- Empty city markers when a city loses its last good.
- Fixed-turn end condition.
- Empty-city-marker end condition with optional extra turn after the trigger.
- Simplified urbanize action for gray or non-urbanized cities.
- Major-line data loading, connection-based claiming, one-time bonus scoring, and action-history logging.
- AI-ready environment functions: reset, legal actions, apply action, copy state, terminal check, final score.

## Simplified Rules

- Each city-to-city link is modelled as one edge, not individual track tiles.
- Track costs are fixed edge costs rather than detailed terrain, track tile, river, or mountain costs.
- Connected track building checks only whether a candidate edge touches the player's existing graph; it does not yet enforce tile placement or terrain constraints.
- All built links are owned by the single player.
- Delivery route selection uses explicit simple graph paths, but does not yet model opponent track fees or complex official route constraints.
- Income uses a small configurable score table rather than the full official income chart.
- Bond interest is simplified to a fixed amount per bond.
- Urbanize uses a simple cost, demand color, and random new goods.
- Major lines are represented as source-target connection bonuses rather than full official route cards.
- The map is a toy map rather than an official board map.
- End condition can be set to `fixed_turns` or `empty_city_markers`.

## Not Yet Implemented

- Full official action phase details.
- First-player auction and turn-order bidding.
- Full urbanize deck/city rules.
- Full empty city marker rules from each official map.
- Full income and dividend rules.
- Full bond and share/economic model.
- Major Lines with official route requirements and map-specific bonuses.
- Rail Baron cards.
- Railroad Operations Cards.
- Full terrain-based track building.
- Track tile placement and tile limits.
- Official map-specific rules.
- Official Eastern U.S. map data.
- Opponent-owned track scoring.

## Intentionally Excluded for Single-Player Version

- Player-vs-player competition.
- First player auction.
- Turn order bidding.
- Competition for goods.
- Multiplayer blocking and route competition.
- Opponent-owned track scoring.
- Leader-follower model.

## Next Rule-Fidelity Checklist

1. Decide whether each turn should always have exactly three actions or allow a formal end-turn/pass phase.
2. Add official-style route choice details such as opponent track payments if multiplayer is ever reintroduced.
3. Add terrain and tile-level build costs.
4. Improve urbanize rules and goods generation.
5. Calibrate income and bond rules against the selected official map/ruleset.
6. Add operation card data structures and a minimal card effect engine.
7. Expand major-line validation to match official card/map requirements.
8. Add a richer map once the toy engine is stable.
9. Add automated test coverage for edge cases before implementing advanced AI.
