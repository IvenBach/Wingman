import tkinter as tk
from Wingman.core.model import Model
from Wingman.gui.view import View
from Wingman.core.controller import Controller

class WingmanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Wingman - 0.2.5")
        self.geometry("500x350")

        model = Model()

        view = View(self)
        view.grid(row=0, column=0)

        self.controller = Controller(model, view)
        view.set_controller(self.controller)

        self.controller.view.setup_ui()
        self.controller.view.apply_theme()
        self.controller.view.update_gui()

    def run(self):
        self.mainloop()
