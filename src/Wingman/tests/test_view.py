import pytest
import tkinter as tk
from unittest.mock import Mock, patch
from Wingman.gui.view import View
from Wingman.core.controller import Controller
from Wingman.core.parser import Parser

class TestView():
    def test_SettingController(self):
        v = View.ForTesting()

        assert isinstance(v, View)

    class TestHealGroupLabelDisplay:
        def test_HealGroupIcon_DisplaysWhenAnyGroupMemberZeroed(self):
            c = Controller.ForTesting()
            v = c.view
            c.receiver.receive("""Foo's group:
    [Bar            01]            Foo                 51/ 100 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   
    [Baz            01]            Fuzz                 1/ 50  (  0%)       50/  50 (100%)     50/ 50  (100%)
    [Duck           01]            Head               500/ 500 (  0%)      500/ 500 (100%)     50/ 50  (100%)""")
            
            with patch.object(v, f'{v.displayHealGroupImage.__name__}') as mockedMethod:
                v.update_gui()
            
            
            assert v._healGroupLabel.winfo_viewable() == 0  # display updates aren't performed (unreliable state) until `mainloop` is able to run freely
            mockedMethod.assert_called_once_with()

        def test_HealGroupIcon_WhileInitiallyDisplayed_RemovedAfterHealthGuiUpdateShowsNonZeroed(self):
            c = Controller.ForTesting()
            v = c.view
            c.receiver.receive('[Baz            01]            Fuzz                 1/ 50  (  0%)       50/  50 (100%)     50/ 50  (100%)')
            v.update_gui()
            c.receiver.receive("""Fuzz's group:
    [Baz            01]            Fuzz                 2/ 50  (  0%)       50/  50 (100%)     50/ 50  (100%)""")

            path = f'{View.hideHealGroupImage.__name__}'
            with patch.object(v, f'{View.hideHealGroupImage.__name__}') as mockedMethod:
                v.update_gui()

            mockedMethod.assert_called_once_with()

    def test_ViewWithoutSetController_WhenUiUpdated_RaisesError(self):
        v = View(tk.Toplevel())

        with pytest.raises(AttributeError):
            v.update_gui()

    class TestAfkLabelDisplay:
        def test_AfkLabelDisplays_WhenAfkStatusReceived(self):
            c = Controller.ForTesting()
            v = c.view
            c.receiver.receive(Parser.AfkStatus.BeginAfk.value)

            with patch.object(v, f'{View.displayAfkLabel.__name__}') as mockedDisplay:
                v.update_gui()
            
            mockedDisplay.assert_called_once_with()
        
        def test_AfkLabelHides_WhenNoLongerAfkStatusReceived(self):
            c = Controller.ForTesting()
            v = c.view
            c.receiver.receive(Parser.AfkStatus.EndAfk.value)

            with patch.object(v, f'{View.hideAfkLabel.__name__}') as mockedHide:
                v.update_gui()
            
            mockedHide.assert_called_once_with()

        def test_NonAfkInput_NeitherDisplayNorHideInvoked(self):
            c = Controller.ForTesting()
            v = c.view
            c.receiver.receive("AFK in input but nothing invoked.")

            with patch.object(v, f'{View.displayAfkLabel.__name__}') as mockedDisplay:
                with patch.object(v, f'{View.hideAfkLabel.__name__}') as mockedHide:
                    v.update_gui()
            
            mockedDisplay.assert_not_called()
            mockedHide.assert_not_called()
