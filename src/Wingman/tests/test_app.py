from unittest.mock import patch, mock_open
import sys
from pathlib import Path
from tkinter import messagebox

if __name__ == "__main__":
    srcDirectory = Path(__file__).parent.parent.parent.resolve()
    sys.path.append(str(srcDirectory))

from Wingman.gui.app import WingmanApp
from Wingman.core.item import Item

class TestApp():
    def test_ClosingApp_SaveSettingsInvoked(self):
        app = WingmanApp(True)

        with patch.object(app.controller, app.controller.saveSettings.__name__) as mockedSaveSettings:
            app.on_closing()

        mockedSaveSettings.assert_called_once()

    def test_FileWithBaseItemNamesCannotBeLocated_AlertsUser(self):
        Item.validBaseItemNames = set()
        with patch.object(Item, Item.load_base_item_names_from_file.__name__, side_effect=FileNotFoundError()) as mockedLoad:
            with patch.object(messagebox, messagebox.showerror.__name__) as mockedShowError:
                WingmanApp(True)

        mockedLoad.assert_called_once()
        mockedShowError.assert_called_once()
        assert Item.validBaseItemNames == set()