import time
from Wingman.core.input_receiver import InputReceiver
from Wingman.core.group import Group

class GameSession:
    def __init__(self, receiver: InputReceiver):
        self.receiver = receiver
        self.total_xp = 0
        self.start_time = time.time()

        # --- PAUSE STATE ---
        self.pause_start_time = None  # Timestamp of when we hit "Pause"
        self.total_paused_duration = 0  # Total accumulated seconds spent paused
        
        # New: Store the latest snapshot of group members
        self.group = Group()

    # --- NEW: Time Calculation Helper ---
    def get_active_duration(self):
        """
        Returns the number of seconds the session has been 'active'.
        Formula: (Now - Start) - (Total Time Spent Paused)
        """
        now = time.time()

        # If we are currently paused, we "freeze" the end time at the moment we paused.
        if self.pause_start_time:
            total_elapsed = self.pause_start_time - self.start_time
        else:
            total_elapsed = now - self.start_time

        # Subtract all the previous chunks of time we were paused
        active_time = total_elapsed - self.total_paused_duration
        return max(0, active_time)

    # --- NEW: Pause Controls ---
    def pause_clock(self):
        """Freezes the timer."""
        if self.pause_start_time is None:
            self.pause_start_time = time.time()

    def resume_clock(self):
        """Unfreezes the timer and adds the elapsed time to the deduction total."""
        if self.pause_start_time:
            time_spent_paused = time.time() - self.pause_start_time
            self.total_paused_duration += time_spent_paused
            self.pause_start_time = None

    def get_xp_per_hour(self):
        if self.total_xp == 0: return 0

        # Use our new helper that accounts for pause time
        elapsed_seconds = self.get_active_duration()

        if elapsed_seconds < 1: return 0
        hours = elapsed_seconds / 3600
        return int(self.total_xp / hours)

    def reset(self):
        self.total_xp = 0
        self.start_time = time.time()
        self.group.Disband()

        # Reset pause data so we don't start with negative time or stuck pauses
        self.pause_start_time = None
        self.total_paused_duration = 0

    def get_duration_str(self):
        # Use our new helper so the visual clock stops ticking when paused
        elapsed = int(self.get_active_duration())

        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"

