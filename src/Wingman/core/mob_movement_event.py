from enum import Enum, auto
    
class MobMovementType(Enum):
    LEAVING = auto()
    ENTERING = auto()

class MobEnteringReasons(Enum):
    ARRIVES_FROM = auto()
    ENTERS_THE_ROOM = auto()
    CHASES = auto()

class MobLeavingReasons(Enum):
    LEAVES = auto()
    DIES = auto()
    CHASES = auto()

class MobMovementEvent:
    def __init__(self,
                 movement: MobMovementType,
                 movementReason: MobEnteringReasons | MobLeavingReasons,
                 mobName: str,
                 isChasingYou: bool):
        self.movementType = movement
        self.movementReason = movementReason
        self.mobName = mobName
        self.isChasingYou = isChasingYou
        