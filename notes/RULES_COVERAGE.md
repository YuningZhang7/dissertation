# Rules Coverage

## Implemented Rules

- Visual railway map using a graph of cities and links.
- Cities with demand colors, goods, urbanized status, gray-city support, and empty city markers.
- Railway links with fixed build costs, built status, and single-player ownership.
- Single-player turn structure with an action phase and income phase.
- Configurable actions per turn.
- Track construction as one city-to-city edge per action.
- Goods delivery over built links only.
- Locomotive level limiting delivery path length.
- Delivery scoring based on path length.
- Rule preventing a delivery from skipping an intermediate city that demands the delivered good color.
- Voluntary bonds, configurable bond value, and configurable final bond penalty.
- Bond interest during income phase.
- Score-based income using a configurable income table.
- Engine upgrades using configurable level-by-level costs.
- Empty city markers when a city loses its last good.
- Fixed-turn end condition and scaffolded empty-city-marker end condition.
- Simplified urbanize action for gray or non-urbanized cities.
- Basic major-line placeholder support.
- AI-ready environment functions: reset, legal actions, apply action, copy state, terminal check, final score.

## Simplified Rules

- Each city-to-city link is modelled as one edge, not individual track tiles.
- Track costs are fixed edge costs rather than detailed terrain, track tile, river, or mountain costs.
- Any unbuilt affordable edge can currently be built; connection restrictions are left as a TODO.
- All built links are owned by the single player.
- Delivery uses the shortest built path rather than explicit route selection.
- Income uses a small configurable score table rather than the full official income chart.
- Bond interest is simplified to a fixed amount per bond.
- Urbanize uses a simple cost, demand color, and random new goods.
- Major lines are represented only as source-target bonus placeholders.
- The map is a toy map rather than an official board map.
- End condition defaults to fixed turns, with empty-city-marker logic scaffolded.

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
2. Replace shortest-path delivery with explicit legal route selection.
3. Add connection restrictions for track building.
4. Improve urbanize rules and goods generation.
5. Calibrate income and bond rules against the selected official map/ruleset.
6. Add operation card data structures and a minimal card effect engine.
7. Expand major-line validation and scoring.
8. Add a richer map once the toy engine is stable.
9. Add automated test coverage for edge cases before implementing advanced AI.
