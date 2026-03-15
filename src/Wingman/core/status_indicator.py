from enum import Flag, auto
class StatusIndicator(Flag):
    BLEED = auto()
    POISON = auto()
    DISEASE = auto()
    STUN = auto()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StatusIndicator):
            return self.value == other.value

        if isinstance(other, str):
            other_flag = StatusIndicator.FromString(other)
            return self.value == other_flag.value

        return False
    
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __str__(self):
        match self:
            case StatusIndicator.BLEED:
                return "B"
            case StatusIndicator.POISON:
                return "P"
            case StatusIndicator.DISEASE:
                return "D"
            case StatusIndicator.STUN:
                return "S"
            case _:
                return ''

    @staticmethod
    def FromString(stringRepresentation: str) -> 'StatusIndicator':
        value = StatusIndicator(0)
        stringToFlag = {
            'B': StatusIndicator.BLEED,
            'P': StatusIndicator.POISON,
            'D': StatusIndicator.DISEASE,
            'S': StatusIndicator.STUN
        }
        for char in stringRepresentation:
            if char in stringToFlag:
                value |= stringToFlag[char]
        
        return value
