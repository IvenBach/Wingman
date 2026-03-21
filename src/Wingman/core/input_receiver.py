from typing import Any, overload
from collections import deque
from Wingman.core.affect import Affect
from Wingman.core.boat_timer_notification import BoatTimerNotification
from Wingman.core.mobs_chasing_you import MobsChasingYou
from Wingman.core.mobs_in_room import MobsInRoom
from Wingman.core.inventory import Inventory
from Wingman.core.equipment import Equipment
from Wingman.core.npc_in_room import BoatCaptainInRoom

class InputReceiver:
    '''Accepts input lines and queues them for processing.'''
    stack_log_file = 'stack_log.txt'  # File to store stack logs

    def __init__(self, on_new_line_callback=None):
        self.last_received = ""
        self._queue: deque[str | Any] = deque()
        self.on_new_line_callback = on_new_line_callback  # Optional callback function

        # Clear the log file when the instance is initialized
        with open(self.stack_log_file, 'w') as f:
            f.write('')  # Clear the contents of the file

    @overload
    def receive(self, input_line: str) -> None: ...
    @overload
    def receive(self, mobInRoom: MobsInRoom) -> None: ...
    @overload
    def receive(self, inventory: Inventory) -> None: ...
    @overload
    def receive(self, equippedGear: Equipment) -> None: ...
    @overload
    def receive(self, affects: list[Affect]) -> None: ...
    @overload
    def receive(self, mobsChasingYou: MobsChasingYou) -> None: ...
    @overload
    def receive(self, boatTimerUpdate: BoatTimerNotification) -> None: ...
    @overload
    def receive(self, captainInRoom: BoatCaptainInRoom) -> None: ...

    def receive(self, input):
        '''
        Receives an input line, and adds it to the processing queue.

        Empty lines are ignored.
        '''
        if isinstance(input, str) and not input.strip():
            return

        self.last_received = input
        self._add_to_queue(input)

    def _add_to_queue(self, cleaned_input: str | Any):
        self._queue.append(cleaned_input)

    def dequeue(self) -> str | Any:
        removed = self._queue.popleft() if self._queue else None
        return removed
    
    def get_last_received(self) -> str | Any:
        return self.last_received
