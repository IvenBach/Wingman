from Wingman.core.parser import Parser
from Wingman.core.meditation_display import MeditationDisplay
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