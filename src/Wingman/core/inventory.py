from Wingman.core.item import Item
from Wingman.core.equipment import Equipment

class Inventory:
    def __init__(self, equippedGear: Equipment, backpack: list[Item]):
        self.EquippedGear_ = equippedGear
        self.Backpack = backpack

    def __eq__(self, other):
        if not isinstance(other, Inventory):
            return False

        return self.EquippedGear_ == other.EquippedGear_ and self.Backpack == other.Backpack
