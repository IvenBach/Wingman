from pathlib import Path
import sys
from unittest.mock import patch

if  __name__ == "__main__":
    srcDirectory = Path(__file__).parent.parent.parent.resolve()
    sys.path.append(str(srcDirectory))
from Wingman.core.meditation_display import MeditationDisplay

def test_ElapsedTimeOf_0_Seconds_ShowDisplaysRegenOf_3():
    md = MeditationDisplay()
    actual = md.value()
    
    assert actual == '3'

def test_ElapsedTimeOf_30_Seconds_ShowDisplaysRegenOf_3():
    md = MeditationDisplay()

    with patch.object(MeditationDisplay, md.meditationDurationInSeconds.__name__) as mockedDuration:
        mockedDuration.return_value = 30
        actual = md.value()

    assert actual == '3'

def test_ElapsedTimeOf_31_Seconds_ShowDisplaysRegenOf_4():
    md = MeditationDisplay()

    with patch.object(MeditationDisplay, md.meditationDurationInSeconds.__name__) as mockedDuration:
        mockedDuration.return_value = 31
        actual = md.value()

    assert actual == '4'

def test_ElapsedTimeOf_60_Seconds_ShowDisplaysRegenOf_4():
    md = MeditationDisplay()
    
    with patch.object(MeditationDisplay, md.meditationDurationInSeconds.__name__) as mockedDuration:
        mockedDuration.return_value = 60
        actual = md.value()

    assert actual == '4'
def test_ElapsedTimeGreaterThan_60_Seconds_ShowDisplaysRegenOfMax():
    md = MeditationDisplay()

    with patch.object(MeditationDisplay, md.meditationDurationInSeconds.__name__) as mockedDuration:
        mockedDuration.return_value = 61
        actual = md.value()

    assert actual == 'Max'

def test_ObserverNotified_WhenRegenValueChanges():
    md = MeditationDisplay()
    observerNotified = False

    class ConcreteObserver():
        def updateMeditationDisplayValue(self):
            print(f"Internals state used in concrete example.")
        
        nonlocal observerNotified
        observerNotified = True

    o = ConcreteObserver()
    md.attach(o)

    with patch.object(md, md.meditationDurationInSeconds.__name__) as mockedDuration:
        mockedDuration.return_value = 33
        md.value()

    assert observerNotified == True

test_ElapsedTimeOf_31_Seconds_ShowDisplaysRegenOf_4()