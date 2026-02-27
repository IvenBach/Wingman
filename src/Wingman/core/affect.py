import time
from datetime import datetime, timedelta

class Affect:
    '''Class representing an active affect on the player, such as a buff or debuff.'''
    def __init__(self, name: str, durationLength: float | None):
        self.Name: str = name

        self.DurationEndsAt: float | None = datetime.now().timestamp() + durationLength if durationLength is not None else None
    def timeRemainingInSeconds(self) -> float:
        if self.DurationEndsAt is None:
            return float("inf")

        return max(0, int(self.DurationEndsAt - time.time()))

    def __str__(self) -> str:
        if self.DurationEndsAt is None:
            return f"{self.Name}, Infinite"

        return f"{self.Name}, {timedelta(seconds=self.timeRemainingInSeconds())}"

    def __repr__(self) -> str:
        return self.__str__()
