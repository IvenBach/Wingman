class Subject:
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        """Attach an observer to receive notifications when the subject's state changes."""
        if observer not in self._observers:
            self._observers.append(observer)
        
    def detach(self, observer):
        """Detach an observer from receiving notifications."""
        try:
            self._observers.remove(observer)
        except:
            pass
    
    def notify(self):
        """Notify all observers/subscribers that a change occurred."""
        for observer in self._observers:
            observer.update()