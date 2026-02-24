from dataclasses import dataclass
from Wingman.core.item import Item

@dataclass
class EquippedGear:
    def __init__(self, 
                 head: Item | None = None,
                 jewel1: Item | None = None,
                 jewel2: Item | None = None,
                 cloak: Item | None = None,
                 body: Item | None = None,
                 hands: Item  | None = None,
                 legs: Item | None = None,
                 feet: Item | None = None,
                 held_right: Item | None = None,
                 held_left: Item | None = None):
        self.Head = head
        self.Jewel1 = jewel1
        self.Jewel2 = jewel2
        self.Cloak = cloak
        self.Body = body
        self.Hands = hands
        self.Legs = legs
        self.Feet = feet
        self.Held_Right = held_right
        self.Held_Left = held_left

class Inventory:
    def __init__(self, equippedGear: EquippedGear, backpack: list[Item]):
        self.EquippedGear_ = equippedGear
        self.Backpack = backpack

    def __eq__(self, other):
        if not isinstance(other, Inventory):
            return False

        return self.EquippedGear_ == other.EquippedGear_ and self.Backpack == other.Backpack
