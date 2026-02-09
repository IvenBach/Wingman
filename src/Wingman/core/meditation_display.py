import time

from Wingman.core.DesignPatterns.ObserverPattern.subject import Subject

class MeditationDisplay(Subject):
    '''Attempt to follow Observer pattern. Implemented `updateMeditationDisplayValue` notification method for subscribers.'''
    def __init__(self):
        super().__init__()
        self._startTime = time.time()
        self._lastRegenValue = '3'
    
    #region - Observer Pattern
    def attach(self, observer):
        """Attach an observer to receive notifications via `updateMeditationDisplayValue` when the regeneration value changes."""
        super().attach(observer)    
    
    def notify(self):
        for observer in self._observers:
            observer.updateMeditationDisplayValue()

    @property
    def lastRegenValue(self) -> str:
        return self._lastRegenValue
    
    @lastRegenValue.setter
    def lastRegenValue(self, value):
        if value != self._lastRegenValue:
            self._lastRegenValue = value

            if value == '':
                return
            
            self.notify()
    #endregion
    
    def meditationDurationInSeconds(self) -> int:
        """Returns the duration of meditation in seconds."""
        return int(time.time() - self._startTime)
    
    def _updateMeditationRegenerationValue(self):
        """Calculates the regeneration value based on meditation duration."""
        duration = self.meditationDurationInSeconds()
        if duration > 60:
            self.lastRegenValue = 'Max'
        elif duration > 30:
            self.lastRegenValue = '4'
        else:
            self.lastRegenValue = '3'
    
    def value(self) -> str:
        self._updateMeditationRegenerationValue()
        return self.lastRegenValue

    def displayValue(self) -> str:
        self._updateMeditationRegenerationValue()
        return f"Med: {self.lastRegenValue}"
    
    def resetMeditationStartTime(self):
        self._startTime = time.time()
        self.lastRegenValue = ''
