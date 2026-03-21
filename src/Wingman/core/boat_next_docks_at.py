from enum import Enum, auto
import datetime as dt

from Wingman.core.boat_transit_information import BoatTransitInformation

class InvasionPortIdentifier(Enum):
    FirstInvasionPort = auto()
    SecondInvasionPort = auto()

class BoatNextAt:
    @staticmethod
    def realmDock(boatLastDockedInRealm: dt.datetime | None,
                  roundTripTimeInSeconds: int,
                  currentDateTime: dt.datetime) -> dt.datetime | None:
        if boatLastDockedInRealm is None:
            return None

        if roundTripTimeInSeconds <= 0:
            raise ValueError("Input values must be positive.")


        elapsedSecondsInTransit = int((currentDateTime - boatLastDockedInRealm).total_seconds())

        if elapsedSecondsInTransit < 0:
            raise ValueError("Current datetime is earlier than the last docked time.")

        wholeRoundTrips = elapsedSecondsInTransit // roundTripTimeInSeconds
        elapsedSecondsInTransit -= wholeRoundTrips * roundTripTimeInSeconds

        nextBoatDockingInRealm = boatLastDockedInRealm + dt.timedelta(seconds=(wholeRoundTrips + 1) * roundTripTimeInSeconds)
        return nextBoatDockingInRealm

    @staticmethod
    def _AllInputValuesNonZeroPositiveNumbers(boatLastDockedInRealm: dt.datetime,
                                            roundTripTimeInSeconds: int,
                                            currentDateTime: dt.datetime) -> bool:
        return boatLastDockedInRealm.timestamp() > 0 and roundTripTimeInSeconds > 0 and currentDateTime.timestamp() > 0

    @staticmethod
    def invasionPort(boatLastDockedInRealm: dt.datetime | None,
                        portToPortTransitTimeIncludingTimeDockedInSeconds: int,
                        currentDateTime: dt.datetime,
                        portIdentifier: InvasionPortIdentifier) -> dt.datetime | None:
        if boatLastDockedInRealm is None:
            return None

        if not BoatNextAt._AllInputValuesNonZeroPositiveNumbers(boatLastDockedInRealm,
                                                                portToPortTransitTimeIncludingTimeDockedInSeconds,
                                                                currentDateTime):
            raise ValueError("All input values must be positive.")

        elapsedSecondsInTransit = int((currentDateTime - boatLastDockedInRealm).total_seconds())

        if elapsedSecondsInTransit < 0:
            raise ValueError("Current datetime is earlier than the last docked time.")

        roundTripTimeInSeconds = 3 * portToPortTransitTimeIncludingTimeDockedInSeconds
        wholeRoundTrips = int(elapsedSecondsInTransit) // roundTripTimeInSeconds
        accurateRealmDockTime = boatLastDockedInRealm + dt.timedelta(seconds=wholeRoundTrips * roundTripTimeInSeconds)
        if portIdentifier == InvasionPortIdentifier.FirstInvasionPort:
            deltaFromRealmPort = dt.timedelta(seconds=portToPortTransitTimeIncludingTimeDockedInSeconds)
        elif portIdentifier == InvasionPortIdentifier.SecondInvasionPort:
            deltaFromRealmPort = dt.timedelta(seconds=2 * portToPortTransitTimeIncludingTimeDockedInSeconds)

        if currentDateTime <= accurateRealmDockTime + deltaFromRealmPort:
            nextPortTime = accurateRealmDockTime + deltaFromRealmPort
        else:
            delta = deltaFromRealmPort + dt.timedelta(seconds=roundTripTimeInSeconds)
            nextPortTime = accurateRealmDockTime + delta

        return nextPortTime

    @staticmethod
    def kaidPort(boatLastDockedInRealm: dt.datetime,
                 portToPortTransitTimeIncludingTimeDockedInSeconds: int,
                 currentDateTime: dt.datetime) -> dt.datetime:
        if currentDateTime < boatLastDockedInRealm - dt.timedelta(seconds=portToPortTransitTimeIncludingTimeDockedInSeconds):
            return boatLastDockedInRealm - dt.timedelta(seconds=portToPortTransitTimeIncludingTimeDockedInSeconds)

        elapsedSecondsInTransit = currentDateTime - boatLastDockedInRealm
        wholeRoundTrips =  int(elapsedSecondsInTransit.total_seconds()) // BoatTransitInformation.KAID_BOAT_ROUNDTRIP_TIME_IN_SECONDS.value


        nextBoatDockingInRealm = boatLastDockedInRealm + dt.timedelta(seconds=(wholeRoundTrips + 1) * BoatTransitInformation.KAID_BOAT_ROUNDTRIP_TIME_IN_SECONDS.value)
        if currentDateTime <= nextBoatDockingInRealm - dt.timedelta(seconds=portToPortTransitTimeIncludingTimeDockedInSeconds):
            return nextBoatDockingInRealm - dt.timedelta(seconds=portToPortTransitTimeIncludingTimeDockedInSeconds)
        else:
            return nextBoatDockingInRealm + dt.timedelta(seconds=portToPortTransitTimeIncludingTimeDockedInSeconds)
