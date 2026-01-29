import time

class MeditationDisplay:
    def __init__(self):
        self.startTime = time.time()
        
    def meditationDurationInSeconds(self) -> int:
        """Returns the duration of meditation in seconds."""
        return int(time.time() - self.startTime)
    
    def meditationRegenerationValue(self) -> str:
        """Calculates the regeneration value based on meditation duration."""
        duration = self.meditationDurationInSeconds()
        if duration > 64:
            return 'Max'
        elif duration > 32:
            return '4'
        else:
            return '3'
    
    def show(self) -> str:
        return f"Med: {self.meditationRegenerationValue()}"
        