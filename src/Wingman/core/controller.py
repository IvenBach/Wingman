import tkinter as tk
from tkinter import ttk, messagebox
import re
import time
import configparser
from pathlib import Path
from typing import Iterable
from Wingman.core.affect import Affect
from Wingman.core.group import Group
from Wingman.core.session import GameSession
from Wingman.core.network_listener import NetworkListener
from Wingman.core.model import Model
from Wingman.core.parser import Parser, MobMovement
from Wingman.core.mobs_in_room import MobsInRoom
from Wingman.core.item import Item, ItemSlot, QuantityComparer
from Wingman.core.inventory import Inventory, Equipment

class Controller:
    def __init__(self, model: Model, view, listener_target_ip='18.119.153.121', listener_target_port=4000):
        from Wingman.gui.view import View # Avoid circular import issues by importing here
        assert isinstance(view, View)
        self.model = model
        self.model.meditationDisplay.attach(self)
        self.view = view

        # Create the SHARED receiver
        from Wingman.core.input_receiver import InputReceiver # Avoid circular import issues by importing here
        self.receiver = InputReceiver(self)
        self.listener = NetworkListener(self.receiver, self, listener_target_ip, listener_target_port) # Pass it to both

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
        self._MISCELLANEOUS_SETTINGS_WINDOW_POSITION__OPTION = 'IgnoredMobsWindowPosition'
        self._GEAR_SETS_WINDOW_POSITION__OPTION = 'GearSetsWindowPosition'
        self._SUPPLY_CHECKER_WINDOW_POSITION__OPTION = 'CheckSuppliesWindowPosition'
        self._PVP_SUPPLIES_TEXT__OPTION = 'PvpSuppliesText'
        self._PVE_SUPPLIES_TEXT__OPTION = 'PveSuppliesText'
        #region GearSet related options
        self._GEAR_SETS_LAST_ACTIVE_TAB_INDEX__OPTION = 'GearSetsLastActiveTab'
        #Pvp
        self._PVP_GEAR_SET_HEAD__OPTION = 'PvpGearSetHead'
        self._PVP_GEAR_SET_JEWEL1__OPTION = 'PvpGearSetJewel1'
        self._PVP_GEAR_SET_JEWEL2__OPTION = 'PvpGearSetJewel2'
        self._PVP_GEAR_SET_CLOAK__OPTION = 'PvpGearSetCloak'
        self._PVP_GEAR_SET_BODY__OPTION = 'PvpGearSetBody'
        self._PVP_GEAR_SET_HANDS__OPTION = 'PvpGearSetHands'
        self._PVP_GEAR_SET_LEGS__OPTION = 'PvpGearSetLegs'
        self._PVP_GEAR_SET_FEET__OPTION = 'PvpGearSetFeet'
        self._PVP_GEAR_SET_HELD_RIGHT__OPTION = 'PvpGearSetHeldRight'
        self._PVP_GEAR_SET_HELD_LEFT__OPTION = 'PvpGearSetHeldLeft'
        #Pve
        self._PVE_GEAR_SET_HEAD__OPTION = 'PveGearSetHead'
        self._PVE_GEAR_SET_JEWEL1__OPTION = 'PveGearSetJewel1'
        self._PVE_GEAR_SET_JEWEL2__OPTION = 'PveGearSetJewel2'
        self._PVE_GEAR_SET_CLOAK__OPTION = 'PveGearSetCloak'
        self._PVE_GEAR_SET_BODY__OPTION = 'PveGearSetBody'
        self._PVE_GEAR_SET_HANDS__OPTION = 'PveGearSetHands'
        self._PVE_GEAR_SET_LEGS__OPTION = 'PveGearSetLegs'
        self._PVE_GEAR_SET_FEET__OPTION = 'PveGearSetFeet'
        self._PVE_GEAR_SET_HELD_RIGHT__OPTION = 'PveGearSetHeldRight'
        self._PVE_GEAR_SET_HELD_LEFT__OPTION = 'PveGearSetHeldLeft'
        #endregion
        self._ACTIVE_SUPPLIES_TAB__OPTION = 'ActiveSuppliesTab'
        self._HIDE_DISPLAYED_LABEL_CALLBACK_TIMER_IN_MILLISECONDS__OPTION = 'HideDisplayedLabelCallbackTimerInMilliseconds'
        self._HIDE_DISPLAYED_LABEL_CALLBACK_TIMER_IN_MILLISECONDS__FALLBACK = 2000
        self._ALERT_FOR_SPELL_DROPPING_DURATION_IN_MINUTES__OPTION = "AlertForSpellDroppingDurationInMinutes"
        self._ALERT_FOR_SPELL_DROPPING_DURATION_IN_MINUTES__FALLBACK = 5
        self._SOUGHT_AFTER_ITEMS__OPTION = "SoughtAfterItems"

    @classmethod
    def ForTesting(cls, m: Model | None = None, view = None, listener_target_ip='1.2.3.4', listener_target_port=1234) -> 'Controller':
        """Instantiates all the dependency prerequisites, in the proper order to avoid `AttributeError`s from occurring.
```
m = Model(Parser())
v = View(tk.Toplevel())
c = Controller(m, v, listener_target_ip, listener_target_port)

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
        c = Controller(m, v, listener_target_ip, listener_target_port)

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

        # Process everything currently in the queue
        while True:
            line = self.receiver.dequeue()
            if line is None:
                break

            if isinstance(line, MobsInRoom):
                self.model.currentMobsInRoom = line.mobs_in_room
                self.updateMobCountDisplay()
                continue

            if isinstance(line, Inventory):
                self.model.inventory = line
                continue

            if isinstance(line, Equipment):
                self.model.inventory.EquippedGear_ = line
                continue

            if isinstance(line, list) and len(line) > 0 and isinstance(line[0], Affect):
                affectsWithTimeExpiration = [affect for affect in line\
                                             if isinstance(affect, Affect) and affect.DurationEndsAt is not None]
                if affectsWithTimeExpiration:
                    self.hideAffectSpellDropWarningLabel()

                self.model.AffectsWithTimeExpiration = affectsWithTimeExpiration
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

            isMobDroppedItem, droppedItem = self.model.parser.parseMobDroppedItem(line)
            if isMobDroppedItem and droppedItem is not None:
                if self.IsLookingForItem(droppedItem.Name):
                    self.model.SoughtAfterItemsThatDropped.append(droppedItem.Name)

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
                self.updateMobCountDisplay()
                self.clearSoughtAfterItemsThatDropped()

            mobMovementRelated, movement, mobName = self.model.parser.ParseMovement().mobRelatedMovement(line, self.model.currentMobsInRoom)
            if mobMovementRelated:
                assert isinstance(mobName, str)
                match movement:
                    case MobMovement.ENTERING:
                        self.model.currentMobsInRoom.append(mobName)
                        self.updateMobCountDisplay()
                    case MobMovement.LEAVING:
                        self.model.currentMobsInRoom.remove(mobName)
                        self.updateMobCountDisplay()

            isBuffOrShieldRefreshing, whatEnded = self.model.parser.parseBuffOrShieldIsRefreshing(line)
            if isBuffOrShieldRefreshing == False:
                self.model.BuffOrShieldEnding = whatEnded

            isSpellMitigationAffect, mitigatingAffect = self.model.parser.parseSpellMitigationAffect(line)
            if isSpellMitigationAffect and mitigatingAffect is not None:
                self.view.displaySpellMitigatesAffectLabel(mitigatingAffect)
        return logs

    def IsLookingForItem(self, itemName: str) -> bool:
        return itemName in self.model.SoughtAfterItems

    def updateMeditationDisplayValue(self):
        '''Method used to inform subscribers of `MeditationDisplay.attach(...)` that a change has occurred.'''
        self.view.var_meditationRegenDisplay.set(self.model.meditationDisplay.displayValue())

    def displayFullPowerLabel(self):
        self.view.displayFullPowerLabel()
    def hideFullPowerLabel(self):
        self.view.hideFullPowerLabel()

    def clearCountOfMobsInRoom(self):
        self.model.currentMobsInRoom.clear()
    
    def open_miscellaneousSettings_window(self):
        self.view.open_pet_or_mobs_display_settings_window()
    
    def updateIgnoredMobsPets(self, csvMobList: str):
        self.clearIgnoredMobsPets()

        if csvMobList == '':
            return

        values = csvMobList.split(',')
        self.model.ignoreTheseMobsInCurrentRoom.extend(value.strip() for value in values)

    def clearIgnoredMobsPets(self):
        self.model.ignoreTheseMobsInCurrentRoom.clear()

    def removedIgnoredMobsFromCurrentRoom(self):
        for ignoreMob in self.model.ignoreTheseMobsInCurrentRoom:
            if ignoreMob in self.model.currentMobsInRoom:
                self.model.currentMobsInRoom.remove(ignoreMob)

    def updateMobCountDisplay(self):
        self.view.updateMobCountDisplay()

    def saveSettings(self):
        activeGearSetTabText = self.activeTabTextInNotebook(self.view.gearSetsNotebook)
        activeGearSetTabIndex = [index for index, tabIdentifier in enumerate(self.view.gearSetsNotebook.tabs())
            if self.view.gearSetsNotebook.tab(tabIdentifier, "text") == activeGearSetTabText][0]

        cp = configparser.ConfigParser()
        cp[self._VIEW_SETTINGS] = {
            self._ALWAYS_ON_TOP__OPTION: str(self.view.var_always_on_top.get()),
            self._DARK_MODE__OPTION: str(self.view.dark_mode),
            self._IGNORED_MOB_PETS_CSV__OPTION: self.view.ignoredMobsPetsCsv.get(),
            self._DISPLAY_PETS_IN_GROUP__OPTION: str(self.model.includePetsInGroup),
            self._PVP_SUPPLIES_TEXT__OPTION: str(self.view.pvpSuppliesText.get("1.0", tk.END)),
            self._PVE_SUPPLIES_TEXT__OPTION: str(self.view.pveSuppliesText.get("1.0", tk.END)),
            self._ACTIVE_SUPPLIES_TAB__OPTION: str(self.view.suppliesNotebook.select()),
            self._SOUGHT_AFTER_ITEMS__OPTION: self.view.var_soughtAfterItems.get(),

            #region GearSets
            self._GEAR_SETS_LAST_ACTIVE_TAB_INDEX__OPTION: str(activeGearSetTabIndex),

            self._PVE_GEAR_SET_HEAD__OPTION: self.view.gearSetsPveHeadEntry.get(),
            self._PVE_GEAR_SET_JEWEL1__OPTION: self.view.gearSetsPveJewel1Entry.get(),
            self._PVE_GEAR_SET_JEWEL2__OPTION: self.view.gearSetsPveJewel2Entry.get(),
            self._PVE_GEAR_SET_CLOAK__OPTION: self.view.gearSetsPveCloakEntry.get(),
            self._PVE_GEAR_SET_BODY__OPTION: self.view.gearSetsPveBodyEntry.get(),
            self._PVE_GEAR_SET_HANDS__OPTION: self.view.gearSetsPveHandsEntry.get(),
            self._PVE_GEAR_SET_LEGS__OPTION: self.view.gearSetsPveLegsEntry.get(),
            self._PVE_GEAR_SET_FEET__OPTION: self.view.gearSetsPveFeetEntry.get(),
            self._PVE_GEAR_SET_HELD_RIGHT__OPTION: self.view.gearSetsPveHeldRightEntry.get(),
            self._PVE_GEAR_SET_HELD_LEFT__OPTION: self.view.gearSetsPveHeldLeftEntry.get(),

            self._PVP_GEAR_SET_HEAD__OPTION: self.view.gearSetsPvpHeadEntry.get(),
            self._PVP_GEAR_SET_JEWEL1__OPTION: self.view.gearSetsPvpJewel1Entry.get(),
            self._PVP_GEAR_SET_JEWEL2__OPTION: self.view.gearSetsPvpJewel2Entry.get(),
            self._PVP_GEAR_SET_CLOAK__OPTION: self.view.gearSetsPvpCloakEntry.get(),
            self._PVP_GEAR_SET_BODY__OPTION: self.view.gearSetsPvpBodyEntry.get(),
            self._PVP_GEAR_SET_HANDS__OPTION: self.view.gearSetsPvpHandsEntry.get(),
            self._PVP_GEAR_SET_LEGS__OPTION: self.view.gearSetsPvpLegsEntry.get(),
            self._PVP_GEAR_SET_FEET__OPTION: self.view.gearSetsPvpFeetEntry.get(),
            self._PVP_GEAR_SET_HELD_RIGHT__OPTION: self.view.gearSetsPvpHeldRightEntry.get(),
            self._PVP_GEAR_SET_HELD_LEFT__OPTION: self.view.gearSetsPvpHeldLeftEntry.get(),
            #endregion
        }

        cp[self._APP_SETTINGS] = {
            self._ROOT_WINDOW_POSITION__OPTION: '+' + self.view.root.geometry().split('+', 1)[1],
            self._MISCELLANEOUS_SETTINGS_WINDOW_POSITION__OPTION: '+' + self.view._miscellaneousSettings.geometry().split('+', 1)[1],
            self._SUPPLY_CHECKER_WINDOW_POSITION__OPTION: '+' + self.view._supplyCheckerWindow.geometry().split('+', 1)[1],
            self._GEAR_SETS_WINDOW_POSITION__OPTION: '+' + self.view._gearSetsWindow.geometry().split('+', 1)[1],
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
        def applyGearSets(self: Controller):
                lastActiveTab = configParser.get(self._VIEW_SETTINGS, self._GEAR_SETS_LAST_ACTIVE_TAB_INDEX__OPTION, fallback='0')
                self.view.gearSetsNotebook.select(lastActiveTab)

                pvpHead = configParser.get(self._VIEW_SETTINGS, self._PVP_GEAR_SET_HEAD__OPTION, fallback='')
                self.view.gearSetsPvpHeadEntry.insert(0, pvpHead)
                pvpJewel1 = configParser.get(self._VIEW_SETTINGS, self._PVP_GEAR_SET_JEWEL1__OPTION, fallback='')
                self.view.gearSetsPvpJewel1Entry.insert(0, pvpJewel1)
                pvpJewel2 = configParser.get(self._VIEW_SETTINGS, self._PVP_GEAR_SET_JEWEL2__OPTION, fallback='')
                self.view.gearSetsPvpJewel2Entry.insert(0, pvpJewel2)
                pvpCloak = configParser.get(self._VIEW_SETTINGS, self._PVP_GEAR_SET_CLOAK__OPTION, fallback='')
                self.view.gearSetsPvpCloakEntry.insert(0, pvpCloak)
                pvpBody = configParser.get(self._VIEW_SETTINGS, self._PVP_GEAR_SET_BODY__OPTION, fallback='')
                self.view.gearSetsPvpBodyEntry.insert(0, pvpBody)
                pvpHands = configParser.get(self._VIEW_SETTINGS, self._PVP_GEAR_SET_HANDS__OPTION, fallback='')
                self.view.gearSetsPvpHandsEntry.insert(0, pvpHands)
                pvpLegs = configParser.get(self._VIEW_SETTINGS, self._PVP_GEAR_SET_LEGS__OPTION, fallback='')
                self.view.gearSetsPvpLegsEntry.insert(0, pvpLegs)
                pvpFeet = configParser.get(self._VIEW_SETTINGS, self._PVP_GEAR_SET_FEET__OPTION, fallback='')
                self.view.gearSetsPvpFeetEntry.insert(0, pvpFeet)
                pvpHeldRight = configParser.get(self._VIEW_SETTINGS, self._PVP_GEAR_SET_HELD_RIGHT__OPTION, fallback='')
                self.view.gearSetsPvpHeldRightEntry.insert(0, pvpHeldRight)
                pvpHeldLeft = configParser.get(self._VIEW_SETTINGS, self._PVP_GEAR_SET_HELD_LEFT__OPTION, fallback='')
                self.view.gearSetsPvpHeldLeftEntry.insert(0, pvpHeldLeft)

                pveHead = configParser.get(self._VIEW_SETTINGS, self._PVE_GEAR_SET_HEAD__OPTION, fallback='')
                self.view.gearSetsPveHeadEntry.insert(0, pveHead)
                pveJewel1 = configParser.get(self._VIEW_SETTINGS, self._PVE_GEAR_SET_JEWEL1__OPTION, fallback='')
                self.view.gearSetsPveJewel1Entry.insert(0, pveJewel1)
                pveJewel2 = configParser.get(self._VIEW_SETTINGS, self._PVE_GEAR_SET_JEWEL2__OPTION, fallback='')
                self.view.gearSetsPveJewel2Entry.insert(0, pveJewel2)
                pveCloak = configParser.get(self._VIEW_SETTINGS, self._PVE_GEAR_SET_CLOAK__OPTION, fallback='')
                self.view.gearSetsPveCloakEntry.insert(0, pveCloak)
                pveBody = configParser.get(self._VIEW_SETTINGS, self._PVE_GEAR_SET_BODY__OPTION, fallback='')
                self.view.gearSetsPveBodyEntry.insert(0, pveBody)
                pveHands = configParser.get(self._VIEW_SETTINGS, self._PVE_GEAR_SET_HANDS__OPTION, fallback='')
                self.view.gearSetsPveHandsEntry.insert(0, pveHands)
                pveLegs = configParser.get(self._VIEW_SETTINGS, self._PVE_GEAR_SET_LEGS__OPTION, fallback='')
                self.view.gearSetsPveLegsEntry.insert(0, pveLegs)
                pveFeet = configParser.get(self._VIEW_SETTINGS, self._PVE_GEAR_SET_FEET__OPTION, fallback='')
                self.view.gearSetsPveFeetEntry.insert(0, pveFeet)
                pveHeldRight = configParser.get(self._VIEW_SETTINGS, self._PVE_GEAR_SET_HELD_RIGHT__OPTION, fallback='')
                self.view.gearSetsPveHeldRightEntry.insert(0, pveHeldRight)
                pveHeldLeft = configParser.get(self._VIEW_SETTINGS, self._PVE_GEAR_SET_HELD_LEFT__OPTION, fallback='')
                self.view.gearSetsPveHeldLeftEntry.insert(0, pveHeldLeft)

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

                pvpSuppliesText = configParser.get(self._VIEW_SETTINGS, self._PVP_SUPPLIES_TEXT__OPTION, fallback='')
                self.view.pvpSuppliesText.insert("1.0", pvpSuppliesText)
                pveSuppliesText = configParser.get(self._VIEW_SETTINGS, self._PVE_SUPPLIES_TEXT__OPTION, fallback='')
                self.view.pveSuppliesText.insert("1.0", pveSuppliesText)
                activeTabIdentifier = configParser.get(self._VIEW_SETTINGS, self._ACTIVE_SUPPLIES_TAB__OPTION, fallback=0)
                try:
                    self.view.suppliesNotebook.select(activeTabIdentifier)
                except tk.TclError:
                    self.view.suppliesNotebook.select(0) # Default to first tab if the saved identifier is invalid

                spellDropTimeInMinutes = configParser.getint(self._VIEW_SETTINGS,
                                                             self._ALERT_FOR_SPELL_DROPPING_DURATION_IN_MINUTES__OPTION,
                                                             fallback=self._ALERT_FOR_SPELL_DROPPING_DURATION_IN_MINUTES__FALLBACK)
                self.view.var_timeInMinutesToWarnAboutSpellsDropping.set(spellDropTimeInMinutes)

                hideDisplayCallbackTimerInMilliseconds = configParser.getint(self._VIEW_SETTINGS,
                                                                             self._HIDE_DISPLAYED_LABEL_CALLBACK_TIMER_IN_MILLISECONDS__OPTION,
                                                                             fallback=self._HIDE_DISPLAYED_LABEL_CALLBACK_TIMER_IN_MILLISECONDS__FALLBACK)
                self.view.var_hideDisplayedLabelCallbackTimerInMilliseconds.set(hideDisplayCallbackTimerInMilliseconds)

                soughtAfterItems = configParser.get(self._VIEW_SETTINGS, self._SOUGHT_AFTER_ITEMS__OPTION, fallback='')
                self.view.var_soughtAfterItems.set(soughtAfterItems)
                self.model.SoughtAfterItems = set(item.strip() for item in soughtAfterItems.split(',') if item.strip() != '')

                applyGearSets(self)

            if configParser.has_section(self._APP_SETTINGS):
                rootWindowSize = self.view.root.geometry().split('+')[0]
                rootWindowPosition = configParser.get(self._APP_SETTINGS, self._ROOT_WINDOW_POSITION__OPTION, fallback='+50+50')
                self.view.root.geometry(rootWindowSize + rootWindowPosition)

                petOrMobDisplaySettingsWindowSize = self.view._miscellaneousSettings.geometry().split('+')[0]
                petOrMobDisplaySettingsWindowPosition = configParser.get(self._APP_SETTINGS, self._MISCELLANEOUS_SETTINGS_WINDOW_POSITION__OPTION, fallback='+50+50')
                self.view._miscellaneousSettings.geometry(petOrMobDisplaySettingsWindowSize + petOrMobDisplaySettingsWindowPosition)

                invasionSuppliesWindowSize = self.view._supplyCheckerWindow.geometry().split('+')[0]
                invasionSuppliesWindowPosition = configParser.get(self._APP_SETTINGS, self._SUPPLY_CHECKER_WINDOW_POSITION__OPTION, fallback='+50+50')
                self.view._supplyCheckerWindow.geometry(invasionSuppliesWindowSize + invasionSuppliesWindowPosition)

                gearSetsWindowSize = self.view._gearSetsWindow.geometry().split('+')[0]
                gearSetsWindowPosition = configParser.get(self._APP_SETTINGS, self._GEAR_SETS_WINDOW_POSITION__OPTION, fallback='+50+50')
                self.view._gearSetsWindow.geometry(gearSetsWindowSize + gearSetsWindowPosition)

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

    def check_invasion_supplies(self, supplyText: str, inventory: Inventory) -> list[Item]:
        """Checks the players  non-geared inventory for items that are on their invasion supplies list. The list is expected to be in a newline separated format.
Example input:
```
 ( 2) A goblet of zombie blood
 ( 4) A darkspawned blackened fish fillet
 ( 2) A bunch of restorative roots
 ( 2) A ticket to Arnak's Plague
 ( 6) A scroll of minor resurrection
```
Returns a `list[Item]` of missing items
"""
        if len(inventory.Backpack) == 0:
            return []

        missingItems: list[Item] = []
        for supplyLine in supplyText.splitlines():
            if supplyLine == '':
                continue
            supplyItem = Parser.parseQuantityItem(supplyLine)
            wasMatchFound = False
            for backpackItem in inventory.Backpack:
                if supplyItem.Name == backpackItem.Name:
                    wasMatchFound = True
                    if backpackItem.QuantityComparison(supplyItem) == QuantityComparer.LESS_THAN:
                        delta = supplyItem.subtract(backpackItem) # Swapped variable order ensures positive delta
                        missingItems.append(Item(supplyItem.Name, quantity=delta))
                        break

            if not wasMatchFound:
                missingItems.append(supplyItem)

        return missingItems

    def suppliesTextFromTab(self, tabIdentifier: str) -> str:
        if tabIdentifier == "PvP":
            return self.view.pvpSuppliesText.get("1.0", tk.END)
        elif tabIdentifier == "PvE":
            return self.view.pveSuppliesText.get("1.0", tk.END)
        else:
            raise ValueError(f"Unexpected active tab name: {tabIdentifier}")

    def updateMissingSuppliesLabel(self, tabIndicator: str, supplyText: str, inventory: Inventory):
        if supplyText == '' or supplyText.isspace():
            self.view.updateMissingSuppliesLabel("***No supplies were checked.")
            return

        if len(inventory.Backpack) == 0:
            self.view.updateMissingSuppliesLabel("***Empty backpack cache. Execute `Inventory` then check again.")
            return

        missingSupplies = self.check_invasion_supplies(supplyText, inventory)
        self.view.updateMissingSuppliesLabel(tabIndicator, missingSupplies)

    def hideAffectSpellDropWarningLabel(self):
        self.view.hideAffectSpellDropWarningLabel()
    def displayAffectSpellDropWarningLabel(self, warningText: str):
        self.view.displayAffectSpellDropWarningLabel(warningText)

    def displayDropAlertLabel(self, text: str):
        self.view.displayDropAlertLabel(text)
    def hideDropAlertLabel(self):
        self.view.hideDropAlertLabel()

    def clearSoughtAfterItemsThatDropped(self):
        self.model.SoughtAfterItemsThatDropped.clear()

    def activeGearSetTabEquipment(self) -> Equipment:
        def pvpGearSetEquipment(self: Controller) -> Equipment:
            gearSet = Equipment()
            gearSet.Head = Item(self.view.gearSetsPvpHeadEntry.get(), slot=ItemSlot.HEAD)
            gearSet.Jewel1 = Item(self.view.gearSetsPvpJewel1Entry.get(), slot=ItemSlot.JEWEL)
            gearSet.Jewel2 = Item(self.view.gearSetsPvpJewel2Entry.get(), slot=ItemSlot.JEWEL)
            gearSet.Cloak = Item(self.view.gearSetsPvpCloakEntry.get(), slot=ItemSlot.CLOAK)
            gearSet.Body = Item(self.view.gearSetsPvpBodyEntry.get(), slot=ItemSlot.BODY)
            gearSet.Hands = Item(self.view.gearSetsPvpHandsEntry.get(), slot=ItemSlot.HANDS)
            gearSet.Legs = Item(self.view.gearSetsPvpLegsEntry.get(), slot=ItemSlot.LEGS)
            gearSet.Feet = Item(self.view.gearSetsPvpFeetEntry.get(), slot=ItemSlot.FEET)
            gearSet.Held_Right = Item(self.view.gearSetsPvpHeldRightEntry.get(), slot=ItemSlot.HELD)
            gearSet.Held_Left = Item(self.view.gearSetsPvpHeldLeftEntry.get(), slot=ItemSlot.HELD)
            return gearSet

        def pveGearSetEquipment(self: Controller) -> Equipment:
            gearSet = Equipment()
            gearSet.Head = Item(self.view.gearSetsPveHeadEntry.get(), slot=ItemSlot.HEAD)
            gearSet.Jewel1 = Item(self.view.gearSetsPveJewel1Entry.get(), slot=ItemSlot.JEWEL)
            gearSet.Jewel2 = Item(self.view.gearSetsPveJewel2Entry.get(), slot=ItemSlot.JEWEL)
            gearSet.Cloak = Item(self.view.gearSetsPveCloakEntry.get(), slot=ItemSlot.CLOAK)
            gearSet.Body = Item(self.view.gearSetsPveBodyEntry.get(), slot=ItemSlot.BODY)
            gearSet.Hands = Item(self.view.gearSetsPveHandsEntry.get(), slot=ItemSlot.HANDS)
            gearSet.Legs = Item(self.view.gearSetsPveLegsEntry.get(), slot=ItemSlot.LEGS)
            gearSet.Feet = Item(self.view.gearSetsPveFeetEntry.get(), slot=ItemSlot.FEET)
            gearSet.Held_Right = Item(self.view.gearSetsPveHeldRightEntry.get(), slot=ItemSlot.HELD)
            gearSet.Held_Left = Item(self.view.gearSetsPveHeldLeftEntry.get(), slot=ItemSlot.HELD)
            return gearSet

        activeTabText = self.activeTabTextInNotebook(self.view.gearSetsNotebook)
        if activeTabText == "PvP":
            return pvpGearSetEquipment(self)
        elif activeTabText == "PvE":
            return pveGearSetEquipment(self)
        else:
            raise ValueError(f"Unexpected active tab name: {activeTabText}")

    def checkGearSet(self, activeGearSetTabEquipment: Equipment, equippedGear_: Equipment):
        if Equipment.IsEmpty(equippedGear_):
            messagebox.showinfo("No equipped gear", "Execute `equipment` in the client then check again.")
            return

        missingViewItemsSet = set(activeGearSetTabEquipment.items()) - set(equippedGear_.items())
        if not missingViewItemsSet:
            self.view.displayMissingGearSetItemsLabel('')
            return

        missingItems = [f"{item.Slot}: {item.Name}" for item in Item.orderBySlot(missingViewItemsSet)]
        self.view.displayMissingGearSetItemsLabel("Missing set items:" + '\n   - ' + '\n   - '.join(missingItems))

    def sendBankWithdrawTextToClipboard(self):
        'Query the view for the active gear set tab, create a withdrawal text, and send it to the clipboard.'
        withdrawalText = self.gearSetBankWidthdrawalTextFromActiveGearSetTab()
        self.view.clipboard_clear()
        self.view.clipboard_append(withdrawalText)
        self.view.update()

    def gearSetBankWidthdrawalTextFromActiveGearSetTab(self) -> str:
        """Create a `', '` separated string from the non-empty gear fields.

        If no entries are filled, shows a `messagebox` to the user and returns an empty string."""
        tabIdentifier = self.activeTabTextInNotebook(self.view.gearSetsNotebook)
        fields = []
        if tabIdentifier == "PvP":
            fields = [self.view.gearSetsPvpHeadEntry.get(),
                      self.view.gearSetsPvpJewel1Entry.get(),
                      self.view.gearSetsPvpJewel2Entry.get(),
                      self.view.gearSetsPvpCloakEntry.get(),
                      self.view.gearSetsPvpBodyEntry.get(),
                      self.view.gearSetsPvpHandsEntry.get(),
                      self.view.gearSetsPvpLegsEntry.get(),
                      self.view.gearSetsPvpFeetEntry.get(),
                      self.view.gearSetsPvpHeldRightEntry.get(),
                      self.view.gearSetsPvpHeldLeftEntry.get()]
        elif tabIdentifier == "PvE":
            fields = [self.view.gearSetsPveHeadEntry.get(),
                      self.view.gearSetsPveJewel1Entry.get(),
                      self.view.gearSetsPveJewel2Entry.get(),
                      self.view.gearSetsPveCloakEntry.get(),
                      self.view.gearSetsPveBodyEntry.get(),
                      self.view.gearSetsPveHandsEntry.get(),
                      self.view.gearSetsPveLegsEntry.get(),
                      self.view.gearSetsPveFeetEntry.get(),
                      self.view.gearSetsPveHeldRightEntry.get(),
                      self.view.gearSetsPveHeldLeftEntry.get()]
        else:
            raise ValueError(f"Unexpected active tab name: {tabIdentifier}")

        if fields[-2] == fields[-1]: # 2handed weapon. Drop an entry
            fields[-1] = ''

        if all(field == "" for field in fields):
            messagebox.showinfo("No gear set", "Please input gear before creating a bank withdrawal text.")
            return ''

        return 'withdraw ' + ', withdraw '.join([field for field in fields if field != ""]).lower()

    def clearGearSetEntriesOnActiveTab(self):
        """Query the view for the activetab, then clear the entries on that tab."""
        tabIdentifier = self.activeTabTextInNotebook(self.view.gearSetsNotebook)
        if tabIdentifier == "PvP":
            self.view.clearPvpSetEntries()
        elif tabIdentifier == "PvE":
            self.view.clearPveSetEntries()
        else:
            raise ValueError(f"Unexpected active tab name: {tabIdentifier}")

    def activeTabTextInNotebook(self, notebook: ttk.Notebook) -> str:
            """Query the notebook for the active tab, and return the `text` of that tab.
            
            The returned text cannot be used for tab selection. Use a zero based index for that as indicated by https://docs.python.org/3/library/tkinter.ttk.html#tab-identifiers"""
            return notebook.tab(notebook.select(), "text")

    def copyPastedGearSetTextToActiveTabEntries(self, text: str):
        '''Copy the pasted text into its corresponding entry input, after clearing input fields to prevent carrying over prior equipment.
        
        If no text is pasted or no gear is worn a `messagebox` is shown to to the user.'''

        pastedFormat = """     On Head:  item1
    On Jewel:  item2
    On Jewel:  item3
    On Cloak:  item4
     On Body:  item5
    On Hands:  item6
     On Legs:  item7
     On Feet:  item8
  Held Right:  item9
   Held Left:  item9 (for 2handed or item10 for an offhand weapon/shield)"""
        message = f"Paste gear text in the format \n\n{pastedFormat}\n\n The spacing doesn't need to be exact, but the labels do."
        if text == '' or text.isspace():
            messagebox.showinfo("No pasted text", message)
            return

        eg = Parser().parseEquippedGear(text)

        if eg is None or all([eg.Head is None,
                                eg.Jewel1 is None,
                                eg.Jewel2 is None,
                                eg.Cloak is None,
                                eg.Body is None,
                                eg.Hands is None,
                                eg.Legs is None,
                                eg.Feet is None,
                                eg.Held_Right is None,
                                eg.Held_Left is None]):
            messagebox.showinfo("No gear worn", message)
            return

        tabIdentifier = self.activeTabTextInNotebook(self.view.gearSetsNotebook)
        if tabIdentifier == "PvP":
            self.view.clearPvpSetEntries()
            self.view.gearSetsPvpHeadEntry.insert(0, eg.Head if eg.Head is not None else '')
            self.view.gearSetsPvpJewel1Entry.insert(0, eg.Jewel1 if eg.Jewel1 is not None else '')
            self.view.gearSetsPvpJewel2Entry.insert(0, eg.Jewel2 if eg.Jewel2 is not None else '')
            self.view.gearSetsPvpCloakEntry.insert(0, eg.Cloak if eg.Cloak is not None else '')
            self.view.gearSetsPvpBodyEntry.insert(0, eg.Body if eg.Body is not None else '')
            self.view.gearSetsPvpHandsEntry.insert(0, eg.Hands if eg.Hands is not None else '')
            self.view.gearSetsPvpLegsEntry.insert(0, eg.Legs if eg.Legs is not None else '')
            self.view.gearSetsPvpFeetEntry.insert(0, eg.Feet if eg.Feet is not None else '')
            self.view.gearSetsPvpHeldRightEntry.insert(0, eg.Held_Right if eg.Held_Right is not None else '')
            self.view.gearSetsPvpHeldLeftEntry.insert(0, eg.Held_Left if eg.Held_Left is not None else '')
        elif tabIdentifier == "PvE":
            self.view.clearPveSetEntries()
            self.view.gearSetsPveHeadEntry.insert(0, eg.Head if eg.Head is not None else '')
            self.view.gearSetsPveJewel1Entry.insert(0, eg.Jewel1 if eg.Jewel1 is not None else '')
            self.view.gearSetsPveJewel2Entry.insert(0, eg.Jewel2 if eg.Jewel2 is not None else '')
            self.view.gearSetsPveCloakEntry.insert(0, eg.Cloak if eg.Cloak is not None else '')
            self.view.gearSetsPveBodyEntry.insert(0, eg.Body if eg.Body is not None else '')
            self.view.gearSetsPveHandsEntry.insert(0, eg.Hands if eg.Hands is not None else '')
            self.view.gearSetsPveLegsEntry.insert(0, eg.Legs if eg.Legs is not None else '')
            self.view.gearSetsPveFeetEntry.insert(0, eg.Feet if eg.Feet is not None else '')
            self.view.gearSetsPveHeldRightEntry.insert(0, eg.Held_Right if eg.Held_Right is not None else '')
            self.view.gearSetsPveHeldLeftEntry.insert(0, eg.Held_Left if eg.Held_Left is not None else '')
        else:
            raise ValueError(f"Unexpected active tab name: {tabIdentifier}")

    def copyPvpGearSetToPve(self):
        self.view.clearPveSetEntries()

        self.view.gearSetsPveHeadEntry.insert(0, self.view.gearSetsPvpHeadEntry.get())
        self.view.gearSetsPveJewel1Entry.insert(0, self.view.gearSetsPvpJewel1Entry.get())
        self.view.gearSetsPveJewel2Entry.insert(0, self.view.gearSetsPvpJewel2Entry.get())
        self.view.gearSetsPveCloakEntry.insert(0, self.view.gearSetsPvpCloakEntry.get())
        self.view.gearSetsPveBodyEntry.insert(0, self.view.gearSetsPvpBodyEntry.get())
        self.view.gearSetsPveHandsEntry.insert(0, self.view.gearSetsPvpHandsEntry.get())
        self.view.gearSetsPveLegsEntry.insert(0, self.view.gearSetsPvpLegsEntry.get())
        self.view.gearSetsPveFeetEntry.insert(0, self.view.gearSetsPvpFeetEntry.get())
        self.view.gearSetsPveHeldRightEntry.insert(0, self.view.gearSetsPvpHeldRightEntry.get())
        self.view.gearSetsPveHeldLeftEntry.insert(0, self.view.gearSetsPvpHeldLeftEntry.get())

    def copyPveGearSetToPvp(self):
        self.view.clearPvpSetEntries()

        self.view.gearSetsPvpHeadEntry.insert(0, self.view.gearSetsPveHeadEntry.get())
        self.view.gearSetsPvpJewel1Entry.insert(0, self.view.gearSetsPveJewel1Entry.get())
        self.view.gearSetsPvpJewel2Entry.insert(0, self.view.gearSetsPveJewel2Entry.get())
        self.view.gearSetsPvpCloakEntry.insert(0, self.view.gearSetsPveCloakEntry.get())
        self.view.gearSetsPvpBodyEntry.insert(0, self.view.gearSetsPveBodyEntry.get())
        self.view.gearSetsPvpHandsEntry.insert(0, self.view.gearSetsPveHandsEntry.get())
        self.view.gearSetsPvpLegsEntry.insert(0, self.view.gearSetsPveLegsEntry.get())
        self.view.gearSetsPvpFeetEntry.insert(0, self.view.gearSetsPveFeetEntry.get())
        self.view.gearSetsPvpHeldRightEntry.insert(0, self.view.gearSetsPveHeldRightEntry.get())
        self.view.gearSetsPvpHeldLeftEntry.insert(0, self.view.gearSetsPveHeldLeftEntry.get())
