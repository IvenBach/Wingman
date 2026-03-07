from Wingman.core.affect import Affect
from Wingman.core.parser import Parser
from Wingman.core.meditation_display import MeditationDisplay
from Wingman.core.inventory import Inventory, Equipment
from Wingman.core.item import Item

class Model:
    def __init__(self, parser: Parser):
        self.parser = parser
        self.isAfk: bool | None = None
        self.isMeditating: bool | None = None
        self.meditationDisplay = MeditationDisplay()
        self.isHiding: bool | None = None
        self.currentMobsInRoom: list[str] = []
        self.ignoreTheseMobsInCurrentRoom: list[str] = []
        self.includePetsInGroup: bool = False
        self.BuffOrShieldEnding: Parser.ParseBuffOrShieldText | None = None
        self.inventory: Inventory = Inventory(Equipment(), [])
        self.AffectsWithTimeExpiration: list[Affect] = []
        self.SoughtAfterItems_ThatDropped:  list[str] = []
        self.SoughtAfterItems_Names: set[str] = set()
        self.SoughtAfterItems_BaseItemNames: set[str] = set()
