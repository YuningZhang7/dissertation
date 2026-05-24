from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Action:
    action_type: str
    params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def build_track(cls, edge_id: str) -> "Action":
        return cls("build_track", {"edge_id": edge_id})

    @classmethod
    def deliver_good(
        cls,
        source: str,
        target: str,
        good_color: str,
    ) -> "Action":
        return cls(
            "deliver_good",
            {"source": source, "target": target, "good_color": good_color},
        )

    @classmethod
    def upgrade_engine(cls) -> "Action":
        return cls("upgrade_engine")

    @classmethod
    def urbanize(cls, city_id: str, demand_color: str | None = None) -> "Action":
        return cls("urbanize", {"city_id": city_id, "demand_color": demand_color})

    @classmethod
    def issue_bond(cls) -> "Action":
        return cls("issue_bond")

    @classmethod
    def select_operation_card(cls) -> "Action":
        return cls("select_operation_card")

    @classmethod
    def pass_action(cls) -> "Action":
        return cls("pass")

    @classmethod
    def next_turn(cls) -> "Action":
        return cls("next_turn")
