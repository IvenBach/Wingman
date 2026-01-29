from Wingman.core.meditation_display import MeditationDisplay
from unittest.mock import patch

def test_ElapsedTimeOf_0_Seconds_ShowDisplaysRegenOf_3():
    md = MeditationDisplay()
    actual = md.meditationRegenerationValue()
    
    assert actual == '3'

def test_ElapsedTimeOf_32_Seconds_ShowDisplaysRegenOf_3():
    md = MeditationDisplay()

    with patch.object(MeditationDisplay, md.meditationDurationInSeconds.__name__) as mockedDuration:
        mockedDuration.return_value = 32
        actual = md.meditationRegenerationValue()

    assert actual == '3'

def test_ElapsedTimeOf_33_Seconds_ShowDisplaysRegenOf_4():
    md = MeditationDisplay()

    with patch.object(MeditationDisplay, md.meditationDurationInSeconds.__name__) as mockedDuration:
        mockedDuration.return_value = 33
        actual = md.meditationRegenerationValue()

    assert actual == '4'

def test_ElapsedTimeOf_64_Seconds_ShowDisplaysRegenOf_4():
    md = MeditationDisplay()

    with patch.object(MeditationDisplay, md.meditationDurationInSeconds.__name__) as mockedDuration:
        mockedDuration.return_value = 64
        actual = md.meditationRegenerationValue()

    assert actual == '4'
def test_ElapsedTimeGreaterThan_64_Seconds_ShowDisplaysRegenOfMax():
    md = MeditationDisplay()

    with patch.object(MeditationDisplay, md.meditationDurationInSeconds.__name__) as mockedDuration:
        mockedDuration.return_value = 65
        actual = md.meditationRegenerationValue()

    assert actual == 'Max'

def test_InvokingShow_DisplaysExpectedValue():
    md = MeditationDisplay()

    with patch.object(md, md.meditationRegenerationValue.__name__) as mockedDuration:
        mockedDuration.return_value = "foo"
        actual = md.show()
    
    assert actual == "Med: foo"
