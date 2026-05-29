from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from functools import lru_cache
from pathlib import Path

import arcade

from sv.core.config import Settings


class ItemKind(Enum):
    WEAPON = auto()
    ARMOR = auto()
    ACCESSORY = auto()
    CONSUMABLE = auto()
    MISC = auto()


class EquipmentSlot(Enum):
    WEAPON = auto()
    ARMOR = auto()
    ACCESSORY = auto()
    EXTRA = auto()

    @property
    def label(self) -> str:
        return {
            EquipmentSlot.WEAPON: "Оружие",
            EquipmentSlot.ARMOR: "Броня",
            EquipmentSlot.ACCESSORY: "Аксессуар",
            EquipmentSlot.EXTRA: "Слот",
        }[self]


@dataclass(frozen=True, slots=True)
class ItemDefinition:
    item_id: str
    name: str
    kind: ItemKind
    icon_index: int
    description: str
    max_stack: int = 1
    equip_slot: EquipmentSlot | None = None

    @property
    def kind_label(self) -> str:
        return {
            ItemKind.WEAPON: "Оружие",
            ItemKind.ARMOR: "Броня",
            ItemKind.ACCESSORY: "Аксессуар",
            ItemKind.CONSUMABLE: "Расходник",
            ItemKind.MISC: "Предмет",
        }[self.kind]

    @property
    def stackable(self) -> bool:
        return self.max_stack > 1

    @property
    def equippable(self) -> bool:
        return self.equip_slot is not None


@dataclass(slots=True)
class ItemStack:
    definition: ItemDefinition
    quantity: int = 1

    def __post_init__(self) -> None:
        self.quantity = max(1, int(self.quantity))
        self.quantity = min(self.quantity, self.definition.max_stack)

    @property
    def name(self) -> str:
        return self.definition.name


_ITEM_TEXTURE_SIZE = 16
_ITEM_SPRITESHEET_PATH = ":assets:/sprites/items.png"
_CHEST_TEXTURE_PATH = ":assets:/sprites/chest.png"
MAP_ITEM_SCALE = 2.0
TILE_SIZE = Settings.TILE_SIZE


@lru_cache(maxsize=1)
def load_item_textures() -> tuple[arcade.Texture, ...]:
    try:
        sheet = arcade.load_spritesheet(_ITEM_SPRITESHEET_PATH)
    except FileNotFoundError:
        fallback_path = Path(__file__).resolve().parents[3] / "assets" / "sprites" / "items.png"
        sheet = arcade.load_spritesheet(fallback_path)
    textures = sheet.get_texture_grid((_ITEM_TEXTURE_SIZE, _ITEM_TEXTURE_SIZE), columns=4, count=4)
    return tuple(textures)


@lru_cache(maxsize=1)
def load_chest_texture() -> arcade.Texture:
    try:
        return arcade.load_texture(_CHEST_TEXTURE_PATH)
    except FileNotFoundError:
        fallback_path = Path(__file__).resolve().parents[3] / "assets" / "sprites" / "chest.png"
        return arcade.load_texture(fallback_path)


class MapItem(arcade.Sprite):
    """Non-blocking item pickup placed on the tile grid."""

    def __init__(
        self,
        definition: ItemDefinition,
        tile_x: int,
        tile_y: int,
        *,
        quantity: int = 1,
    ) -> None:
        super().__init__(scale=MAP_ITEM_SCALE)
        self.definition = definition
        self.stack = ItemStack(definition, quantity)
        self.tile_x = int(tile_x)
        self.tile_y = int(tile_y)
        self.blocking = False
        self.texture = load_item_textures()[definition.icon_index]
        self.center_x = self.tile_x * TILE_SIZE + TILE_SIZE / 2
        self.center_y = self.tile_y * TILE_SIZE + TILE_SIZE / 2


class MapChest(arcade.Sprite):
    """Blocking chest with one loot stack."""

    def __init__(self, stack: ItemStack, tile_x: int, tile_y: int) -> None:
        super().__init__()
        self.stack = stack
        self.tile_x = int(tile_x)
        self.tile_y = int(tile_y)
        self.blocking = True
        self.texture = load_chest_texture()
        self.center_x = self.tile_x * TILE_SIZE + TILE_SIZE / 2
        self.center_y = self.tile_y * TILE_SIZE + TILE_SIZE / 2


DEFAULT_ITEM_DEFINITIONS: dict[str, ItemDefinition] = {
    "sword": ItemDefinition(
        item_id="sword",
        name="Меч",
        kind=ItemKind.WEAPON,
        icon_index=0,
        description="Стандартный клинок для ближнего боя.",
        equip_slot=EquipmentSlot.WEAPON,
    ),
    "armor": ItemDefinition(
        item_id="armor",
        name="Кольчуга",
        kind=ItemKind.ARMOR,
        icon_index=1,
        description="Лёгкая защита, рассчитанная на раннюю игру.",
        equip_slot=EquipmentSlot.ARMOR,
    ),
    "ring": ItemDefinition(
        item_id="ring",
        name="Кольцо",
        kind=ItemKind.ACCESSORY,
        icon_index=2,
        description="Простой аксессуар. Заглушка для будущих эффектов.",
        equip_slot=EquipmentSlot.ACCESSORY,
    ),
    "potion": ItemDefinition(
        item_id="potion",
        name="Зелье",
        kind=ItemKind.CONSUMABLE,
        icon_index=3,
        description="Заглушка расходника. Пока ничего не делает.",
        max_stack=5,
    ),
}
