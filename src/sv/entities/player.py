from __future__ import annotations

from sv.entities.base import Entity
from sv.items import create_default_inventory


class Player(Entity):
    """Player-controlled entity."""

    def __init__(self, tile_x: int, tile_y: int) -> None:
        texture = ":assets:/sprites/player.png"
        super().__init__(texture, tile_x, tile_y, hp=10, blocking=True)
        self.light_max = 10
        self.light = 10
        self.inventory = create_default_inventory()

    def spend_light(self, amount: int = 1) -> int:
        amount = max(0, int(amount))
        if amount == 0:
            return 0
        spent = min(self.light, amount)
        self.light -= spent
        return spent

    def recover_light(self, amount: int = 1) -> int:
        amount = max(0, int(amount))
        if amount == 0:
            return 0
        before = self.light
        self.light = min(self.light_max, self.light + amount)
        return self.light - before

    def light_ratio(self) -> float:
        if self.light_max <= 0:
            return 0.0
        return max(0.0, min(1.0, self.light / self.light_max))
