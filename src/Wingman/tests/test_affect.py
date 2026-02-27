from datetime import timedelta
import time

import pytest

from Wingman.core.affect import Affect

def test_StringDisplay_DurationSpansOverMidnight_DisplayHMS_Format():
    affect = Affect("TestAffect", timedelta(hours=2, seconds=1).total_seconds())
    stringRepresentation = str(affect)

    assert "2:00:00" in stringRepresentation

def test_DurationRemaining_ForTesting():
    affect = Affect("TestAffect", 300)

    assert affect.timeRemainingInSeconds() == pytest.approx(300, rel=0.5)

def test_NoDuration_TimeRemainingReturnsFloatInf():
    affect = Affect("TestAffect", None)

    assert affect.timeRemainingInSeconds() == float("inf")

def test_StringTimeRemaining():
    a = Affect("Foo", 60*60*1 + 60*7 + 18)
    timePortion = str(a).split(' ')[1]

    convertedTime = time.strptime(timePortion, "%H:%M:%S")

    assert convertedTime.tm_hour == 1
    assert convertedTime.tm_min == 7
    assert convertedTime.tm_sec == 17
