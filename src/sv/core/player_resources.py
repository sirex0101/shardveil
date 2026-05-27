from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PLAYER_ACTION_LIGHT_COST = 1
PLAYER_WAIT_LIGHT_RECOVERY = 2
DEPTH_LIGHT_RECOVERY = 3
DEFAULT_CAMERA_ZOOM = 2.0


@dataclass(frozen=True)
class PlayerCarryover:
    inventory: Any = None
    hp: int | None = None
    light: int | None = None
    zoom: float = DEFAULT_CAMERA_ZOOM

    @classmethod
    def capture(cls, player, camera_controller, *, keep_player: bool) -> "PlayerCarryover":
        if not keep_player or player is None:
            return cls()
        zoom = (
            camera_controller.zoom
            if camera_controller is not None
            else DEFAULT_CAMERA_ZOOM
        )
        return cls(
            inventory=getattr(player, "inventory", None),
            hp=getattr(player, "hp", None),
            light=getattr(player, "light", None),
            zoom=zoom,
        )


def next_depth(current_depth: int, *, keep_player: bool) -> int:
    return int(current_depth) + 1 if keep_player else 1


def apply_player_carryover(player, carryover: PlayerCarryover | None) -> None:
    if player is None or carryover is None:
        return
    if carryover.inventory is not None:
        player.inventory = carryover.inventory
    if carryover.hp is not None:
        player.hp = max(1, min(player.max_hp, int(carryover.hp)))
    if carryover.light is not None:
        player.light = max(0, min(player.light_max, int(carryover.light)))


def player_light_ratio(player) -> float:
    if not player:
        return 0.0
    try:
        return player.light_ratio()
    except Exception:
        return 0.0


def recover_player_light(player, amount: int) -> int:
    if not player:
        return 0
    try:
        return player.recover_light(amount)
    except Exception:
        return 0


def consume_player_light(player, amount: int = PLAYER_ACTION_LIGHT_COST) -> int:
    if not player:
        return 0
    try:
        return player.spend_light(amount)
    except Exception:
        return 0
