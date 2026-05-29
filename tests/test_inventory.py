import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sv.items import DEFAULT_ITEM_DEFINITIONS, Inventory, ItemStack


class InventoryTests(unittest.TestCase):
    def test_add_stack_places_item_in_empty_storage_cell(self):
        inventory = Inventory()
        stack = ItemStack(DEFAULT_ITEM_DEFINITIONS["sword"])

        result = inventory.add_stack(stack)

        self.assertTrue(result.added)
        self.assertEqual(result.quantity_added, 1)
        self.assertIs(inventory.storage[0].definition, stack.definition)

    def test_add_stack_merges_stackable_items(self):
        inventory = Inventory()
        potion = DEFAULT_ITEM_DEFINITIONS["potion"]
        inventory.storage[0] = ItemStack(potion, 3)

        result = inventory.add_stack(ItemStack(potion, 2))

        self.assertTrue(result.added)
        self.assertEqual(result.quantity_added, 2)
        self.assertEqual(inventory.storage[0].quantity, 5)

    def test_add_stack_reports_full_inventory(self):
        inventory = Inventory()
        sword = DEFAULT_ITEM_DEFINITIONS["sword"]
        inventory.storage = [ItemStack(sword) for _ in inventory.storage]

        result = inventory.add_stack(ItemStack(DEFAULT_ITEM_DEFINITIONS["armor"]))

        self.assertFalse(result.added)
        self.assertEqual(result.reason, "Инвентарь заполнен.")


if __name__ == "__main__":
    unittest.main()
