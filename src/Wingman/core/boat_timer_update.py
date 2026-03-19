from Wingman.core.parsing.parser import BoatNotificationBytes
from Wingman.core.boat_captain_mob import BoatCaptainNpc

class BoatTimerNotification:
    def __init__(self, boatCaptain: BoatCaptainNpc | None, boatNotification: BoatNotificationBytes, timestamp: float):
        self.BoatCaptain = boatCaptain
        self.BoatNotification = boatNotification
        self.Timestamp = timestamp
