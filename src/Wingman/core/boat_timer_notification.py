import datetime as dt

from Wingman.core.parsing.parser import BoatNotificationBytes
from Wingman.core.boat_captain_npc import BoatCaptainNpcs

class BoatTimerNotification:
    def __init__(self, boatCaptain: BoatCaptainNpcs | None, boatNotification: BoatNotificationBytes, notificationDateTime: dt.datetime):
        self.BoatCaptain = boatCaptain
        self.BoatNotification = boatNotification
        self.DateTime = notificationDateTime
