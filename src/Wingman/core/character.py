from Wingman.core.status_indicator import StatusIndicator
from Wingman.core.resource_bar import ResourceBar

class Character:
    def __init__(self, name: str,
                        class_: str = "",
                        level: int = -1,
                        status: StatusIndicator = StatusIndicator(0),
                        hp: ResourceBar = ResourceBar(-1,-1),
                        fat: ResourceBar = ResourceBar(-1,-1),
                        pow: ResourceBar = ResourceBar(-1,-1),
                        isNewFollower: bool = False):
        self.Name = name.strip()

        self.Class_ = class_.strip(); 
        self.Level = level
        self.Status = status
        self.Hp = hp
        self.Fat = fat
        self.Pow = pow
        self.IsNewGroupFollower = isNewFollower

    def __repr__(self):
        return f"{self.Name}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Character):
            return False

        # Compare `ResourceBar`s first since they're most likely to differ
        return (self.Hp == other.Hp and
                self.Fat == other.Fat and
                self.Pow == other.Pow and
                self.Status == other.Status and
                self.Name == other.Name and
                self.Class_ == other.Class_ and
                self.Level == other.Level and
                self.IsNewGroupFollower == other.IsNewGroupFollower)

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)