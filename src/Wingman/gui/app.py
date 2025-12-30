import tkinter as tk
import time
from tkinter import ttk
from Wingman.core.session import GameSession


class XPTrackerApp:
    def __init__(self, session: GameSession):
        self.session = session

        self.last_stat_update = 0

        self.root = tk.Tk()
        self.root.title("Wingman - 0.2.4")
        self.root.geometry("500x350")  # Widened slightly for the columns
        self.root.attributes("-topmost", True)

        self.var_total_xp = tk.StringVar(value="Total XP: 0")
        self.var_xp_hr = tk.StringVar(value="XP/Hr: 0")
        self.var_duration = tk.StringVar(value="Time: 00:00:00")

        self.setup_ui()
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

        # Column 2: Time & Reset
        col2 = ttk.Frame(stats_frame)
        col2.pack(side=tk.RIGHT, padx=5)
        ttk.Label(col2, textvariable=self.var_duration, font=("Consolas", 10)).pack(anchor="e")
        ttk.Button(col2, text="Reset", command=self.reset_stats, width=6).pack(pady=2)

        # --- Group Dashboard (Treeview) ---
        lbl_dash = ttk.Label(main_frame, text="Group Status:", font=("Segoe UI", 10, "bold"))
        lbl_dash.pack(anchor="w", pady=(5, 0))

        # Define Columns
        columns = ("cls", "lvl", "status", "name", "hp", "fat", "pwr")  # Added "status"
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=8)

        # Setup Headings
        self.tree.heading("cls", text="Class")
        self.tree.heading("lvl", text="Lvl")
        self.tree.heading("status", text="Sts")  # Short header to save space
        self.tree.heading("name", text="Name")
        self.tree.heading("hp", text="HP")
        self.tree.heading("fat", text="Fatigue")
        self.tree.heading("pwr", text="Power")

        # Setup Columns Widths
        self.tree.column("cls", width=50, anchor="center")
        self.tree.column("lvl", width=40, anchor="center")
        self.tree.column("status", width=30, anchor="center")  # Narrow column
        self.tree.column("name", width=100, anchor="w")
        self.tree.column("hp", width=80, anchor="center")
        self.tree.column("fat", width=80, anchor="center")
        self.tree.column("pwr", width=80, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

    def reset_stats(self):
        self.session.reset()
        # Clear the tree
        for item in self.tree.get_children():
            self.tree.delete(item)

    def update_gui(self):
        # --- FAST UPDATES (Every 100ms) ---
        # 1. Process Queue (Instant logs)
        self.session.process_queue()

        # 2. Update Group Dashboard (Instant status changes)
        group_data = self.session.get_latest_group_data()
        if group_data:
            self._refresh_tree(group_data)

        # 3. Update Total XP (Instant gratification)
        # We update the total immediately, so it matches the log text appearing
        current_xp = self.session.total_xp
        self.var_total_xp.set(f"Total XP: {current_xp:,}")

        # --- THROTTLED UPDATES (Every 1.0s) ---
        now = time.time()
        if now - self.last_stat_update >= 1.0:
            # Update XP/Hr
            current_rate = self.session.get_xp_per_hour()
            self.var_xp_hr.set(f"{current_rate:,} xp / hr")

            # Update Duration Timer
            self.var_duration.set(self.session.get_duration_str())

            # Reset the timer
            self.last_stat_update = now

        # Schedule next loop
        self.root.after(100, self.update_gui)

    def _refresh_tree(self, members):
        """Clears and refills the treeview."""
        # Clear current list
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Refill
        for m in members:
            # Add m['status'] to the tuple
            values = (m['cls'], m['lvl'], m['status'], m['name'], m['hp'], m['fat'], m['pwr'])
            self.tree.insert("", tk.END, values=values)

    def run(self):
        self.root.mainloop()