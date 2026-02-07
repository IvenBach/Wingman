import tkinter as tk
import re
import time
from Wingman.core.group import Group
from Wingman.core.input_receiver import InputReceiver
from Wingman.core.session import GameSession
from Wingman.core.network_listener import NetworkListener
from Wingman.core.model import Model
from Wingman.core.parser import Parser, MobMovement
from Wingman.core.mobs_in_room import MobsInRoom

class Controller:
    def __init__(self, model: Model, view):
        from Wingman.gui.view import View #TODO: Confirm whether valid workaround for circular import
        assert isinstance(view, View)
        self.model = model
        self.view = view
        
        # Create the SHARED receiver
        self.receiver = InputReceiver()
        self.listener = NetworkListener(self.receiver, self) # Pass it to both
        
        self.gameSession = GameSession(self.receiver)

        self.listener.start()
    
    @classmethod
    def ForTesting(cls) -> 'Controller':
        """Instantiates all the dependency prerequisites, in the proper order to avoid `AttributeError`s from occurring.
```
m = Model(Parser())
v = View(tk.Tk())
c = Controller(m, v)

v.set_controller(c)
v._setup_ui()
```

:returns: An instance of Controller with all dependencies set up for testing.
:rtype: `Controller`
        """
        from Wingman.gui.view import View #To avoid circular import
        m = Model(Parser())
        # https://stackoverflow.com/questions/26097811/image-pyimage2-doesnt-exist
        # `tk.Toplevel()` is used instead of `tk.Tk()` to prevent multiple root windows
        # from being created during tests, which leads to `TclError`s.
        v = View(tk.Toplevel()) # https://tkdocs.com/shipman/toplevel.html
        c = Controller(m, v)
        
        v.set_controller(c)
        v.setup_ui()
        
        return c
        
    def reset_stats(self):
        self.view.reset_stats()
    
    def process_queue(self):
        """
        Dequeues items, calculates XP, and parses Group stats.
        Returns a list of text logs for the GUI.
        """
        logs = []

        def needToClearGroupData(line: str, group: Group) -> bool:
            # --- Logic 1: Group Detection ---
            # If we see "Someone's group:", we assume a fresh list is coming.
            # We clear the current data so we don't hold onto stale members.

            # OLD:
            # if "group:" in line and re.search(r"^\S+'s group:", line):

            # NEW: Remove the '^' to allow timestamps before the name
            if "group:" in line and re.search(r"\S+'s group:", line):
                return True
            
            if "You disband from " in line:
                return True

            leader = group.Leader
            if leader is None:
                return False
            if self.model.parser.parse_has_group_leader_disbanded_party(line, group):
                return True

            return False

        # Process everything currently in the stack
        while True:
            line = self.receiver.dequeue()
            if line is None:
                break
            
            if isinstance(line, MobsInRoom):
                self.model.currentMobsInRoom = line.mobs_in_room
                self.view.displayOrUpdateMobCountInRoom()
                continue

            if needToClearGroupData(line, self.gameSession.group):
                self.gameSession.group.Disband()

            # Check for member rows in this line
            found_members = self.model.parser.parse_group_status(line)
            if found_members:
                # Add found members to our "dashboard" list
                self.gameSession.group.AddMembers(found_members)
            
            leavingMembers = self.model.parser.parse_leaveGroup(line)
            if leavingMembers:
                self.gameSession.group.RemoveMembers(leavingMembers)

            # --- Logic 2: XP Detection ---
            xp_gain = self.model.parser.parse_xp_message(line)
            if xp_gain > 0:
                # Optional: You could check if self.pause_start_time is None here
                # if you want to ignore XP gained while paused, though the UI
                # usually stops calling process_queue anyway.
                print(f"DEBUG: XP FOUND: {xp_gain}")
                self.gameSession.total_xp += xp_gain
                timestamp = time.strftime("%H:%M:%S", time.localtime())
                log_entry = f"[{timestamp}] +{xp_gain:,} XP"
                logs.append(log_entry)

            afkRelated = self.model.parser.parseAfkStatus(line)
            match afkRelated:
                case True:
                    self.model.isAfk = True
                case False:
                    self.model.isAfk = False
                    # Method invoked here since moving while AFK will 
                    # immediately overwrite the models state of `False` 
                    # with `None`, before the view can update the gui for the user to see.
                    self.view.hideAfkLabel()
                case _:
                    self.model.isAfk = None

            meditationRelated = self.model.parser.parseMeditation(line)
            match meditationRelated:
                case True:
                    self.model.isMeditating = True
                    self.model.meditationRegenDisplay.resetMeditationStartTime()
                    self.view.displayMeditationLabel()
                case False:
                    self.model.isMeditating = False
                    self.view.hideMeditationLabel()
                case _:
                    self.model.isMeditating = None

            hidingRelated = self.model.parser.parseHideStatus(line)
            match hidingRelated:
                case True:
                    self.model.isHiding = True
                    self.view.displayHidingLabel()
                case False:
                    self.model.isHiding = False
                    self.view.hideHidingLabel()
                case _:
                    self.model.isHiding = None

            if self.model.parser.ParseMovement().playerMovement(line):
                self.clearMobsInRoom()
                self.hideMobCountInRoom()

            mobMovementRelated, movement, mobName = self.model.parser.ParseMovement().mobRelatedMovement(line, self.model.currentMobsInRoom)
            if mobMovementRelated:
                match movement:
                    case MobMovement.ENTERING:
                        self.model.currentMobsInRoom.append(mobName)
                        self.view.displayOrUpdateMobCountInRoom()
                    case MobMovement.LEAVING:
                        self.model.currentMobsInRoom.remove(mobName)
                        self.view.displayOrUpdateMobCountInRoom()
            
        return logs
    
    def clearMobsInRoom(self):
        self.model.currentMobsInRoom.clear()
    
    def hideMobCountInRoom(self):
        self.view.hideMobCountInRoom()