from unittest.mock import patch
import sys
from pathlib import Path
if __name__ == "__main__":
    srcDirectory = Path(__file__).parent.parent.parent.resolve()
    sys.path.append(str(srcDirectory))

from Wingman.gui.app import WingmanApp

class TestApp():
    def test_ClosingApp_SaveSettingsInvoked(self):
        app = WingmanApp(True)

        with patch.object(app.controller, app.controller.saveSettings.__name__) as mockedSaveSettings:
            app.on_closing()

        mockedSaveSettings.assert_called_once()
