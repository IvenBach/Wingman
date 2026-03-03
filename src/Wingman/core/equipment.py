from dataclasses import dataclass
from Wingman.core.item import Item

@dataclass
class Equipment:
    @staticmethod
    def IsEmpty(equippedGear: 'Equipment') -> bool:
        return all(item is None for item in equippedGear.__dict__.values())

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

    def __eq__(self, other):
        if not isinstance(other, Equipment):
            return False

        return (self.Head == other.Head
                and self.Jewel1 == other.Jewel1
                and self.Jewel2 == other.Jewel2
                and self.Cloak == other.Cloak
                and self.Body == other.Body
                and self.Hands == other.Hands
                and self.Legs == other.Legs
                and self.Feet == other.Feet
                and self.Held_Right == other.Held_Right
                and self.Held_Left == other.Held_Left)

    def items(self) -> list[Item]:
        items = [self.Head,
                 self.Jewel1,
                 self.Jewel2,
                 self.Cloak,
                 self.Body,
                 self.Hands,
                 self.Legs,
                 self.Feet,
                 self.Held_Right,
                 self.Held_Left]

        return [item for item in items if not (item is None or item.Name == "")]
