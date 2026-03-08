import os
import tkinter as tk
from tkinter import ttk
import time
import ctypes
from typing import overload, Callable
from enum import Enum, StrEnum
from Wingman.core.controller import Controller
from Wingman.core.group import Group
from Wingman.core.character import Character
from Wingman.core.health_Tagger import HealthTagger
from Wingman.core.parsing.parser import Parser
from Wingman.core.item import Item

class SuppliesPaneChangeDirection(Enum):
    PREVIOUS = -1
    NEXT = 1

class View(tk.Frame):
    def __init__(self, root: tk.Tk | tk.Toplevel):
        super().__init__(root)

        self.grid(row=0, column=0, sticky=tk.NSEW)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.root = root
        # State
        self.var_total_xp = tk.StringVar(value="Total XP: 0")
        self.var_xp_hr = tk.StringVar(value="XP/Hr: 0")
        self.var_count_of_mobs_in_room = tk.StringVar(value="Mobs in Room: 0")
        self.var_duration = tk.StringVar(value="Time: 00:00:00")
        self.var_always_on_top = tk.BooleanVar(value=True)
        self.var_meditationRegenDisplay = tk.StringVar(value="Med: 0")
        self.isPaused: bool = False
        self.last_stat_update = 0
        self.dark_mode = False
        self._controller: Controller
        self.groupTreeview: ttk.Treeview
        self.menu_settings: tk.Menu
        self.var_ignoredMobPetsSemicolonDelimited = tk.StringVar(value="")
        self._miscellaneousSettings = tk.Toplevel(root, name="miscellaneousSettingsWindow")
        self._supplyCheckerWindow = tk.Toplevel(root, name="supplyCheckerWindow")
        self._gearSetsWindow = tk.Toplevel(root, name="gearSetsWindow")
        self.var_missingGearSetItems = tk.StringVar(value="")
        self.var_missingSupplyValues = tk.StringVar(value="")
        self.var_missingPveSupplyValues = tk.StringVar(value="")
        self.var_includePetsInGroup = tk.BooleanVar(value=False)
        self._cachedGroup: Group = Group([])
        self.var_buffOrShieldEndingText = tk.StringVar(value="")
        self.var_mitigatedAffectText = tk.StringVar(value="")
        self.var_spellDropWarningText = tk.StringVar(value="")
        self.var_soughtAfterItems = tk.StringVar(value="")
        #controller dependent *Var fields are applied in `set_controller`

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self._TopLevelWidgets: list[tk.Tk | tk.Toplevel] = [self.root,
                                                            self._miscellaneousSettings,
                                                            self._supplyCheckerWindow,
                                                            self._gearSetsWindow]

    @classmethod
    def ForTesting(cls):
        """
        Instantiates all the dependency prerequisites, in the proper order to avoid `AttributeError`s from occurring.
```
c = Controller.ForTesting()
```
:returns: An instance of `View` its controller set up for testing.
:rtype: `View`
        """
        c = Controller.ForTesting()
        return c.view

    def set_controller(self, controller: Controller):
        self._controller = controller
        # 1. Initialize "Always on Top" variable
        self.var_always_on_top = tk.BooleanVar(value=True)
        self.root.attributes("-topmost", self.var_always_on_top.get())

        self.var_hideDisplayedLabelCallbackTimerInMilliseconds = tk.IntVar(value=self._controller._HIDE_DISPLAYED_LABEL_CALLBACK_TIMER_IN_MILLISECONDS__FALLBACK)
        self.var_timeInMinutesToWarnAboutSpellsDropping = tk.IntVar(value=self._controller._ALERT_FOR_SPELL_DROPPING_DURATION_IN_MINUTES__FALLBACK)

    def setup_ui(self):
        """
        Setting up the UI requires the controller to be set first for binding.

        If the controller is not set an `AttributeError` occurs.
        """
        main_frame = ttk.Frame(self, name="main_frame", padding="10")
        main_frame.grid(row=0, column=0, sticky=tk.NSEW)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self._setUpUi_StatsRow(main_frame)
        self._setUpUi_GroupDisplay(main_frame)
        self._setUpUi_StatusFooter(main_frame)

    def _setUpUi_StatsRow(self, main_frame: ttk.Frame):
        # --- Top Stats Row ---
        stats_frame = ttk.Frame(main_frame, name="stats_frame", height=100)
        stats_frame.grid(row=0, column=0, pady=(0, 10), sticky=tk.EW)
        stats_frame.grid_columnconfigure(1, weight=1)

        experienceFrame = ttk.Frame(stats_frame)
        experienceFrame.grid(row=0, column=0, sticky=tk.W, padx=5, pady=10)
        ttk.Label(experienceFrame, textvariable=self.var_total_xp, font=("Segoe UI", 12, "bold")).grid(sticky=tk.W)
        ttk.Label(experienceFrame, textvariable=self.var_xp_hr).grid(sticky=tk.W)
        ttk.Label(experienceFrame, textvariable=self.var_count_of_mobs_in_room).grid(sticky=tk.W)

        #Central Column Labels
        centerFrame = ttk.Frame(stats_frame)
        centerFrame.grid(row=0, column=1, sticky=tk.NSEW)
        centerFrame.grid_rowconfigure(0, weight=1)
        centerFrame.grid_columnconfigure(0, weight=1)

        hospitalIconPath = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'gui', 'hospitalMapIcon.png')
        self._healGroupImage = tk.PhotoImage(file=hospitalIconPath)
        self._healGroupLabel = ttk.Label(centerFrame, name='healGroupLabel', image=self._healGroupImage)
        #Initially gridded/displayed to place it on the UI.
        #Immediately removed/hidden, only to be shown when predicate conditions are satisfied.
        self._healGroupLabel.grid(row=0, column=0)
        self._healGroupLabel.grid_remove()

        centralLabelStyleName = 'centralLabel.TLabel'
        self._afkImageLabel = ttk.Label(centerFrame, name='afkStatusLabel', text="AFK", style=centralLabelStyleName)
        self._afkImageLabel.grid(row=0, column=0)
        self._afkImageLabel.grid_remove()

        self._meditatingLabel = ttk.Label(centerFrame, name='meditationStatusLabel',
                                          textvariable=self.var_meditationRegenDisplay,
                                          style=centralLabelStyleName)
        self._meditatingLabel.grid(row=0, column=0)
        self._meditatingLabel.grid_remove()

        self._fullPowerLabel = ttk.Label(centerFrame, name='fullPowerStatusLabel',
                                         text="Full Power!",
                                         style=centralLabelStyleName)
        self._fullPowerLabel.grid(row=0, column=0)
        self._fullPowerLabel.grid_remove()

        self._dropAlertLabel = ttk.Label(centerFrame, name='dropAlertLabel',
                                            textvariable=self.var_spellDropWarningText,
                                            style=centralLabelStyleName)
        self._dropAlertLabel.grid(row=0, column=0)
        self._dropAlertLabel.grid_remove()

        self._hidingLabel = ttk.Label(main_frame, text="Hiding", anchor=tk.CENTER)
        self._hidingLabel.grid(row=1, column=0, sticky=tk.EW)
        self._hidingLabel.grid_remove()

        pauseSettingsTimerFrame = ttk.Frame(stats_frame)
        pauseSettingsTimerFrame.grid(row=0, column=2, sticky=tk.E, padx=5)
        ttk.Label(pauseSettingsTimerFrame, textvariable=self.var_duration, font=("Consolas", 10)).grid(row=0, column=0,sticky=tk.E, pady=(0,5))

        # Control Buttons Frame
        btns_frame = ttk.Frame(pauseSettingsTimerFrame)
        btns_frame.grid(row=1, column=0, sticky=tk.E)
        self.btn_pause = ttk.Button(btns_frame, text="Pause", command=lambda: self.apply_pause(not self.isPaused), width=8)
        self.btn_pause.grid(row=0, column=0, sticky=tk.W, padx=(0, 2))

        # Settings Dropdown
        self.mb_settings = ttk.Menubutton(btns_frame, text="⚙", width=3)
        self.mb_settings.grid(row=0, column=1, sticky=tk.W)

        self.menu_settings = tk.Menu(self.mb_settings, tearoff=0)

        # 2. Add the Checkbutton for Always on Top
        self.menu_settings.add_checkbutton(
            label="Always on Top",
            variable=self.var_always_on_top,
            command=lambda: self.apply_topmost(self.var_always_on_top.get())
        )
        self.menu_settings.add_separator()

        self.menu_settings.add_command(label="Toggle Dark Mode", command=self.toggle_theme)
        self.menu_settings.add_separator()
        self.menu_settings.add_command(label="Reset Stats", command=self._controller.reset_stats)
        self.menu_settings.add_separator()
        self.menu_settings.add_command(label="Miscellaneous settings", command=self._controller.open_miscellaneousSettings_window)
        self.mb_settings["menu"] = self.menu_settings

        self._setUpTopLevelWindow(self._miscellaneousSettings, "Miscellaneous Settings", "<Escape>", self._withdraw_miscellaneous_settings_window)
        self._miscellaneousSettings.grid_columnconfigure(1, weight=1)
        self._miscellaneousSettings.bind("<Escape>", lambda e: self._withdraw_miscellaneous_settings_window())
        self._miscellaneousSettings.minsize(550, 185)
        self._miscellaneousSettings.resizable(True, False)

        ttk.Label(self._miscellaneousSettings,
                  text="Ignore mobs/pets in room\n(semicolon ; delimited):", anchor=tk.E)\
            .grid(row=0, column=0, sticky=tk.E, padx=10, pady=(10, 0))
        self.ignoredMobsPetsCommaDelimitedEntry = ttk.Entry(self._miscellaneousSettings,
                                                            textvariable=self.var_ignoredMobPetsSemicolonDelimited)
        self.ignoredMobsPetsCommaDelimitedEntry.grid(row=0, column=1, sticky=tk.EW, padx=(0, 10))
        # helpful lambda explanation: https://stackoverflow.com/a/55093731
        self.ignoredMobsPetsCommaDelimitedEntry.bind("<FocusOut>", # Without the lambda the function is never invoked.
                                lambda e: self._controller.updateIgnoredMobsPets(self.var_ignoredMobPetsSemicolonDelimited.get()))
        ttk.Label(self._miscellaneousSettings,
                  text="Include mobs in\ngroup window: ")\
            .grid(row=1, column=0, sticky=tk.E, padx=10)
        self.includeMobsInGroupCheckButton = ttk.Checkbutton(self._miscellaneousSettings,
                                                        variable=self.var_includePetsInGroup,
                                                        command=lambda: self.update_display_of_pets_in_group_window(self.var_includePetsInGroup.get()))
        self.includeMobsInGroupCheckButton.grid(row=1, column=1, sticky=tk.W)
        ttk.Label(self._miscellaneousSettings,
                  text="Alerts to be displayed:\n(in milliseconds)")\
            .grid(row=2, column=0, sticky=tk.E, padx=10)
        self.alertLabelDurationDisplayEntry = ttk.Entry(self._miscellaneousSettings,
                                                  textvariable=self.var_hideDisplayedLabelCallbackTimerInMilliseconds,
                                                  width=10)
        self.alertLabelDurationDisplayEntry.grid(row=2, column=1, sticky=tk.W)
        ttk.Label(self._miscellaneousSettings,
                  text="Alert before affects drop:\n(in minutes)")\
            .grid(row=3, column=0, sticky=tk.E, padx=10)
        self.affectDropWarningDurationEntry = ttk.Entry(self._miscellaneousSettings,
                                                  textvariable=self.var_timeInMinutesToWarnAboutSpellsDropping,
                                                  width=10)
        self.affectDropWarningDurationEntry.grid(row=3, column=1, sticky=tk.W)

        ttk.Label(self._miscellaneousSettings,
                  text="Items sought after\n(semicolon ; delimited):",
                  anchor=tk.CENTER)\
            .grid(row=4, column=0, sticky=tk.EW, padx=10)
        #https://stackoverflow.com/a/4140988
        validateSoughtAfterItemsCommand = (self.register(self.validateSoughtAfterItemsEntry), '%P')
        self.soughtAfterItemsEntry = ttk.Entry(self._miscellaneousSettings,
                                               textvariable=self.var_soughtAfterItems,
                                               validate='key',
                                               validatecommand=validateSoughtAfterItemsCommand)
        self.soughtAfterItemsEntry.grid(row=4, column=1, sticky=tk.EW, padx=(0, 10))


        self.menu_settings.add_command(label="Gear sets", command=self.open_gearSetsWindow)


        gearSetsFrame = ttk.Frame(self._gearSetsWindow, name="gearSetsFrame")
        gearSetsFrame.grid(row=0, column=0, sticky=tk.NSEW)
        gearSetsFrame.grid_rowconfigure(0, weight=1)
        gearSetsFrame.grid_columnconfigure(0, weight=1)
        ttk.Label(gearSetsFrame, text="Dependent on current `equipment` in client.\nExecute `equipment` in the client to update cached values.")\
            .grid(row=0, column=0, sticky=tk.EW, padx=10, pady=(10, 0))
        self.gearSetsNotebook = ttk.Notebook(gearSetsFrame, name="gearSetsNotebook")
        self.gearSetsNotebook.grid(row=1, column=0, sticky=tk.NSEW, padx=10, pady=10)
        self.gearSetsNotebook.bind("<Button-3>", self.showGearSetsContextMenu)
        #https://pythonexamples.org/python-tkinter-context-menu/
        self.gearSetsContextMenu = tk.Menu(self._gearSetsWindow, tearoff=False)
        self.gearSetsContextMenu.add_command(label="Copy PvP -> PvE", command=self._controller.copyPvpGearSetToPve)
        self.gearSetsContextMenu.add_command(label="Copy PvE -> PvP", command=self._controller.copyPveGearSetToPvp)

        gearSetsPvpFrame = ttk.Frame(self.gearSetsNotebook, name="gearSetsPvpFrame")
        gearSetsPveFrame = ttk.Frame(self.gearSetsNotebook, name="gearSetsPveFrame")
        self.gearSetsNotebook.add(gearSetsPvpFrame, text="PvP")
        self.gearSetsNotebook.add(gearSetsPveFrame, text="PvE")
        self._setUpTopLevelWindow(self._gearSetsWindow, "Gear Sets", "<Escape>", self._withdraw_gearSetsWindow)
        self._gearSetsWindow.grid_columnconfigure(0, weight=1)
        self.bindPageUpAndPageDownToChangePanesInNotebook(self._gearSetsWindow, self.gearSetsNotebook)

        ttk.Label(gearSetsPvpFrame, text="On Head:").grid(row=0, column=0, sticky=tk.E)
        self.gearSetsPvpHeadEntry = ttk.Entry(gearSetsPvpFrame, width=50)
        self.gearSetsPvpHeadEntry.grid(row=0, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPvpFrame, text="On Jewel:").grid(row=1, column=0, sticky=tk.E)
        self.gearSetsPvpJewel1Entry = ttk.Entry(gearSetsPvpFrame)
        self.gearSetsPvpJewel1Entry.grid(row=1, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPvpFrame, text="On Jewel:").grid(row=2, column=0, sticky=tk.E)
        self.gearSetsPvpJewel2Entry = ttk.Entry(gearSetsPvpFrame)
        self.gearSetsPvpJewel2Entry.grid(row=2, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPvpFrame, text="On Cloak:").grid(row=3, column=0, sticky=tk.E)
        self.gearSetsPvpCloakEntry = ttk.Entry(gearSetsPvpFrame)
        self.gearSetsPvpCloakEntry.grid(row=3, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPvpFrame, text="On Body:").grid(row=4, column=0, sticky=tk.E)
        self.gearSetsPvpBodyEntry = ttk.Entry(gearSetsPvpFrame)
        self.gearSetsPvpBodyEntry.grid(row=4, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPvpFrame, text="On Hands:").grid(row=5, column=0, sticky=tk.E)
        self.gearSetsPvpHandsEntry = ttk.Entry(gearSetsPvpFrame)
        self.gearSetsPvpHandsEntry.grid(row=5, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPvpFrame, text="On Legs:").grid(row=6, column=0, sticky=tk.E)
        self.gearSetsPvpLegsEntry = ttk.Entry(gearSetsPvpFrame)
        self.gearSetsPvpLegsEntry.grid(row=6, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPvpFrame, text="On Feet:").grid(row=7, column=0, sticky=tk.E)
        self.gearSetsPvpFeetEntry = ttk.Entry(gearSetsPvpFrame)
        self.gearSetsPvpFeetEntry.grid(row=7, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPvpFrame, text="Held Right:").grid(row=8, column=0, sticky=tk.E)
        self.gearSetsPvpHeldRightEntry = ttk.Entry(gearSetsPvpFrame)
        self.gearSetsPvpHeldRightEntry.grid(row=8, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPvpFrame, text="Held Left:").grid(row=9, column=0, sticky=tk.E)
        self.gearSetsPvpHeldLeftEntry = ttk.Entry(gearSetsPvpFrame)
        self.gearSetsPvpHeldLeftEntry.grid(row=9, column=1, sticky=tk.EW)

        ttk.Label(gearSetsPveFrame, text="On Head:").grid(row=0, column=0, sticky=tk.E)
        self.gearSetsPveHeadEntry = ttk.Entry(gearSetsPveFrame, width=50)
        self.gearSetsPveHeadEntry.grid(row=0, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPveFrame, text="On Jewel:").grid(row=1, column=0, sticky=tk.E)
        self.gearSetsPveJewel1Entry = ttk.Entry(gearSetsPveFrame)
        self.gearSetsPveJewel1Entry.grid(row=1, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPveFrame, text="On Jewel:").grid(row=2, column=0, sticky=tk.E)
        self.gearSetsPveJewel2Entry = ttk.Entry(gearSetsPveFrame)
        self.gearSetsPveJewel2Entry.grid(row=2, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPveFrame, text="On Cloak:").grid(row=3, column=0, sticky=tk.E)
        self.gearSetsPveCloakEntry = ttk.Entry(gearSetsPveFrame)
        self.gearSetsPveCloakEntry.grid(row=3, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPveFrame, text="On Body:").grid(row=4, column=0, sticky=tk.E)
        self.gearSetsPveBodyEntry = ttk.Entry(gearSetsPveFrame)
        self.gearSetsPveBodyEntry.grid(row=4, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPveFrame, text="On Hands:").grid(row=5, column=0, sticky=tk.E)
        self.gearSetsPveHandsEntry = ttk.Entry(gearSetsPveFrame)
        self.gearSetsPveHandsEntry.grid(row=5, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPveFrame, text="On Legs:").grid(row=6, column=0, sticky=tk.E)
        self.gearSetsPveLegsEntry = ttk.Entry(gearSetsPveFrame)
        self.gearSetsPveLegsEntry.grid(row=6, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPveFrame, text="On Feet:").grid(row=7, column=0, sticky=tk.E)
        self.gearSetsPveFeetEntry = ttk.Entry(gearSetsPveFrame)
        self.gearSetsPveFeetEntry.grid(row=7, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPveFrame, text="Held Right:").grid(row=8, column=0, sticky=tk.E)
        self.gearSetsPveHeldRightEntry = ttk.Entry(gearSetsPveFrame)
        self.gearSetsPveHeldRightEntry.grid(row=8, column=1, sticky=tk.EW)
        ttk.Label(gearSetsPveFrame, text="Held Left:").grid(row=9, column=0, sticky=tk.E)
        self.gearSetsPveHeldLeftEntry = ttk.Entry(gearSetsPveFrame)
        self.gearSetsPveHeldLeftEntry.grid(row=9, column=1, sticky=tk.EW)

        pasteFrame = ttk.Frame(gearSetsFrame)
        pasteFrame.grid(row=2, column=0, sticky=tk.NSEW, pady=(0, 10))
        gearSetsPasteAreaText = tk.Text(pasteFrame, height=5, width=10, name='gearSetsPasteAreaText')
        gearSetsPasteAreaText.grid(row=0, column=0, sticky=tk.EW, padx=(10, 5), pady=(0, 5),
                                   columnspan=2, rowspan=2)
        gearSetsCopyPastedTextToEntriesButton = ttk.Button(pasteFrame,
                                                           text="Copy text to above entries",
                                                           command=lambda: self._controller.copyPastedGearSetTextToActiveTabEntries(gearSetsPasteAreaText.get("1.0", tk.END)))
        gearSetsCopyPastedTextToEntriesButton.grid(row=0, column=2, sticky=tk.W)
        ttk.Label(pasteFrame, text="<----- Area to the side for pasting into\nthen clicking the button to copy into entries.")\
            .grid(row=1, column=2, sticky=tk.W)

        gearSetsFooterFrame = ttk.Frame(gearSetsFrame)
        gearSetsFooterFrame.grid(row=3, column=0, sticky=tk.EW)
        ttk.Button(gearSetsFooterFrame, text="Check Gear Set",
                   command=lambda: self._controller.checkGearSet(self._controller.activeGearSetTabEquipment(),
                                                                 self._controller.model.inventory.EquippedGear_))\
            .grid(row=0, column=0, sticky=tk.E, padx=10, pady=(0, 10))
        ttk.Button(gearSetsFooterFrame, text="Withdraw Text - Clipboard", command=self._controller.sendBankWithdrawTextToClipboard)\
            .grid(row=0, column=1, sticky=tk.W, padx=10, pady=(0, 10))
        ttk.Button(gearSetsFooterFrame, text="Clear Set", command=self._controller.clearGearSetEntriesOnActiveTab)\
            .grid(row=0, column=2, sticky=tk.W, padx=10, pady=(0, 10))

        self.missingGearSetItemsLabel = ttk.Label(gearSetsFooterFrame, textvariable=self.var_missingGearSetItems, name="missingGearSetItemsLabel")
        self.missingGearSetItemsLabel.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=10)

        self.menu_settings.add_command(label="Check Supplies", command=self.open_suppliesWindow)
        suppliesFrame = ttk.Frame(self._supplyCheckerWindow, name="suppliesFrame")
        suppliesFrame.grid(row=0, column=0, sticky=tk.NSEW)
        suppliesFrame.grid_rowconfigure(1, weight=1)
        suppliesFrame.grid_columnconfigure(0, weight=1)

        ttk.Label(suppliesFrame,
                  text="List of items to have in your inventory.\nDependent on accurate cache. Execute `inventory` in client to refresh cache.")\
            .grid(row=0, column=0, sticky=tk.W, padx=10, pady=(10, 0))
        self.suppliesNotebook = ttk.Notebook(suppliesFrame, name="suppliesNotebook")
        self.suppliesNotebook.grid(row=1, column=0, sticky=tk.NSEW, padx=10, pady=5)
        suppliesPvpFrame = ttk.Frame(self.suppliesNotebook, name="pvpSuppliesFrame")
        suppliesPvpFrame.grid_columnconfigure(0, weight=1)
        suppliesPveFrame = ttk.Frame(self.suppliesNotebook, name="pveSuppliesFrame")
        suppliesPveFrame.grid_columnconfigure(0, weight=1)
        self.suppliesNotebook.add(suppliesPvpFrame, text="PvP")
        self.pvpSuppliesText = tk.Text(suppliesPvpFrame, width=60, height=10)
        self.pvpSuppliesText.grid(row=0, column=0, sticky=tk.NSEW)
        self.suppliesNotebook.add(suppliesPveFrame, text="PvE")
        self.pveSuppliesText = tk.Text(suppliesPveFrame, width=60, height=10)
        self.pveSuppliesText.grid(row=0, column=0, sticky=tk.NSEW)

        self._setUpTopLevelWindow(self._supplyCheckerWindow, "Supply Checker", "<Escape>", self._withdraw_suppliesWindow)
        self._supplyCheckerWindow.minsize(450, 280)
        self._supplyCheckerWindow.grid_rowconfigure(1, weight=1)
        self._supplyCheckerWindow.grid_columnconfigure(0, weight=1)
        self.bindPageUpAndPageDownToChangePanesInNotebook(self._supplyCheckerWindow, self.suppliesNotebook)

        supplyCheckerFooterFrame = ttk.Frame(suppliesFrame)
        supplyCheckerFooterFrame.grid(row=2, column=0, sticky=tk.EW)
        ttk.Button(supplyCheckerFooterFrame,
                text="Check Inventory",
                command=lambda: self._controller.updateMissingSuppliesLabel(self._controller.activeTabTextInNotebook(self.suppliesNotebook),
                                                                            self._controller.suppliesTextFromTab(self._controller.activeTabTextInNotebook(self.suppliesNotebook)),
                                                                            self._controller.model.inventory))\
            .grid(row=0, column=0, sticky=tk.NW, padx=10, pady=5)
        ttk.Label(supplyCheckerFooterFrame,
                textvariable=self.var_missingSupplyValues,
                wraplength=475)\
            .grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

    def _setUpTopLevelWindow(self, window: tk.Toplevel, title: str, bindKey: str, withdrawWindowCallback: Callable[[], None]):
        window.attributes("-topmost", self.var_always_on_top.get())
        window.protocol("WM_DELETE_WINDOW", withdrawWindowCallback)  # Hide on close
        window.withdraw() # Start hidden
        window.title(title)
        window.bind(bindKey, lambda e: withdrawWindowCallback())

    def showGearSetsContextMenu(self, event):
        self.gearSetsContextMenu.tk_popup(event.x_root, event.y_root)
        self.gearSetsContextMenu.grab_release()

    def _setUpUi_GroupDisplay(self, main_frame: ttk.Frame):
        # --- Group Dashboard (Treeview) ---
        lbl_dash = ttk.Label(main_frame, name="groupStatusLabel", text="Group Status:", font=("Segoe UI", 10, "bold"))
        lbl_dash.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        columns = ("cls", "lvl", "status", "name", "hp", "fat", "pwr")
        self.groupTreeview = ttk.Treeview(main_frame, columns=columns, show="headings", height=8, 
                                    name='groupTreeView')

        self.groupTreeview.tag_configure(HealthTagger.HealthLevels.ZEROED.value, background='#000000', foreground='#ffffff')
        self.groupTreeview.tag_configure(HealthTagger.HealthLevels.AT_OR_BELOW_25.value, background='#ff0000', foreground='#000000')
        self.groupTreeview.tag_configure(HealthTagger.HealthLevels.AT_OR_BELOW_50.value, background="#FFFF00", foreground='#000000')

        self.groupTreeview.heading("cls", text="Class")
        self.groupTreeview.heading("lvl", text="Lvl")
        self.groupTreeview.heading("status", text="Status")
        self.groupTreeview.heading("name", text="Name")
        self.groupTreeview.heading("hp", text="HP")
        self.groupTreeview.heading("fat", text="Fatigue")
        self.groupTreeview.heading("pwr", text="Power")

        self.groupTreeview.column("cls", width=50, anchor="center")
        self.groupTreeview.column("lvl", width=40, anchor="center")
        self.groupTreeview.column("status", width=30, anchor="center")
        self.groupTreeview.column("name", width=100, anchor="w")
        self.groupTreeview.column("hp", width=80, anchor="center")
        self.groupTreeview.column("fat", width=80, anchor="center")
        self.groupTreeview.column("pwr", width=80, anchor="center")

        self.groupTreeview.grid(row=2, column=0, pady=5, sticky=tk.NSEW)

    def _setUpUi_StatusFooter(self, main_frame: ttk.Frame):
        #region Shield/Buff Ending Labels
        _statusFooter = ttk.Frame(main_frame, name="statusFooter")
        _statusFooter.grid(row=3, column=0, sticky=tk.EW)
        _statusFooter.grid_columnconfigure(0, weight=1)
        _statusFooter.grid_columnconfigure(1, weight=1)
        _statusFooter.grid_columnconfigure(2, weight=1)
        #Common labels
        statusFooterStyleName = 'statusFooter.TLabel'
        statusFooterStyle = ttk.Style().configure(statusFooterStyleName,
                                                font=("Segoe UI", 8, "bold"),
                                                padding=5)
        self.buffOrShieldEndedLabel = ttk.Label(_statusFooter,
                                                textvariable=self.var_buffOrShieldEndingText,
                                                style=statusFooterStyleName)
        self.buffOrShieldEndedLabel.grid(row=0, column=0, sticky=tk.W)
        self.buffOrShieldEndedLabel.grid_remove()

        self.spellMitigatesAffectsLabel = ttk.Label(_statusFooter,
                                                    textvariable=self.var_mitigatedAffectText,
                                                    style=statusFooterStyleName)
        self.spellMitigatesAffectsLabel.grid(row=3, column=1)

        self.spellDropWarningLabel = ttk.Label(_statusFooter,
                                                textvariable=self.var_spellDropWarningText,
                                                style=statusFooterStyleName)
        self.spellDropWarningLabel.grid(row=3, column=2, sticky=tk.E)
        self.spellDropWarningLabel.grid_remove()

    def apply_theme(self):
        if self.dark_mode:
            bg_color = "#2b2b2b"
            fg_color = "#ffffff"
            field_bg = "#383838"
            select_bg = "#4a6984"
            self.set_windows_titlebar_color(True)
        else:
            bg_color = "#f0f0f0"
            fg_color = "#000000"
            field_bg = "#ffffff"
            select_bg = "#0078d7"
            self.set_windows_titlebar_color(False)

        for window in self._TopLevelWidgets:
            window.configure(bg=bg_color)

        self.style.configure(".", background=bg_color, foreground=fg_color, fieldbackground=field_bg)
        self.style.configure("Treeview", background=field_bg, foreground=fg_color, fieldbackground=field_bg)
        self.style.map("Treeview", background=[("selected", select_bg)], foreground=[("selected", "white")])
        self.style.configure("Treeview.Heading", background=bg_color, foreground=fg_color, relief="flat")
        self.style.configure("TMenubutton", background=bg_color, foreground=fg_color)

        #https://likegeeks.com/tkinter-notebook-tab-styling-ttk/
        self.style.configure("TNotebook.Tab", foreground="black")
        self.style.map("TNotebook.Tab",
                  background=[("selected", bg_color), ("active", field_bg), ("disabled", "black")],
                  foreground=[("selected", fg_color), ("active", fg_color), ("disabled", "darkgray")])
        self.pvpSuppliesText.configure(bg=field_bg, fg=fg_color)
        self.pveSuppliesText.configure(bg=field_bg, fg=fg_color)

        self.menu_settings.config(bg=field_bg, fg=fg_color, activebackground=select_bg, activeforeground="white")

    def apply_pause(self, isPaused: bool):
        if isPaused:
            self.btn_pause.config(text="Resume")
            self._controller.gameSession.pause_clock()
        else:
            self.btn_pause.config(text="Pause")
            self._controller.gameSession.resume_clock()

        self.isPaused = isPaused

    def set_windows_titlebar_color(self, use_dark: bool):
        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
            get_parent = ctypes.windll.user32.GetParent
            value = 1 if use_dark else 0
            for window in self._TopLevelWidgets:
                hwnd = get_parent(window.winfo_id())
                set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(ctypes.c_int(value)), 4)

            self.update()
        except Exception:
            pass

    def update_gui(self):
        self.after(100, self.update_gui)
        self._controller.process_queue()
        group_data = self._controller.gameSession.group
        if group_data != self._cachedGroup:
            self.refreshGroupDisplay(group_data)
            self._cachedGroup = Group(group_data.Members) # Cache a new instance to avoid using the same reference for next comparison.

        if not self.isPaused:
            current_xp = self._controller.gameSession.total_xp
            self.var_total_xp.set(f"Total XP: {current_xp:,}")
            now = time.time()
            if now - self.last_stat_update >= 1.0:
                self.updateTimeRelatedValues(now)

        match self._controller.model.isAfk:
            case True:
                self.displayAfkLabel()
            case False:
                self.hideAfkLabel()
            case _:
                pass

        match self._controller.model.isMeditating:
            case True:
                self.displayMeditationLabel()
            case False:
                self.hideMeditationLabel()
                self._controller.model.isMeditating = None # Set to None to avoid repeated grid removals.
            case _:
                pass

        match self._controller.model.isHiding:
            case True:
                self.displayHidingLabel()
            case False:
                self.hideHidingLabel()
            case _:
                pass

        if self._controller.model.BuffOrShieldEnding is not None:
            self.displayBuffOrShieldEndedLabel(self._controller.model.BuffOrShieldEnding)

            # Reset the value after handling to avoid repeated removal calls.
            self._controller.model.BuffOrShieldEnding = None

        self.updateMobCountDisplay()

        if self._controller.model.AffectsWithTimeExpiration:
            affectNamesEndingSoon = [affect.Name for affect in self._controller.model.AffectsWithTimeExpiration \
                                    if affect.timeRemainingInSeconds() <= 60 * self.var_timeInMinutesToWarnAboutSpellsDropping.get() ]
            if affectNamesEndingSoon:
                warningText = ", ".join(affectNamesEndingSoon)
                self._controller.displayAffectSpellDropWarningLabel(warningText)
            else:
                self._controller.hideAffectSpellDropWarningLabel()

        if self._controller.model.SoughtAfterItems_ThatDropped:
            self._controller.displayDropAlertLabel(", ".join(self._controller.model.SoughtAfterItems_ThatDropped))
            self._controller.model.SoughtAfterItems_ThatDropped.clear()

    def updateTimeRelatedValues(self, currentTime: float):
        current_rate = self._controller.gameSession.get_xp_per_hour()
        self.var_xp_hr.set(f"{current_rate:,} xp / hr")
        self.var_duration.set(self._controller.gameSession.get_duration_str())
        self.last_stat_update = currentTime

    # 3. The Toggle Logic
    def apply_topmost(self, value: bool):
        """Applies the current state of the BooleanVar to the window."""
        self.var_always_on_top.set(value)
        self.root.attributes("-topmost", value)
        for widget in self._TopLevelWidgets:
            widget.attributes("-topmost", value)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def reset_stats(self):
        self._controller.gameSession.reset()
        for item in self.groupTreeview.get_children():
            self.groupTreeview.delete(item)

    def displayHealGroupImage(self):
        self._healGroupLabel.grid()
    
    def hideHealGroupImage(self):
        self._healGroupLabel.grid_remove()

    def refreshGroupDisplay(self, group: Group):
        def isCurrentPartyMember(m: Character):
            return m.Class_ != ""

        def isNewlyJoinedPartyMember(m: Character):
            return m.Class_ == "" and m.IsNewGroupFollower

        for item in self.groupTreeview.get_children():
            self.groupTreeview.delete(item)
        for m in group.Members:
            if isCurrentPartyMember(m):
                values = (m.Class_, m.Level, str(m.Status), m.Name, str(m.Hp), str(m.Fat), str(m.Pow))

                healthTag = HealthTagger.HealthTag(m)

                self.groupTreeview.insert('', tk.END, iid=m.Name, values=values, tags=(healthTag))
            elif isNewlyJoinedPartyMember(m):
                suffixToMakeUnique = ''
                while self.groupTreeview.exists(m.Name + suffixToMakeUnique):
                    suffixToMakeUnique += '+'

                values = ('__', "__", "__", m.Name, '__', '__', '__')
                self.groupTreeview.insert('', tk.END, iid=m.Name + suffixToMakeUnique, values=values)


        if group.DisplayHealingIcon:
            self.displayHealGroupImage()
        else:
            self.hideHealGroupImage()

    def displayAfkLabel(self):
        self._afkImageLabel.grid()
    def hideAfkLabel(self):
        self._afkImageLabel.grid_remove()

    def displayMeditationLabel(self):
        self._controller.updateMeditationDisplayValue()
        self._meditatingLabel.grid()
    def hideMeditationLabel(self):
        self._meditatingLabel.grid_remove()

    def displayFullPowerLabel(self):
        self._fullPowerLabel.grid()
        self.after(self.var_hideDisplayedLabelCallbackTimerInMilliseconds.get(), self.hideFullPowerLabel)
    def hideFullPowerLabel(self):
        self._fullPowerLabel.grid_remove()

    def displayHidingLabel(self):
        self._hidingLabel.grid()
    def hideHidingLabel(self):
        self._hidingLabel.grid_remove()

    def updateMobCountDisplay(self):
        self._controller.removedIgnoredMobsFromCurrentRoom()
        if len(self._controller.model.currentMobsInRoom) == 0:
            self.var_count_of_mobs_in_room.set("")
        else:
            self.var_count_of_mobs_in_room.set(f"Mobs in Room: {len(self._controller.model.currentMobsInRoom)}")

    def open_pet_or_mobs_display_settings_window(self):
        self._miscellaneousSettings.deiconify()

    def _withdraw_miscellaneous_settings_window(self):
        self._miscellaneousSettings.withdraw()

    def update_display_of_pets_in_group_window(self, displayMobsInGroupWindow: bool):
        self._controller.update_display_of_pets_in_group_window(displayMobsInGroupWindow)

    def displayBuffOrShieldEndedLabel(self, endingBuffOrShield :Parser.ParseBuffOrShieldText):
        self.var_buffOrShieldEndingText.set(endingBuffOrShield.name
                                            .replace("Dot", ".")
                                            .replace("_", " "))
        self.buffOrShieldEndedLabel.grid()
        self.after(self.var_hideDisplayedLabelCallbackTimerInMilliseconds.get(), self.hideBuffOrShieldEndedLabel)
    def hideBuffOrShieldEndedLabel(self):
        self.buffOrShieldEndedLabel.grid_remove()

    @overload
    def displayMitigatedAffectLabel(self, spellMitigationAffectMember: Parser.SpellMitigationAffect): ...
    @overload
    def displayMitigatedAffectLabel(self, affectResistedByConstitution: Parser.ConstitutionResisted): ...

    def displayMitigatedAffectLabel(self, mitigationEnumMember: StrEnum):
        self.var_mitigatedAffectText.set(mitigationEnumMember.name
                                              .replace("Dot", "."))
        self.spellMitigatesAffectsLabel.grid()
        self.after(self.var_hideDisplayedLabelCallbackTimerInMilliseconds.get(), self.hideSpellMitigatesAffect)
    def hideSpellMitigatesAffect(self):
        self.spellMitigatesAffectsLabel.grid_remove()

    def open_suppliesWindow(self):
        self._supplyCheckerWindow.deiconify()
    def _withdraw_suppliesWindow(self):
        self._supplyCheckerWindow.withdraw()

    @overload
    def updateMissingSuppliesLabel(self, displayText: str): ...
    @overload
    def updateMissingSuppliesLabel(self, tabIndicator: str, missingSuppliesList: list[Item]): ...

    def updateMissingSuppliesLabel(self, *args):
        if len(args) == 1 and isinstance(args[0], str):
            value = args[0]
            self.var_missingSupplyValues.set(value)
            return
        
        if len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], list):
            tabIndicatorText = args[0]
            value = args[1]
            if len(value) == 0:
                displayText = "All items are present for invading!"
                self.after(self.var_hideDisplayedLabelCallbackTimerInMilliseconds.get(), lambda: self.var_missingSupplyValues.set("")) # Clear the label after a delay
            else:
                displayText = f"Missing '{tabIndicatorText}' Supplies:\n  " + "\n  ".join([f"{item}" for item in value])

            self.var_missingSupplyValues.set(displayText)

    def bindPageUpAndPageDownToChangePanesInNotebook(self, window: tk.Toplevel, notebook: ttk.Notebook):
        window.bind("<Control-Next>",
                lambda _: self.change_page_in_notebook(notebook=notebook,
                                                       direction=SuppliesPaneChangeDirection.NEXT))
        window.bind("<Control-Prior>",
                lambda _: self.change_page_in_notebook(notebook=notebook,
                                                       direction=SuppliesPaneChangeDirection.PREVIOUS))

    def change_page_in_notebook(self, notebook: ttk.Notebook, direction: SuppliesPaneChangeDirection):
        currentTab = notebook.index(notebook.select())
        totalTabs = len(notebook.tabs())
        newTabIndex = (currentTab + direction.value) % totalTabs
        notebook.select(newTabIndex)

    def displayAffectSpellDropWarningLabel(self, warningText: str):
        self.var_spellDropWarningText.set(f"{warningText} dropping in less than {self.var_timeInMinutesToWarnAboutSpellsDropping.get()} minutes!")
        self.spellDropWarningLabel.grid()
    def hideAffectSpellDropWarningLabel(self):
        self.spellDropWarningLabel.grid_remove()

    def displayDropAlertLabel(self, text: str):
        self.var_spellDropWarningText.set("Dropped: " + text)
        self._dropAlertLabel.grid()
        self.after(self.var_hideDisplayedLabelCallbackTimerInMilliseconds.get(), self.hideDropAlertLabel)
    def hideDropAlertLabel(self):
        self._dropAlertLabel.grid_remove()

    def validateSoughtAfterItemsEntry(self, proposedValue: str) -> bool:
        itemNamesSet, itemBaseNamesSet = self._controller.SoughtAfterItems_SemicolonDelimitedTextToTwoSets(proposedValue)
        self._controller.model.SoughtAfterItems_Names = itemNamesSet
        self._controller.model.SoughtAfterItems_BaseItemNames = itemBaseNamesSet

        return True

    def open_gearSetsWindow(self):
        self._gearSetsWindow.deiconify()
    def _withdraw_gearSetsWindow(self):
        self._gearSetsWindow.withdraw()

    def clearPvpSetEntries(self):
        self.gearSetsPvpHeadEntry.delete(0, tk.END)
        self.gearSetsPvpJewel1Entry.delete(0, tk.END)
        self.gearSetsPvpJewel2Entry.delete(0, tk.END)
        self.gearSetsPvpCloakEntry.delete(0, tk.END)
        self.gearSetsPvpBodyEntry.delete(0, tk.END)
        self.gearSetsPvpHandsEntry.delete(0, tk.END)
        self.gearSetsPvpLegsEntry.delete(0, tk.END)
        self.gearSetsPvpFeetEntry.delete(0, tk.END)
        self.gearSetsPvpHeldRightEntry.delete(0, tk.END)
        self.gearSetsPvpHeldLeftEntry.delete(0, tk.END)
    def clearPveSetEntries(self):
        self.gearSetsPveHeadEntry.delete(0, tk.END)
        self.gearSetsPveJewel1Entry.delete(0, tk.END)
        self.gearSetsPveJewel2Entry.delete(0, tk.END)
        self.gearSetsPveCloakEntry.delete(0, tk.END)
        self.gearSetsPveBodyEntry.delete(0, tk.END)
        self.gearSetsPveHandsEntry.delete(0, tk.END)
        self.gearSetsPveLegsEntry.delete(0, tk.END)
        self.gearSetsPveFeetEntry.delete(0, tk.END)
        self.gearSetsPveHeldRightEntry.delete(0, tk.END)
        self.gearSetsPveHeldLeftEntry.delete(0, tk.END)

    def displayMissingGearSetItemsLabel(self, value: str):
        self.var_missingGearSetItems.set(value)
        self.missingGearSetItemsLabel.grid()
    def hideMissingGearSetItemsLabel(self):
        self.missingGearSetItemsLabel.grid_remove()
