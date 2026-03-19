from enum import Enum

class BoatNotificationBytes(Enum):
    '''Enum for bytes that indicate boat docking events.'''
    DOCKED = b'Dockhands rush to tie in the ship that has just arrived.'
    DEPARTED = b'You arrive just in time to see the crew of the ship pull up the plank leading ashore and untie the rope to the dock.'