import os
import tkinter as tk
from tkinter import ttk
import time
import ctypes
from Wingman.core.controller import Controller
from Wingman.core.group import Group
from Wingman.core.character import Character
from Wingman.core.health_Tagger import HealthTagger

class View(tk.Frame):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.parent = parent
        # State
        self.var_total_xp = tk.StringVar(value="Total XP: 0")
        self.var_xp_hr = tk.StringVar(value="XP/Hr: 0")
        self.var_duration = tk.StringVar(value="Time: 00:00:00")
        self.var_always_on_top = tk.BooleanVar(value=True)
        self.paused: bool = False
        self.last_stat_update = 0
        self.dark_mode = False
        self.paused = False

        self.style = ttk.Style()
        self.style.theme_use('clam')

    def set_controller(self, controller: Controller):
        self.controller = controller
        # 1. Initialize "Always on Top" variable
        self.var_always_on_top = tk.BooleanVar(value=True)
        self.parent.attributes("-topmost", self.var_always_on_top.get())
    
    def setup_ui(self):
        main_frame = ttk.Frame(self, name="main_frame", padding="10")
        main_frame.grid(row=0, column=0, sticky=tk.EW)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # --- Top Stats Row ---
        stats_frame = ttk.Frame(main_frame, name="stats_frame", height=100)
        stats_frame.grid(row=0, column=0, pady=(0, 10), sticky=tk.EW)
        stats_frame.grid_columnconfigure(1, weight=1)

        col1 = ttk.Frame(stats_frame)
        col1.grid(row=0, column=0, sticky=tk.W, padx=5, pady=10)
        ttk.Label(col1, textvariable=self.var_total_xp, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(col1, textvariable=self.var_xp_hr).pack(anchor="w")

        hospitalIcon = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'gui', 'hospitalMapIcon.png')
        self._healGroupImage = tk.PhotoImage(file=hospitalIcon)
        self._healGroupLabel = ttk.Label(stats_frame, 
                                        name='healGroupLabel', 
                                        image=self._healGroupImage)
        #Initially gridded/displayed to place it on the UI.
        #Immediately removed/hidden, only to be shown when predicate conditions are satisfied.
        self._healGroupLabel.grid(row=0, column=1)
        self._healGroupLabel.grid_remove()
        

        col2 = ttk.Frame(stats_frame)
        col2.grid(row=0, column=2, sticky=tk.E, padx=5)
        ttk.Label(col2, textvariable=self.var_duration, font=("Consolas", 10)).pack(anchor="e", pady=(0, 5))

        # Control Buttons Frame
        btns_frame = ttk.Frame(col2)
        btns_frame.pack(anchor="e")

        # Pause Button (Updated width to 8 per previous request)
        self.btn_pause = ttk.Button(btns_frame, text="Pause", command=self.toggle_pause, width=8)
        self.btn_pause.pack(side=tk.LEFT, padx=(0, 2))

        # Settings Dropdown
        self.mb_settings = ttk.Menubutton(btns_frame, text="⚙", width=3)
        self.mb_settings.pack(side=tk.LEFT)

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
        self.menu_settings.add_command(label="Reset Stats", command=self.controller.reset_stats)

        self.mb_settings["menu"] = self.menu_settings

        # --- Group Dashboard (Treeview) ---
        lbl_dash = ttk.Label(main_frame, name="groupStatusLabel", text="Group Status:", font=("Segoe UI", 10, "bold"))
        lbl_dash.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        columns = ("cls", "lvl", "status", "name", "hp", "fat", "pwr")
        self.groupTreeview = ttk.Treeview(main_frame, columns=columns, show="headings", height=8, 
                                    name='groupTreeView')

        self.groupTreeview.tag_configure(HealthTagger.HealthLevels.ZEROED.value, background='#000000', foreground='#ffffff')
        self.groupTreeview.tag_configure(HealthTagger.HealthLevels.AT_OR_BELOW_25.value, background='#ff0000')
        self.groupTreeview.tag_configure(HealthTagger.HealthLevels.AT_OR_BELOW_50.value, background="#FFFF00")

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

        self.parent.configure(bg=bg_color)
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
            if hasattr(self.controller.session, 'pause_clock'): self.controller.session.pause_clock()
        else:
            self.btn_pause.config(text="Pause")
            if hasattr(self.controller.session, 'resume_clock'): self.controller.session.resume_clock()
    
    def set_windows_titlebar_color(self, use_dark: bool):
        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
            get_parent = ctypes.windll.user32.GetParent
            hwnd = get_parent(self.parent.winfo_id())
            value = 1 if use_dark else 0
            set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(ctypes.c_int(value)), 4)
            self.update()
        except Exception:
            pass

    def update_gui(self):
        self.after(100, self.update_gui)
        if self.paused: return
        self.controller.session.process_queue()
        group_data = self.controller.session.Group
        if group_data or self.controller.session.shouldRefreshGroupDisplay:
            self._refresh_tree(group_data)
        current_xp = self.controller.session.total_xp
        self.var_total_xp.set(f"Total XP: {current_xp:,}")
        now = time.time()
        if now - self.last_stat_update >= 1.0:
            current_rate = self.controller.session.get_xp_per_hour()
            self.var_xp_hr.set(f"{current_rate:,} xp / hr")
            self.var_duration.set(self.controller.session.get_duration_str())
            self.last_stat_update = now

    # 3. The Toggle Logic
    def toggle_topmost(self):
        """Applies the current state of the BooleanVar to the window."""
        is_top = self.var_always_on_top.get()
        self.parent.attributes("-topmost", is_top)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def reset_stats(self):
        self.controller.session.reset()
        for item in self.groupTreeview.get_children():
            self.groupTreeview.delete(item)

    def displayHealGroupImage(self):
        self._healGroupLabel.grid()
    
    def hideHealGroupImage(self):
        self._healGroupLabel.grid_remove()

    def _refresh_tree(self, group: Group):
        def isCurrentPartyMember(m: Character):
            return m.ClassProfession != ""

        def isNewlyJoinedPartyMember(m: Character):
            return m.ClassProfession == "" and m.IsNewGroupFollower

        for item in self.groupTreeview.get_children():
            self.groupTreeview.delete(item)
        for m in group.Members:
            if isCurrentPartyMember(m):
                values = (m.ClassProfession, m.Level, str(m.Status), m.Name, str(m.Hp), str(m.Fat), str(m.Pow))
                
                healthTag = HealthTagger.HealthTag(m)
                
                item_id = self.groupTreeview.insert('', tk.END, iid=m.Name, values=values, tags=(healthTag))
            elif isNewlyJoinedPartyMember(m):
                suffixToMakeUnique = ''
                while self.groupTreeview.exists(m.Name + suffixToMakeUnique):
                    suffixToMakeUnique += '+'

                values = ('__', "__", "__", m.Name, '__', '__', '__')
                item_id = self.groupTreeview.insert('', tk.END, iid=m.Name + suffixToMakeUnique, values=values)
        
        
        if group.DisplayHealingIcon:
            self.displayHealGroupImage() #TODO: determine better way to externally indicate Image is displaying. Tying to implementation detail.
        else:
            self.hideHealGroupImage()

        self.controller.session.shouldRefreshGroupDisplay = False
