import tkinter as tk
import re
import time
import configparser
from pathlib import Path
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
        self.model.meditationDisplay.attach(self)
        self.view = view
        
        # Create the SHARED receiver
        self.receiver = InputReceiver()
        self.listener = NetworkListener(self.receiver, self) # Pass it to both
        
        self.gameSession = GameSession(self.receiver)

        self.listener.start()

        self._SETTINGS_FILE_NAME = 'WingmanSettings.ini'
        self._VIEW_SETTINGS = 'ViewSettings'
        self._APP_SETTINGS = 'AppSettings'
        self._IGNORED_MOB_PETS_CSV__OPTION = 'IgnoredMobsPetsCsv'
        self._DISPLAY_PETS_IN_GROUP__OPTION = 'DisplayPetsInGroup'
        self._ALWAYS_ON_TOP__OPTION = 'AlwaysOnTop'
        self._DARK_MODE__OPTION = 'DarkMode'
        self._ROOT_WINDOW_POSITION__OPTION = 'RootWindowPosition'
        self._IGNORED_MOBS_WINDOW_POSITION__OPTION = 'IgnoredMobsWindowPosition'

    @classmethod
    def ForTesting(cls, m: Model | None = None, view = None) -> 'Controller':
        """Instantiates all the dependency prerequisites, in the proper order to avoid `AttributeError`s from occurring.
```
m = Model(Parser())
v = View(tk.Toplevel())
c = Controller(m, v)

v.set_controller(c)
v.setup_ui()
```

:returns: An instance of Controller with all dependencies set up for testing.
:rtype: `Controller`
        """
        from Wingman.gui.view import View #To avoid circular import
        m = m or Model(Parser())
        # https://stackoverflow.com/questions/26097811/image-pyimage2-doesnt-exist
        # `tk.Toplevel()` is used instead of `tk.Tk()` to prevent multiple root windows
        # from being created during tests, which leads to `TclError`s.
        v = view or View(tk.Toplevel()) # https://tkdocs.com/shipman/toplevel.html
        c = Controller(m, v)
        
        v.set_controller(c)
        v.setup_ui()
        
        return c
        
    def reset_stats(self):
        self.view.reset_stats()
    
    def process_queue(self):
        """
        Dequeues items (alters state as needed), calculates XP, and parses Group stats.
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
                self.updateMobCountInRoom()
                continue

            assert isinstance(line, str)
            if needToClearGroupData(line, self.gameSession.group):
                self.gameSession.group.Disband()

            # Check for member rows in this line
            found_members = self.model.parser.parse_group_status(line, self.model.includePetsInGroup)
            if found_members:
                # Add found members to our "dashboard" list
                self.gameSession.group.AddMembers(found_members)
            
            leavingMembers = self.model.parser.parse_leaveGroup(line)
            if leavingMembers:
                self.gameSession.group.RemoveMembers(leavingMembers)

            # --- Logic 2: XP Detection ---
            xp_gain = self.model.parser.parse_xp_message(line)
            if xp_gain > 0:
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

            isMeditationRelated, meditationState  = self.model.parser.parseMeditation(line)
            match isMeditationRelated:
                case True:
                    self.model.isMeditating = True
                    self.model.meditationDisplay.resetMeditationStartTime()
                case False:
                    self.model.isMeditating = False

                    if meditationState == Parser.MeditationState.Termination_ByFullPower:
                        self.displayFullPowerLabel()
                case None:
                    pass

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
                self.clearCountOfMobsInRoom()
                self.updateMobCountInRoom()

            mobMovementRelated, movement, mobName = self.model.parser.ParseMovement().mobRelatedMovement(line, self.model.currentMobsInRoom)
            if mobMovementRelated:
                assert isinstance(mobName, str)
                match movement:
                    case MobMovement.ENTERING:
                        self.model.currentMobsInRoom.append(mobName)
                        self.updateMobCountInRoom()
                    case MobMovement.LEAVING:
                        self.model.currentMobsInRoom.remove(mobName)
                        self.updateMobCountInRoom()
            
            isBuffOrShieldRefreshing, whatEnded = self.model.parser.parseBuffOrShieldIsRefreshing(line)
            if isBuffOrShieldRefreshing == False:
                self.model.BuffOrShieldEnding = whatEnded

            isSpellMitigationAffect, mitigatingAffect = self.model.parser.parseSpellMitigationAffect(line)
            if isSpellMitigationAffect and mitigatingAffect is not None:
                self.view.displaySpellMitigatesAffectLabel(mitigatingAffect)
        return logs

    def updateMeditationDisplayValue(self):
        '''Method used to inform subscribers of `MeditationDisplay.attach(...)` that a change has occurred.'''
        self.view.var_meditationRegenDisplay.set(self.model.meditationDisplay.displayValue())

    def displayFullPowerLabel(self):
        self.view.displayFullPowerLabel()
    def hideFullPowerLabel(self):
        self.view.hideFullPowerLabel()

    def clearCountOfMobsInRoom(self):
        self.model.currentMobsInRoom.clear()
    
    def open_ignore_mobs_window(self):
        self.view.open_pet_or_mobs_display_settings_window()
    
    def updateIgnoredMobsPets(self, csvMobList: str):
        self.clearIgnoredMobsPets()

        if csvMobList == '':    
            return
        
        values = csvMobList.split(',')
        self.model.ignoreTheseMobsInCurrentRoom.extend(value.strip() for value in values)
    
    def clearIgnoredMobsPets(self):
        self.model.ignoreTheseMobsInCurrentRoom.clear()
    
    def updateMobsInCurrentRoom(self):
        for mob in self.model.ignoreTheseMobsInCurrentRoom:
            if mob in self.model.currentMobsInRoom:
                self.model.currentMobsInRoom.remove(mob)
    
    def updateMobCountInRoom(self):
        self.view.updateMobCountInRoom()
    
    def saveSettings(self):
        cp = configparser.ConfigParser()
        cp[self._VIEW_SETTINGS] = {
            self._ALWAYS_ON_TOP__OPTION: str(self.view.var_always_on_top.get()),
            self._DARK_MODE__OPTION: str(self.view.dark_mode),
            self._IGNORED_MOB_PETS_CSV__OPTION: self.view.ignoredMobsPetsCsv.get(),
            self._DISPLAY_PETS_IN_GROUP__OPTION: str(self.model.includePetsInGroup)
        }

        cp[self._APP_SETTINGS] = {
            self._ROOT_WINDOW_POSITION__OPTION: '+' + self.view.parent.geometry().split('+', 1)[1],
            self._IGNORED_MOBS_WINDOW_POSITION__OPTION: '+' + self.view._pet_or_mobs_display_settings_window.geometry().split('+', 1)[1]
        }

        srcDirectory = self.settingsFilePath()
        self._writeSettingsToFile(cp, srcDirectory, self._SETTINGS_FILE_NAME)
    
    def settingsFilePath(self) -> Path:
        return Path(__file__).parent.parent.resolve()

    def _writeSettingsToFile(self, 
                            configParser: configparser.ConfigParser, 
                            filePath: Path, 
                            fileName: str):
        fullPath = filePath.joinpath(fileName).resolve()
        with open(fullPath, 'w') as f:
            configParser.write(f)
    
    def loadSettings(self) -> configparser.ConfigParser:
        cp = configparser.ConfigParser()
        cp.read(self.settingsFilePath().joinpath(self._SETTINGS_FILE_NAME))
        return cp
        
    def applySettings(self, configParser: configparser.ConfigParser):       
        try:
            if configParser.has_section(self._VIEW_SETTINGS):
                ignoredMobsPetsCsv = configParser.get(self._VIEW_SETTINGS, self._IGNORED_MOB_PETS_CSV__OPTION, fallback='')
                self.view.var_ignoredMobPetsCsv.set(ignoredMobsPetsCsv)
                self.updateIgnoredMobsPets(ignoredMobsPetsCsv)

                darkModeSavedSetting = configParser.getboolean(self._VIEW_SETTINGS, self._DARK_MODE__OPTION, fallback=False)
                if darkModeSavedSetting != False:
                    self.view.toggle_theme()

                displayPetsInGroup = configParser.getboolean(self._VIEW_SETTINGS, self._DISPLAY_PETS_IN_GROUP__OPTION, fallback=False)
                self.view.var_includePetsInGroup.set(displayPetsInGroup)
                self.model.includePetsInGroup = displayPetsInGroup

                isAlwaysOnTop = configParser.getboolean(self._VIEW_SETTINGS, self._ALWAYS_ON_TOP__OPTION, fallback=False)
                self.view.apply_topmost(isAlwaysOnTop)

            if configParser.has_section(self._APP_SETTINGS):
                rootWindowSize = self.view.parent.geometry().split('+')[0]
                rootWindowPosition = configParser.get(self._APP_SETTINGS, self._ROOT_WINDOW_POSITION__OPTION, fallback='+50+50')
                self.view.parent.geometry(rootWindowSize + rootWindowPosition)

                petOrMobDisplaySettingsWindowSize = self.view._pet_or_mobs_display_settings_window.geometry().split('+')[0]
                petOrMobDisplaySettingsWindowPosition = configParser.get(self._APP_SETTINGS, self._IGNORED_MOBS_WINDOW_POSITION__OPTION, fallback='+50+50')
                self.view._pet_or_mobs_display_settings_window.geometry(petOrMobDisplaySettingsWindowSize + petOrMobDisplaySettingsWindowPosition)
            
        except KeyError:
            # This means the config file was missing or malformed. We can choose to ignore this and just use defaults.
            with open(self.settingsFilePath().joinpath('No settings file.txt'), 'w') as f:
                f.write("No settings file found or failed to load. Default settings have been used.\n")
                f.write(f"This file can be deleted if a `{self._SETTINGS_FILE_NAME}` file exists in the same folder.\n")
        
    def update_display_of_pets_in_group_window(self, displayMobsInGroupWindow: bool):
        """
        Updates displayed members in the group. A `False` value will remove any pets from the group.
        """
        self.model.includePetsInGroup = displayMobsInGroupWindow
        if not displayMobsInGroupWindow:
            # If we're toggling off the display of pets/mobs in the group window, we need to remove any that are currently being displayed.
            self.gameSession.group.RemoveMembers([member for member in self.gameSession.group.Members if member.Class_ == 'mob'])
