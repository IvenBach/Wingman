from abc import ABC, abstractmethod
class Observer(ABC):
    @abstractmethod
    def update(self, subject):
        """Receive update from subject."""
        pass