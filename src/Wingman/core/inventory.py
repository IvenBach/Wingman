from dataclasses import dataclass
from Wingman.core.item import Item

@dataclass
class EquippedGear:
    Head: Item | None
    Jewel1: Item | None
    Jewel2: Item | None
    Cloak: Item | None
    Body: Item | None
    Hands: Item  | None
    Legs: Item | None
    Feet: Item | None
    Held_Right: Item | None
    Held_Left: Item | None

    def __init__(self, 
                 Head: Item | None = None,
                 Jewel1: Item | None = None,
                 Jewel2: Item | None = None,
                 Cloak: Item | None = None,
                 Body: Item | None = None,
                 Hands: Item  | None = None,
                 Legs: Item | None = None,
                 Feet: Item | None = None,
                 Held_Right: Item | None = None,
                 Held_Left: Item | None = None):
        self.Head = Head
        self.Jewel1 = Jewel1
        self.Jewel2 = Jewel2
        self.Cloak = Cloak
        self.Body = Body
        self.Hands = Hands
        self.Legs = Legs
        self.Feet = Feet
        self.Held_Right = Held_Right
        self.Held_Left = Held_Left

@dataclass
class Inventory:
    EquippedGear_: EquippedGear
    Backpack: list[Item]
