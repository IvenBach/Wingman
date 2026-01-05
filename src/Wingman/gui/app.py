import tkinter as tk
import time
import ctypes
from tkinter import ttk
from Wingman.core.session import GameSession
from Wingman.core.parser import Group, Character

class XPTrackerApp:
    def __init__(self, session: GameSession):
        self.session = session
        self.last_stat_update = 0

        # State
        self.dark_mode = False
        self.paused = False

        self.root = tk.Tk()
        self.root.title("Wingman - 0.2.5")
        self.root.geometry("500x350")

        # 1. Initialize "Always on Top" variable
        self.var_always_on_top = tk.BooleanVar(value=True)
        self.root.attributes("-topmost", self.var_always_on_top.get())

        self.var_total_xp = tk.StringVar(value="Total XP: 0")
        self.var_xp_hr = tk.StringVar(value="XP/Hr: 0")
        self.var_duration = tk.StringVar(value="Time: 00:00:00")

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.setup_ui()
        self.apply_theme()

        self.update_gui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Top Stats Row ---
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        # Column 1: Totals
        col1 = ttk.Frame(stats_frame)
        col1.pack(side=tk.LEFT, padx=5)
        ttk.Label(col1, textvariable=self.var_total_xp, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(col1, textvariable=self.var_xp_hr).pack(anchor="w")

        # Column 2: Controls
        col2 = ttk.Frame(stats_frame)
        col2.pack(side=tk.RIGHT, padx=5)
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
        self.menu_settings.add_command(label="Reset Stats", command=self.reset_stats)

        self.mb_settings["menu"] = self.menu_settings

        # --- Group Dashboard (Treeview) ---
        lbl_dash = ttk.Label(main_frame, text="Group Status:", font=("Segoe UI", 10, "bold"))
        lbl_dash.pack(anchor="w", pady=(5, 0))

        columns = ("cls", "lvl", "status", "name", "hp", "fat", "pwr")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=8)

        self.tree.heading("cls", text="Class");
        self.tree.heading("lvl", text="Lvl")
        self.tree.heading("status", text="Status");
        self.tree.heading("name", text="Name")
        self.tree.heading("hp", text="HP");
        self.tree.heading("fat", text="Fatigue")
        self.tree.heading("pwr", text="Power")

        self.tree.column("cls", width=50, anchor="center")
        self.tree.column("lvl", width=40, anchor="center")
        self.tree.column("status", width=30, anchor="center")
        self.tree.column("name", width=100, anchor="w")
        self.tree.column("hp", width=80, anchor="center")
        self.tree.column("fat", width=80, anchor="center")
        self.tree.column("pwr", width=80, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

    # 3. The Toggle Logic
    def toggle_topmost(self):
        """Applies the current state of the BooleanVar to the window."""
        is_top = self.var_always_on_top.get()
        self.root.attributes("-topmost", is_top)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.btn_pause.config(text="Resume")
            if hasattr(self.session, 'pause_clock'): self.session.pause_clock()
        else:
            self.btn_pause.config(text="Pause")
            if hasattr(self.session, 'resume_clock'): self.session.resume_clock()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        if self.dark_mode:
            bg_color = "#2b2b2b";
            fg_color = "#ffffff";
            field_bg = "#383838";
            select_bg = "#4a6984"
            self.set_windows_titlebar_color(True)
        else:
            bg_color = "#f0f0f0";
            fg_color = "#000000";
            field_bg = "#ffffff";
            select_bg = "#0078d7"
            self.set_windows_titlebar_color(False)

        self.root.configure(bg=bg_color)
        self.style.configure(".", background=bg_color, foreground=fg_color, fieldbackground=field_bg)
        self.style.configure("Treeview", background=field_bg, foreground=fg_color, fieldbackground=field_bg)
        self.style.map("Treeview", background=[("selected", select_bg)], foreground=[("selected", "white")])
        self.style.configure("Treeview.Heading", background=bg_color, foreground=fg_color, relief="flat")
        self.style.configure("TMenubutton", background=bg_color, foreground=fg_color)
        self.menu_settings.config(bg=field_bg, fg=fg_color, activebackground=select_bg, activeforeground="white")

    def set_windows_titlebar_color(self, use_dark: bool):
        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
            get_parent = ctypes.windll.user32.GetParent
            hwnd = get_parent(self.root.winfo_id())
            value = 1 if use_dark else 0
            set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(ctypes.c_int(value)), 4)
            self.root.update()
        except Exception:
            pass

    def reset_stats(self):
        self.session.reset()
        for item in self.tree.get_children():
            self.tree.delete(item)

    def update_gui(self):
        self.root.after(100, self.update_gui)
        if self.paused: return
        self.session.process_queue()
        group_data = self.session.Group
        if group_data or self.session.shouldRefreshGroupDisplay:
            self._refresh_tree(group_data)
        current_xp = self.session.total_xp
        self.var_total_xp.set(f"Total XP: {current_xp:,}")
        now = time.time()
        if now - self.last_stat_update >= 1.0:
            current_rate = self.session.get_xp_per_hour()
            self.var_xp_hr.set(f"{current_rate:,} xp / hr")
            self.var_duration.set(self.session.get_duration_str())
            self.last_stat_update = now


    def _refresh_tree(self, group: Group):
        def isCurrentPartyMember(m: Character):
            return m.ClassProfession != ""

        def isNewlyJoinedPartyMember(m: Character):
            return m.ClassProfession == "" and m.IsNewGroupFollower

        for item in self.tree.get_children():
            self.tree.delete(item)
        for m in group.Members:
            if isCurrentPartyMember(m):
                values = (m.ClassProfession, m.Level, str(m.Status), m.Name, str(m.Hp), str(m.Fat), str(m.Pow))
                item_id = self.tree.insert('', tk.END, iid=m.Name, values=values)
                self.tree.see(item_id)
            elif isNewlyJoinedPartyMember(m):
                suffixToMakeUnique = ''
                while self.tree.exists(m.Name + suffixToMakeUnique):
                    suffixToMakeUnique += '+'

                values = ('__', "__", "__", m.Name, '__', '__', '__')
                item_id = self.tree.insert('', tk.END, iid=m.Name + suffixToMakeUnique, values=values)
                self.tree.see(item_id)
        
        self.session.shouldRefreshGroupDisplay = False

    def run(self):
        self.root.mainloop()