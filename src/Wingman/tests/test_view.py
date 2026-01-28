import pytest
import tkinter as tk
from unittest.mock import Mock, patch
from Wingman.gui.view import View
from Wingman.gui.app import WingmanApp


class TestView():
    def test_SettingController(self):
        v = View.ForTesting()

        assert isinstance(v, View)

    def test_HealGroupIcon_DisplaysWhenAnyGroupMemberZeroed(self):
        app = WingmanApp(True)
        app.controller.receiver.receive("""Foo's group:
[Bar            01]            Foo                 51/ 100 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   
[Baz            01]            Fuzz                 1/ 50  (  0%)       50/  50 (100%)     50/ 50  (100%)
[Duck           01]            Head               500/ 500 (  0%)      500/ 500 (100%)     50/ 50  (100%)""")
        
        with patch.object(app.controller.view, f'{View.displayHealGroupImage.__name__}') as mockedMethod:
            app.view.update_gui()
        
        
        assert app.view._healGroupLabel.winfo_viewable() == 0  # display updates aren't performed (unreliable state) until `mainloop` is able to run freely
        mockedMethod.assert_called_once_with()

    def test_HealGroupIcon_WhileInitiallyDisplayed_RemovedAfterHealthGuiUpdateShowsNonZeroed(self):
        app = WingmanApp(True)
        app.controller.receiver.receive('[Baz            01]            Fuzz                 1/ 50  (  0%)       50/  50 (100%)     50/ 50  (100%)')
        app.controller.view.update_gui()
        app.controller.receiver.receive("""Fuzz's group:
[Baz            01]            Fuzz                 2/ 50  (  0%)       50/  50 (100%)     50/ 50  (100%)""")

        path = f'{View.hideHealGroupImage.__name__}'
        with patch.object(app.controller.view, f'{View.hideHealGroupImage.__name__}') as mockedMethod:
            app.controller.view.update_gui()

        mockedMethod.assert_called_once_with()

    def test_ViewWithoutSetController_WhenUiUpdated_RaisesError(self):
        v = View(tk.Toplevel())

        with pytest.raises(AttributeError):
            v.update_gui()
