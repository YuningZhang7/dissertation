from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Action:
    action_type: str
    params: dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.action_type, _hashable_value(self.params)))

    @classmethod
    def build_track_segments(cls, segment_ids: list[str]) -> "Action":
        return cls("build_track_segments", {"segment_ids": list(segment_ids)})

    @classmethod
    def deliver_good(
        cls,
        source: str,
        target: str,
        good_color: str,
        path: list[str] | None = None,
    ) -> "Action":
        params: dict[str, Any] = {
            "source": source,
            "target": target,
            "good_color": good_color,
        }
        if path is not None:
            params["path"] = path
        return cls("deliver_good", params)

    @classmethod
    def upgrade_engine(cls) -> "Action":
        return cls("upgrade_engine")

    @classmethod
    def urbanize(cls, city_id: str, demand_color: str | None = None) -> "Action":
        return cls("urbanize", {"city_id": city_id, "demand_color": demand_color})

    @classmethod
    def select_operation_card(cls, card_id: str) -> "Action":
        return cls("select_operation_card", {"card_id": card_id})

    @classmethod
    def pass_action(cls) -> "Action":
        return cls("pass")

    @classmethod
    def next_turn(cls) -> "Action":
        return cls("next_turn")


def _hashable_value(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple(
            (key, _hashable_value(item))
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        )
    if isinstance(value, list | tuple):
        return tuple(_hashable_value(item) for item in value)
    if isinstance(value, set):
        return tuple(sorted(_hashable_value(item) for item in value))
    return value
