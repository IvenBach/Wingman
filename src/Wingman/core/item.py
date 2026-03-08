from typing import overload
from re import Match
from enum import Enum, StrEnum, auto

class ItemMaterials(Enum):
    CLOTH = auto()
    LEATHER = auto()
    STUDDED_AND_PLATE = auto()
    WOOD = auto()

class ItemMaterial_Cloth(Enum):
    WOOL = auto()
    COTTON = auto()
    SILK = auto()
    GOSSAMER = auto()
    WISPWEAVE = auto()
    EBONWEAVE = auto()

class ItemMaterial_Leather(Enum):
    LEATHER = auto()
    ROUGH = auto()
    SUEDE = auto()
    EMBOSSED = auto()
    WYVERNSCALE = auto()
    ENCHANTED = auto()

class ItemMaterial_Studded_And_Plate(Enum):
    BRONZE = auto()
    IRON = auto()
    STEEL = auto()
    ALLOY = auto()
    MITHRIL = auto()
    LAEN = auto()

class ItemMaterial_Wood(Enum):
    MAPLE = auto()
    OAK = auto()
    YEW = auto()
    ROSEWOOD = auto()
    IRONWOOD = auto()
    EBONY = auto()

class ItemSlot(Enum):
    HEAD = auto()
    JEWEL = auto()
    CLOAK = auto()
    BODY = auto()
    HANDS = auto()
    FEET = auto()
    LEGS = auto()
    HELD = auto()

class ItemEnchantments(Enum):
    SILVERED = auto()
    BRIGHT = auto()
    SHINING = auto()
    GLOWING = auto()
    LUSTROUS = auto()
    BRILLIANT = auto()

class ItemType(StrEnum):
    CLAW = "CLAW"
    CLOTH = "CLOTH"
    CRUSH_1H = "CRUSH_1H"
    CRUSH_2H = "CRUSH_2H"
    DIRECT_CRUSH_1H = "DIRECT_CRUSH_1H"
    DIRECT_CRUSH_2H = "DIRECT_CRUSH_2H"
    DIRECT_SLASH_1H = "DIRECT_SLASH_1H"
    DIRECT_SLASH_2H = "DIRECT_SLASH_2H"
    DIRECT_THRUST_1H = "DIRECT_THRUST_1H"
    DIRECT_THRUST_2H = "DIRECT_THRUST_2H"
    FIRED_1H = "FIRED_1H"
    FIRED_2H = "FIRED_2H"
    LEATHER = "LEATHER"
    OFFHAND_CRUSH_1H = "OFFHAND_CRUSH_1H"
    OFFHAND_CRUSH_2H = "OFFHAND_CRUSH_2H"
    OFFHAND_DIRECT_SLASH_1H  = "OFFHAND_DIRECT_SLASH_1H"
    OFFHAND_SLASH_1H = "OFFHAND_SLASH_1H"
    OFFHAND_SLASH_2H = "OFFHAND_SLASH_2H"
    OFFHAND_THRUST_1H = "OFFHAND_THRUST_1H"
    OFFHAND_THRUST_2H = "OFFHAND_THRUST_2H"
    PARRY_STAFF = "PARRY_STAFF"
    PLATE = "PLATE"
    SLASH_1H = "SLASH_1H"
    SLASH_2H = "SLASH_2H"
    STUDDED = "STUDDED"
    THRUST_1H = "THRUST_1H"
    THRUST_2H = "THRUST_2H"

class DamageRange(StrEnum):
    AMAZING = "AMAZING"
    GOOD = "GOOD"
    VERY_GOOD = "VERY_GOOD"
    SMALL = "SMALL"

class FumbleRate(StrEnum):
    SOMETIMES = "SOMETIMES"
    NEVER = "NEVER"
    RARELY = "RARELY"
    OFTEN = "OFTEN"

class AccuracyRate(StrEnum):
    NORMAL = "NORMAL"
    BETTER = "BETTER"
    MUCH_BETTER = "MUCH_BETTER"
    WORSE = "WORSE"

class DefenseRating(StrEnum):
    MUCH_WORSE = "MUCH_WORSE"
    WORSE = "WORSE"
    NORMAL = "NORMAL"
    BETTER = "BETTER"
    MUCH_BETTER = "MUCH_BETTER"

class Sigil(StrEnum):
    FIRE = "FIRE"
    COLD = "COLD"
    SHOCK = "SHOCK"
    WATER = "WATER"
    EARTH = "EARTH"
    LIGHTNING = "LIGHTNING"
    PAIN = "PAIN"
    NORMAL = "NORMAL"

# Inspiration taken from - Test cases used to cover 'Note to Implementers'
#https://learn.microsoft.com/en-us/dotnet/api/system.icomparable-1.compareto?view=net-10.0#notes-to-implementers
#https://learn.microsoft.com/en-us/dotnet/api/system.icomparable-1?view=net-10.0#remarks
class QuantityComparer(Enum):
    LESS_THAN = -1
    EQUAL_TO = 0
    GREATER_THAN = 1
    INVALID_COMPARISON = 9999 # String name comparison with non-matching names. ¿Better way?

class Item:
    _MATERIAL_LOOKUP = {}

    for enum_cls, mat_type in [(ItemMaterial_Cloth, ItemMaterials.CLOTH),
                                (ItemMaterial_Leather, ItemMaterials.LEATHER),
                                (ItemMaterial_Studded_And_Plate, ItemMaterials.STUDDED_AND_PLATE),
                                (ItemMaterial_Wood, ItemMaterials.WOOD)]:
        for name, member in enum_cls.__members__.items():
            _MATERIAL_LOOKUP[name.lower()] = member

    del(name, member, enum_cls, mat_type)

    @staticmethod
    def resolveMaterial(materialName: str) -> Enum | None:
        '''Look for the material in a cached registry'''
        if not materialName:
            return None

        return Item._MATERIAL_LOOKUP.get(materialName.lower(), None)

    _ENCHANTMENT_LOOKUP = {enchantment.name.lower(): enchantment for enchantment in ItemEnchantments}

    @staticmethod
    def resolveEnchantment(enchantmentName: str) -> ItemEnchantments | None:
        '''Look for the enchantment in a cached registry'''
        if not enchantmentName:
            return None

        return Item._ENCHANTMENT_LOOKUP.get(enchantmentName.lower(), None)


    @overload
    def __init__(self, name: str):...
    @overload
    def __init__(self, name: str, quantity: int):...
    @overload
    def __init__(self, name: str, quantity: None):...
    @overload
    def __init__(self, name: str, slot: ItemSlot):...

    def __init__(self,
                 name: str,
                 slot: ItemSlot | None = None,
                 type: ItemType | None = None,
                 spell: str | None = None,
                 level: int = 0,
                 damage: DamageRange | None = None,
                 timer: int | None = None,
                 fumble: FumbleRate | None = None,
                 accuracy: AccuracyRate | None = None,
                 defense: DefenseRating | None = None,
                 sigil_: Sigil | None = None,
                 sigilLevel: int | None = None,
                 weight: int = 0,
                 realm: str | None = None,
                 area: str | None = None,
                 mob: str | list[str] = "",
                 quantity: int | None = None,
                 enchantment: ItemEnchantments | None = None,
                 material: Enum | None = None,
                 parsedBaseItemName: str | None = None):
        self.Name = name.strip()
        self.Slot = slot
        self.Type = type
        self.Spell = spell
        self.Level = level
        self.Damage = damage
        self.Timer = timer
        self.Fumble = fumble
        self.Accuracy = accuracy
        self.Defense = defense
        self.Sigil_ = sigil_
        self.SigilLevel = sigilLevel
        self.Weight = weight
        self.Realm = realm
        self.Area = area
        self.Mob = mob
        self.Quantity = quantity
        self.Enchantment = enchantment
        self.Material = material
        self.ParsedBaseItemName = parsedBaseItemName

    def __str__(self):
        if self.Quantity is not None:
            return f"({str(self.Quantity).rjust(2)}) {self.Name}"

        return self.Name

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, str):
            from Wingman.core.parsing.parser import Parser
            return self == Parser.parseQuantityItem(other)

        if not isinstance(other, Item):
            return False

        if self.Name.lower() != other.Name.lower():
            return False

        return self.Quantity == other.Quantity

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.Name.lower(), self.Quantity))

    def QuantityComparison(self, other) -> 'QuantityComparer':
        if isinstance(other, str):
            from Wingman.core.parsing.parser import Parser
            itemOther = Parser.parseQuantityItem(other)

            if self.Name != itemOther.Name:
                return QuantityComparer.INVALID_COMPARISON

        if not isinstance(other, Item):
            return QuantityComparer.INVALID_COMPARISON

        if self.Name != other.Name:
            return QuantityComparer.INVALID_COMPARISON

        if self.Quantity is None and other.Quantity is None:
            return QuantityComparer.EQUAL_TO

        if self.Quantity is None and other.Quantity is not None:
            return QuantityComparer.LESS_THAN

        if self.Quantity is not None and other.Quantity is None:
            return QuantityComparer.GREATER_THAN

        assert self.Quantity is not None and other.Quantity is not None
        if self.Quantity < other.Quantity:
            return QuantityComparer.LESS_THAN

        if self.Quantity > other.Quantity:
            return QuantityComparer.GREATER_THAN

        return QuantityComparer.EQUAL_TO

    def subtract(self, other):
        if not isinstance(other, Item):
            raise ValueError(f"Can only subtract another Item from this Item, not {type(other)}")

        if self.Name != other.Name:
            raise ValueError(f"Cannot subtract items with different names: '{self.Name}' and '{other.Name}'")

        if self.Quantity is None and other.Quantity is None:
            return 0

        if self.Quantity is None and not other.Quantity is None:
            return other.Quantity - 1

        if self.Quantity is not None and other.Quantity is None:
            return self.Quantity - 1

        assert self.Quantity is not None and other.Quantity is not None
        return self.Quantity - other.Quantity
