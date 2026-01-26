import tkinter as tk
from Wingman.core.model import Model
from Wingman.gui.view import View
from Wingman.core.controller import Controller
from Wingman.core.parser import Parser

class WingmanApp(tk.Tk):
    def __init__(self, inUnitTesting: bool = False):
        super().__init__()
        
        self.title("Wingman - 0.2.5")
        self.geometry("500x350")

        self.model = Model(Parser())

        if inUnitTesting:
            self.view = View(tk.Toplevel())
        else:
            self.view = View(self)
        
        self.configure(background='blue')
        self.bind('<Motion>', lambda e: print(f"Mouse moved to ({e.x}, {e.y}) in WingmanApp"))

        self.controller = Controller(self.model, self.view)
        self.view.set_controller(self.controller)

        self.controller.view.setup_ui()
        self.controller.view.apply_theme()
        self.controller.view.update_gui()

    def run(self):
        self.mainloop()
