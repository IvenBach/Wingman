import pytest
import time
import datetime as dt

from Wingman.core.boat_next_docks_at import BoatNextAt, InvasionPortIdentifier
from Wingman.core.boat_transit_information import BoatTransitInformation
class TestRealmDock:
    def test_NoLastDockRecorded_ReturnsNone(self):
        result = BoatNextAt.realmDock(None, 1, 1)

        assert result is None

    def test_TimestampEarlierThanLastDocked_ThrowsValueError(self):
        with pytest.raises(ValueError):
            BoatNextAt.realmDock(dt.datetime(2026, 1, 1, 10, 0, 0),
                                 100,
                                 dt.datetime(2026, 1, 1, 9, 0, 0))

    def test_TimeLessThanWholeRoundTrip_CalculatesCorrectValue(self):
        boatLastDockedInRealm = dt.datetime(2026, 1, 1, 9, 0, 0)
        roundTripTimeInSeconds = 30
        currentTimestamp = dt.datetime(2026, 1, 1, 9, 1, 0)

        result = BoatNextAt.realmDock(boatLastDockedInRealm, roundTripTimeInSeconds, currentTimestamp)

        assert result == dt.datetime(2026, 1, 1, 9, 1, 30)

    def test_TimeGreaterThanWholeRoundTrip_CalculatesCorrectValue(self):
        boatLastDockedInRealm = dt.datetime(2026, 1, 1, 9, 0, 0)
        roundTripTimeInSeconds = 501
        currentTimestamp = dt.datetime(2026, 1, 1, 9, 20, 0)

        result = BoatNextAt.realmDock(boatLastDockedInRealm, roundTripTimeInSeconds, currentTimestamp)

        assert result == dt.datetime(2026, 1, 1, 9, 25, 3)

    @pytest.mark.parametrize('roundTripTimeInSeconds',
                            [0, -1],
                            ids=["Zero roundTripTimeInSeconds",
                                "Negative roundTripTimeInSeconds",])
    def test_ZeroOrNegativeRoundTripTime_RaisesValueError(self,
                                                        roundTripTimeInSeconds: int):
        with pytest.raises(ValueError, match=".*Input values.*"):
            BoatNextAt.realmDock(dt.datetime(2026, 1, 1, 9, 0, 0),
                                 roundTripTimeInSeconds,
                                 dt.datetime(2026, 1, 1, 9, 20, 0))

    def test_KaidBoatTransitValues_CalculatesCorrectValue(self):
        expected = dt.datetime(2026, 1, 1, 9, 55, 0)

        boatLastDockedInRealm = dt.datetime(2026, 1, 1, 9, 15, 0)
        roundTripTimeInSeconds = BoatTransitInformation.KAID_BOAT_ROUNDTRIP_TIME_IN_SECONDS.value
        currentTimestamp = dt.datetime(2026, 1, 1, 9, 53, 27)

        result = BoatNextAt.realmDock(boatLastDockedInRealm,
                                      roundTripTimeInSeconds,
                                      currentTimestamp)

        assert result is not None
        assert result == expected

    def test_RealmBoatTransitValues_CalculatesCorrectValue(self):
        expected = dt.datetime(2026, 1, 1, 10, 9, 0)

        boatLastDockedInRealm = dt.datetime(2026, 1, 1, 9, 15, 0)
        roundTripTimeInSeconds = BoatTransitInformation.REALM_BOAT_ROUNDTRIP_TIME_IN_SECONDS.value
        currentTimestamp = dt.datetime(2026, 1, 1, 9, 53, 27)

        result = BoatNextAt.realmDock(boatLastDockedInRealm,
                                      roundTripTimeInSeconds,
                                      currentTimestamp)

        assert result is not None
        assert result == expected

class TestInvasionPort:
    @pytest.mark.parametrize('portIdentifier, portToPortTransitTimeIncludingTimeDockedInSeconds, boatLastDockedInRealm, currentTimestamp, expectedArrivalTime',
        [(InvasionPortIdentifier.FirstInvasionPort, 150,
         dt.datetime(2026, 1, 1, 9, 15, 0), dt.datetime(2026, 1, 1, 9, 20, 0), dt.datetime(2026, 1, 1, 9, 25, 0)),
        (InvasionPortIdentifier.SecondInvasionPort, 201,
         dt.datetime(2026, 1, 1, 9, 15, 0), dt.datetime(2026, 1, 1, 9, 22, 0), dt.datetime(2026, 1, 1, 9, 31, 45))],
                            ids=["First invasion port",
                                 "Second invasion port"])
    def test_RealmBoatInvadingAtFirstPort_TimeLessThanRoundTrip_CalculatesCorrectValues(self,
                                                        portIdentifier: InvasionPortIdentifier,
                                                        portToPortTransitTimeIncludingTimeDockedInSeconds: int,
                                                        boatLastDockedInRealm: dt.datetime,
                                                        currentTimestamp: dt.datetime,
                                                        expectedArrivalTime: dt.datetime):
        result = BoatNextAt.invasionPort(boatLastDockedInRealm,
                                        portToPortTransitTimeIncludingTimeDockedInSeconds,
                                        currentTimestamp,
                                        portIdentifier)

        assert result == expectedArrivalTime

    @pytest.mark.parametrize('portIdentifier, portToPortTransitTimeIncludingTimeDockedInSeconds, boatLastDockedInRealm, currentTimestamp, expectedArrivalTime',
        [(InvasionPortIdentifier.FirstInvasionPort, 50,
          dt.datetime(2026, 1, 1, 9, 15, 0), dt.datetime(2026, 1, 1, 9, 20, 1), dt.datetime(2026, 1, 1, 9, 20, 50)),
         (InvasionPortIdentifier.SecondInvasionPort, 50,
          dt.datetime(2026, 1, 1, 9, 15, 0), dt.datetime(2026, 1, 1, 9, 21, 2), dt.datetime(2026, 1, 1, 9, 21, 40))],
                            ids=["First invasion port",
                                "Second invasion port"])
    def test_RealmBoatInvadingAtFirstPort_TimeLessGreaterThanRoundTrip_CalculatesCorrectValue(self,
                                                        portIdentifier: InvasionPortIdentifier,
                                                        portToPortTransitTimeIncludingTimeDockedInSeconds: int,
                                                        boatLastDockedInRealm: dt.datetime,
                                                        currentTimestamp: dt.datetime,
                                                        expectedArrivalTime: dt.datetime):
        result = BoatNextAt.invasionPort(boatLastDockedInRealm,
                                        portToPortTransitTimeIncludingTimeDockedInSeconds,
                                        currentTimestamp,
                                        portIdentifier)

        assert result == expectedArrivalTime

class TestKaidPort:
    def test_CurrentTimestampBeforeBoatNextDocksInKaid_CalculatesCorrectValue(self):
        expected = dt.datetime(2026, 1, 1, 9, 12, 0)

        boatNextDocksInRealm = dt.datetime(2026, 1, 1, 9, 15, 0)
        portToPortTransitTimeIncludingTimeDockedInSeconds = BoatTransitInformation.KAID_BOAT_TRANSIT_TIME_IN_SECONDS.value + BoatTransitInformation.REALM_BOAT_DOCK_TIME_IN_SECONDS.value
        currentTimestamp = dt.datetime(2026, 1, 1, 9, 10, 0)

        result = BoatNextAt.kaidPort(boatNextDocksInRealm,
                                     portToPortTransitTimeIncludingTimeDockedInSeconds,
                                     currentTimestamp)

        assert result == expected

    def test_CurrentTimestampBeforeBoatNextDocksInRealm_CalculatesCorrectValue(self):
        expected = dt.datetime(2026, 1, 1, 9, 19, 0)

        boatNextDocksInRealm = dt.datetime(2026, 1, 1, 9, 15, 0)
        portToPortTransitTimeIncludingTimeDockedInSeconds = BoatTransitInformation.KAID_BOAT_TRANSIT_TIME_IN_SECONDS.value + BoatTransitInformation.KAID_BOAT_DOCK_TIME_IN_SECONDS.value
        currentTimestamp = dt.datetime(2026, 1, 1, 9, 14, 0)

        result = BoatNextAt.kaidPort(boatNextDocksInRealm,
                                     portToPortTransitTimeIncludingTimeDockedInSeconds,
                                     currentTimestamp)

        assert result == expected

    @pytest.mark.parametrize('boatLastDockedInRealm, currentTimestamp, expected',[
        (dt.datetime(2026, 1, 1, 9, 15, 0), dt.datetime(2026, 1, 1, 10, 14, 3), dt.datetime(2026, 1, 1, 10, 15, 0)),
        (dt.datetime(2026, 1, 1, 9, 15, 0), dt.datetime(2026, 1, 1, 10, 6, 3), dt.datetime(2026, 1, 1, 10, 7, 0))],
                            ids=["In transit to kaid port",
                                 'In transit to realm port'])
    def test_CurrentTimestampHourAfterLastRecordedBoatNextDocksInRealm_CalculatesCorrectValue(self,
                                                                                boatLastDockedInRealm: dt.datetime,
                                                                                currentTimestamp: dt.datetime,
                                                                                expected: dt.datetime):
        portToPortTransitTimeIncludingTimeDockedInSeconds = BoatTransitInformation.KAID_BOAT_TRANSIT_TIME_IN_SECONDS.value + BoatTransitInformation.KAID_BOAT_DOCK_TIME_IN_SECONDS.value

        result = BoatNextAt.kaidPort(boatLastDockedInRealm,
                                     portToPortTransitTimeIncludingTimeDockedInSeconds,
                                     currentTimestamp)

        assert result == expected
