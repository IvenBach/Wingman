import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from Wingman.core.model import Model
from Wingman.gui.view import View
from Wingman.core.controller import Controller
from Wingman.core.parsing.parser import Parser
from Wingman.core.item import Item

class WingmanApp(tk.Tk):
    def __init__(self, inUnitTesting: bool = False):
        super().__init__()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.title("Wingman - 0.2.5")
        self.geometry("500x350")

        self.model = Model(Parser())

        if inUnitTesting:
            self.view = View(tk.Toplevel())
        else:
            self.view = View(self)

        self.controller = Controller(self.model, self.view)
        self.view.set_controller(self.controller)

        self.controller.view.setup_ui()
        self.controller.view.apply_theme()
        self.controller.view.update_gui()

        try:
            srcDirectory = Path(__file__).parent.parent.resolve()
            base_item_names_path = str(Path(srcDirectory).joinpath('data/baseItemNames.txt'))
            Item.load_base_item_names_from_file(base_item_names_path)
        except FileNotFoundError as e:
            messageText = f"Could not find the file `{base_item_names_path}` containing base item names. Wingman will continue to run, but some item parsing may not work correctly.\n\nContact the developer if you need assistance resolving this issue."
            messagebox.showerror(f"Error:", messageText)

        settings = self.controller.loadSettings()
        self.controller.applySettings(settings)


    def run(self):
        self.mainloop()

    def on_closing(self):
        self.controller.saveSettings()
        self.destroy()