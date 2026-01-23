import tkinter as tk
from Wingman.core.input_receiver import InputReceiver
from Wingman.core.session import GameSession
from Wingman.core.network_listener import NetworkListener

class Controller:
    def __init__(self, model, view):
        from Wingman.gui.view import View #TODO: Confirm whether valid workaround for circular import
        assert isinstance(view, View)
        self.model = model
        self.view = view
        
        # Create the SHARED receiver
        shared_receiver = InputReceiver()
        self.listener = NetworkListener(shared_receiver) # Pass it to both
        session = GameSession(shared_receiver)
        self.session = session

        self.listener.start()
        
    def reset_stats(self):
        self.view.reset_stats()
    
