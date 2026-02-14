import os
import tkinter as tk
from tkinter import ttk
import time
import ctypes
from Wingman.core.controller import Controller
from Wingman.core.group import Group
from Wingman.core.character import Character
from Wingman.core.health_Tagger import HealthTagger
from Wingman.core.parser import Parser

class View(tk.Frame):
    def __init__(self, parent: tk.Tk | tk.Toplevel):
        super().__init__(parent)

        self.grid(row=0, column=0, sticky=tk.NSEW)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.parent = parent
        # State
        self.var_total_xp = tk.StringVar(value="Total XP: 0")
        self.var_xp_hr = tk.StringVar(value="XP/Hr: 0")
        self.var_count_of_mobs_in_room = tk.StringVar(value="Mobs in Room: 0")
        self.var_duration = tk.StringVar(value="Time: 00:00:00")
        self.var_always_on_top = tk.BooleanVar(value=True)
        self.var_meditationRegenDisplay = tk.StringVar(value="Med: 0")
        self.paused: bool = False
        self.last_stat_update = 0
        self.dark_mode = False
        self._controller: Controller
        self.groupTreeview: ttk.Treeview
        self.menu_settings: tk.Menu
        self.var_ignoredMobPetsCsv = tk.StringVar(value="")
        self._pet_or_mobs_display_settings_window = tk.Toplevel(parent)
        self.var_includePetsInGroup = tk.BooleanVar(value=False)
        self._cachedGroup: Group = Group([])
        self._buffOrShieldEndingDisplayTime = 2000 #ms

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self._TopLevelWidgets: list[tk.Tk | tk.Toplevel] = [self.parent, self._pet_or_mobs_display_settings_window]
    
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
        self.parent.attributes("-topmost", self.var_always_on_top.get())
    
    def setup_ui(self):
        """
        Setting up the UI requires the controller to be set first for binding.

        If the controller is not set an `AttributeError` occurs.
        """
        main_frame = ttk.Frame(self, name="main_frame", padding="10")
        main_frame.grid(row=0, column=0, sticky=tk.NSEW)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

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
        afkStyle = ttk.Style().configure(centralLabelStyleName, font=("Segoe UI", 30, "bold"))
        self._afkImageLabel.grid(row=0, column=0)
        self._afkImageLabel.grid_remove()

        self._meditatingLabel = ttk.Label(centerFrame, name='meditationStatusLabel', 
                                          textvariable=self.var_meditationRegenDisplay, 
                                          style=centralLabelStyleName)
        self._meditatingLabel.grid(row=0, column=0)
        self._meditatingLabel.grid_remove()

        self._hidingLabel = ttk.Label(main_frame, text="Hiding", anchor=tk.CENTER)
        self._hidingLabel.grid(row=1, column=0, sticky=tk.EW)
        self._hidingLabel.grid_remove()

        pauseSettingsTimerFrame = ttk.Frame(stats_frame)
        pauseSettingsTimerFrame.grid(row=0, column=2, sticky=tk.E, padx=5)
        ttk.Label(pauseSettingsTimerFrame, textvariable=self.var_duration, font=("Consolas", 10)).grid(row=0, column=0,sticky=tk.E, pady=(0,5))

        # Control Buttons Frame
        btns_frame = ttk.Frame(pauseSettingsTimerFrame)
        btns_frame.grid(row=1, column=0, sticky=tk.E)

        # Pause Button (Updated width to 8 per previous request)
        self.btn_pause = ttk.Button(btns_frame, text="Pause", command=self.toggle_pause, width=8)
        self.btn_pause.grid(row=0, column=0, sticky=tk.W, padx=(0, 2))

        # Settings Dropdown
        self.mb_settings = ttk.Menubutton(btns_frame, text="⚙", width=3)
        self.mb_settings.grid(row=0, column=1, sticky=tk.W)

        self.menu_settings = tk.Menu(self.mb_settings, tearoff=0)

        # 2. Add the Checkbutton for Always on Top
        self.menu_settings.add_checkbutton(
            label="Always on Top",
            variable=self.var_always_on_top,
            command=self.toggle_topmost
        )
        self.menu_settings.add_separator()

        self.menu_settings.add_command(label="Toggle Dark Mode", command=self.toggle_theme)
        self.menu_settings.add_separator()
        self.menu_settings.add_command(label="Reset Stats", command=self._controller.reset_stats)
        self.menu_settings.add_separator()
        self.menu_settings.add_command(label="Mobs/Pet settings", command=self._controller.open_ignore_mobs_window)
        self._pet_or_mobs_display_settings_window.attributes("-topmost", True)
        self._pet_or_mobs_display_settings_window.protocol("WM_DELETE_WINDOW", self._withdraw_pet_or_mobs_display_settings_window)  # Hide on close
        self._pet_or_mobs_display_settings_window.withdraw()  # Start hidden
        self._pet_or_mobs_display_settings_window.title("Mob/Pet Settings")
        ttk.Label(self._pet_or_mobs_display_settings_window, 
                  text="Ignore mobs/pets in room\n(comma-separated):")\
            .grid(row=0, column=0, sticky=tk.W, padx=10, pady=(10, 0))
        self.ignoredMobsPetsCsv = ttk.Entry(self._pet_or_mobs_display_settings_window, 
                                       textvariable=self.var_ignoredMobPetsCsv, 
                                       width=50)
        self.ignoredMobsPetsCsv.grid(row=0, column=1, sticky=tk.W, padx=10)
        # helpful lambda explanation: https://stackoverflow.com/a/55093731
        self.ignoredMobsPetsCsv.bind("<FocusOut>", # Without the lambda the function is never invoked.
                                lambda e: self._controller.updateIgnoredMobsPets(self.var_ignoredMobPetsCsv.get()))
        ttk.Label(self._pet_or_mobs_display_settings_window,
                  text="Include mobs in group window: ")\
            .grid(row=1, column=0, sticky=tk.W, padx=10)
        self.includeMobsInGroupCheckButton = ttk.Checkbutton(self._pet_or_mobs_display_settings_window, 
                                                        variable=self.var_includePetsInGroup, 
                                                        command=lambda: self.update_display_of_pets_in_group_window(self.var_includePetsInGroup.get()))
        self.includeMobsInGroupCheckButton.grid(row=1, column=1, sticky=tk.W, padx=10, pady=(0, 10))
        
        self.mb_settings["menu"] = self.menu_settings

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

        #region Shield/Buff Ending Labels
        #Common labels
        shieldBuffStyleName = 'shieldBuff.TLabel'
        shieldBuffStyle = ttk.Style().configure(shieldBuffStyleName,
                                                font=("Segoe UI", 8, "bold"),
                                                padding=5)
        self.shieldEndedLabel = ttk.Label(main_frame, text="Shield - ended", style=shieldBuffStyleName)
        self.shieldEndedLabel.grid(row=3, column=0, sticky=tk.W)
        self.shieldEndedLabel.grid_remove()

        self.blurEndedLabel = ttk.Label(main_frame, text="Blur - ended", style=shieldBuffStyleName)
        self.blurEndedLabel.grid(row=3, column=0, sticky=tk.W)
        self.blurEndedLabel.grid_remove()

        self.protectEndedLabel = ttk.Label(main_frame, text="Protect - ended", style=shieldBuffStyleName)
        self.protectEndedLabel.grid(row=3, column=0, sticky=tk.W)
        self.protectEndedLabel.grid_remove()

        self.toughSkinEndedLabel = ttk.Label(main_frame, text="Tough.Skin - ended", style=shieldBuffStyleName)
        self.toughSkinEndedLabel.grid(row=3, column=0, sticky=tk.W)
        self.toughSkinEndedLabel.grid_remove()

        #Chaos
        self.bleedResistEndedLabel = ttk.Label(main_frame, text="Bleed Resist - ended", style=shieldBuffStyleName)
        self.bleedResistEndedLabel.grid(row=3, column=0, sticky=tk.W)
        self.bleedResistEndedLabel.grid_remove()

        self.chaosFortitudeEndedLabel = ttk.Label(main_frame, text="Chaos Fortitude - ended", style=shieldBuffStyleName)
        self.chaosFortitudeEndedLabel.grid(row=3, column=0, sticky=tk.W)
        self.chaosFortitudeEndedLabel.grid_remove()

        self.combatEndedLabel = ttk.Label(main_frame, text="Combat - ended", style=shieldBuffStyleName)
        self.combatEndedLabel.grid(row=3, column=0, sticky=tk.W)
        self.combatEndedLabel.grid_remove()

        self.diseaseResistEndedLabel = ttk.Label(main_frame, text="Disease Resist - ended", style=shieldBuffStyleName)
        self.diseaseResistEndedLabel.grid(row=3, column=0, sticky=tk.W)
        self.diseaseResistEndedLabel.grid_remove()

        self.poisonResistEndedLabel = ttk.Label(main_frame, text="Poison Resist - ended", style=shieldBuffStyleName)
        self.poisonResistEndedLabel.grid(row=3, column=0, sticky=tk.W)
        self.poisonResistEndedLabel.grid_remove()

        #Good
        self.blessEndedLabel = ttk.Label(main_frame, text="Bless - ended", style=shieldBuffStyleName)
        self.blessEndedLabel.grid(row=3, column=0, sticky=tk.W)
        self.blessEndedLabel.grid_remove()

        #Evil
        self.regenerateEndedLabel = ttk.Label(main_frame, text="Regenerate - ended", style=shieldBuffStyleName)
        self.regenerateEndedLabel.grid(row=3, column=0, sticky=tk.W)
        self.regenerateEndedLabel.grid_remove()

        self.vitalizeEndedLabel = ttk.Label(main_frame, text="Vitalize - ended", style=shieldBuffStyleName)
        self.vitalizeEndedLabel.grid(row=3, column=0, sticky=tk.W)
        self.vitalizeEndedLabel.grid_remove()
        #endregion


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
        self.menu_settings.config(bg=field_bg, fg=fg_color, activebackground=select_bg, activeforeground="white")

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.btn_pause.config(text="Resume")
            if hasattr(self._controller.gameSession, 'pause_clock'): self._controller.gameSession.pause_clock()
        else:
            self.btn_pause.config(text="Pause")
            if hasattr(self._controller.gameSession, 'resume_clock'): self._controller.gameSession.resume_clock()
    
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
        if self.paused: return
        self._controller.process_queue()
        group_data = self._controller.gameSession.group
        if group_data != self._cachedGroup:
            self.refreshGroupDisplay(group_data)
            self._cachedGroup = Group(group_data.Members) # Cache a new instance to avoid using the same reference for next comparison.
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
            match self._controller.model.BuffOrShieldEnding:
                case Parser.ParseBuffOrShieldText.ShieldEnds:
                    self.displayShieldEndedLabel()
                case Parser.ParseBuffOrShieldText.BlurEnds:
                    self.displayBlurEndedLabel()
                case Parser.ParseBuffOrShieldText.ProtectEnds:
                    self.displayProtectEndedLabel()
                case Parser.ParseBuffOrShieldText.ToughSkinEnds:
                    self.displayToughSkinEndedLabel()
                #Chaos
                case Parser.ParseBuffOrShieldText.BleedResistEnds:
                    self.displayBleedResistEndedLabel()
                case Parser.ParseBuffOrShieldText.ChaosFortitudeEnds:
                    self.displayChaosFortitudeEndedLabel()
                case Parser.ParseBuffOrShieldText.CombatEnds:
                    self.displayCombatEndedLabel()
                case Parser.ParseBuffOrShieldText.DiseaseResistEnds:
                    self.displayDiseaseResistEndedLabel()
                case Parser.ParseBuffOrShieldText.PoisonResistEnds:
                    self.displayPoisonResistEndedLabel()
                #Good
                case Parser.ParseBuffOrShieldText.BlessEnds:
                    self.displayBlessEndedLabel()
                #Evil
                case Parser.ParseBuffOrShieldText.RegenerateEnds:
                    self.displayRegenerateEndedLabel()
                case Parser.ParseBuffOrShieldText.VitalizeEnds:
                    self.displayVitalizeEndedLabel()
                #Fall through case
                case _:
                    pass

            # Reset the value after handling to avoid repeated removal calls.
            self._controller.model.BuffOrShieldEnding = None

        self.updateMobCountInRoom()

    def updateTimeRelatedValues(self, currentTime: float):
        current_rate = self._controller.gameSession.get_xp_per_hour()
        self.var_xp_hr.set(f"{current_rate:,} xp / hr")
        self.var_duration.set(self._controller.gameSession.get_duration_str())
        self.last_stat_update = currentTime

    # 3. The Toggle Logic
    def toggle_topmost(self):
        """Applies the current state of the BooleanVar to the window."""
        is_top = self.var_always_on_top.get()
        self.parent.attributes("-topmost", is_top)

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
                
                item_id = self.groupTreeview.insert('', tk.END, iid=m.Name, values=values, tags=(healthTag))
            elif isNewlyJoinedPartyMember(m):
                suffixToMakeUnique = ''
                while self.groupTreeview.exists(m.Name + suffixToMakeUnique):
                    suffixToMakeUnique += '+'

                values = ('__', "__", "__", m.Name, '__', '__', '__')
                item_id = self.groupTreeview.insert('', tk.END, iid=m.Name + suffixToMakeUnique, values=values)
        
        
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

    def displayHidingLabel(self):
        self._hidingLabel.grid()
    def hideHidingLabel(self):
        self._hidingLabel.grid_remove()

    def updateMobCountInRoom(self):
        self._controller.updateMobsInCurrentRoom()
        if len(self._controller.model.currentMobsInRoom) == 0:
            self.var_count_of_mobs_in_room.set("")
        else:
            self.var_count_of_mobs_in_room.set(f"Mobs in Room: {len(self._controller.model.currentMobsInRoom)}")

    def open_pet_or_mobs_display_settings_window(self):
        self._pet_or_mobs_display_settings_window.deiconify()

    def _withdraw_pet_or_mobs_display_settings_window(self):
         self._pet_or_mobs_display_settings_window.withdraw()
    
    def update_display_of_pets_in_group_window(self, displayMobsInGroupWindow: bool):
        self._controller.update_display_of_pets_in_group_window(displayMobsInGroupWindow)

    def displayShieldEndedLabel(self):
        self.shieldEndedLabel.grid()
        self.after(self._buffOrShieldEndingDisplayTime, self.hideShieldEndedLabel)
    def hideShieldEndedLabel(self):
        self.shieldEndedLabel.grid_remove()

    def displayBlurEndedLabel(self):
        self.blurEndedLabel.grid()
        self.after(self._buffOrShieldEndingDisplayTime, self.hideBlurEndedLabel)
    def hideBlurEndedLabel(self):
        self.blurEndedLabel.grid_remove()

    def displayProtectEndedLabel(self):
        self.protectEndedLabel.grid()
        self.after(self._buffOrShieldEndingDisplayTime, self.hideProtectEndedLabel)
    def hideProtectEndedLabel(self):
        self.protectEndedLabel.grid_remove()

    def displayToughSkinEndedLabel(self):
        self.toughSkinEndedLabel.grid()
        self.after(self._buffOrShieldEndingDisplayTime, self.hideToughSkinEndedLabel)
    def hideToughSkinEndedLabel(self):
        self.toughSkinEndedLabel.grid_remove()

    #Chaos
    def displayBleedResistEndedLabel(self):
        self.bleedResistEndedLabel.grid()
        self.after(self._buffOrShieldEndingDisplayTime, self.hideBleedResistEndedLabel)
    def hideBleedResistEndedLabel(self):
        self.bleedResistEndedLabel.grid_remove()

    def displayChaosFortitudeEndedLabel(self):
        self.chaosFortitudeEndedLabel.grid()
        self.after(self._buffOrShieldEndingDisplayTime, self.hideChaosFortitudeEndedLabel)
    def hideChaosFortitudeEndedLabel(self):
        self.chaosFortitudeEndedLabel.grid_remove()

    def displayCombatEndedLabel(self):
        self.combatEndedLabel.grid()
        self.after(self._buffOrShieldEndingDisplayTime, self.hideCombatEndedLabel)
    def hideCombatEndedLabel(self):
        self.combatEndedLabel.grid_remove()

    def displayDiseaseResistEndedLabel(self):
        self.diseaseResistEndedLabel.grid()
        self.after(self._buffOrShieldEndingDisplayTime, self.hideDiseaseResistEndedLabel)
    def hideDiseaseResistEndedLabel(self):
        self.diseaseResistEndedLabel.grid_remove()

    def displayPoisonResistEndedLabel(self):
        self.poisonResistEndedLabel.grid()
        self.after(self._buffOrShieldEndingDisplayTime, self.hidePoisonResistEndedLabel)
    def hidePoisonResistEndedLabel(self):
        self.poisonResistEndedLabel.grid_remove()

    #Good
    def displayBlessEndedLabel(self):
        self.blessEndedLabel.grid()
        self.after(self._buffOrShieldEndingDisplayTime, self.hideBlessEndedLabel)
    def hideBlessEndedLabel(self):
        self.blessEndedLabel.grid_remove()

    #Evil
    def displayRegenerateEndedLabel(self):
        self.regenerateEndedLabel.grid()
        self.after(self._buffOrShieldEndingDisplayTime, self.hideRegenerateEndedLabel)
    def hideRegenerateEndedLabel(self):
        self.regenerateEndedLabel.grid_remove()

    def displayVitalizeEndedLabel(self):
        self.vitalizeEndedLabel.grid()
        self.after(self._buffOrShieldEndingDisplayTime, self.hideVitalizeEndedLabel)
    def hideVitalizeEndedLabel(self):
        self.vitalizeEndedLabel.grid_remove()
