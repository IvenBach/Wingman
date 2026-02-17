import pytest
import tkinter as tk
from unittest.mock import Mock, patch, call
import sys
from pathlib import Path
if __name__ == "__main__":
    srcDirectory = Path(__file__).parent.parent.parent.resolve()
    sys.path.append(str(srcDirectory))
from Wingman.gui.view import View
from Wingman.core.controller import Controller
from Wingman.core.parser import Parser
from Wingman.core.model import Model

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
            
            # Edge case of moving while AFK will overwrite the models AFK state before gui can update.
            # Called as part of `update_gui` and inside view._controller.process_queue
            # that is why `assert_called_with()` is used instead of `assert_called_once_with()`
            mockedHide.assert_called_with()
            assert mockedHide.call_args_list == [call(), call()]

        def test_NonAfkInput_NeitherDisplayNorHideInvoked(self):
            c = Controller.ForTesting()
            v = c.view
            c.receiver.receive("AFK in input but nothing invoked.")

            with patch.object(v, f'{View.displayAfkLabel.__name__}') as mockedDisplay:
                with patch.object(v, f'{View.hideAfkLabel.__name__}') as mockedHide:
                    v.update_gui()
            
            mockedDisplay.assert_not_called()
            mockedHide.assert_not_called()

    def test_ViewInitiallyIncludesPets_DeselectedFromView_WhenUpdateMethodInvokedPetsAreRemoved(self):
        m = Model(Parser())
        m.includePetsInGroup = True
        v = View(tk.Toplevel())
        v.var_includePetsInGroup.set(True)
        c = Controller.ForTesting(m, v)
        c.receiver.receive("""Beautiful's group:

[ Class      Lv] Status   Name              Hits            Fat             Power         
[Sin         74]         Beautiful        500/500 (100%)  500/500 (100%)  687/731 ( 93%)  
[mob         72]         angel of death   417/417 (100%)  417/417 (100%)  618/618 (100%)  """)
        c.process_queue()

        groupCountWithPetsIncluded = c.gameSession.group.Count
        #https://tkdocs.com/shipman/ttk-Checkbutton.html - Not supported are the following methods of the Tkinter Checkbutton widget: .deselect(), .flash(), .select(), and .toggle(). To change the state of a checkbutton through program control, use the .set() method of the associated control variable.
        # Checking for change on button state is done directly on the backing `BooleanVar`.
        v.var_includePetsInGroup.set(False) 
        v.update_display_of_pets_in_group_window(v.var_includePetsInGroup.get())
        
        assert groupCountWithPetsIncluded == 2
        assert c.gameSession.group.Count == 1

    def test_CachedGroupMatchesCurrentGroup_GroupDisplayNotRefreshed(self):
        c = Controller.ForTesting()
        v = c.view
        c.receiver.receive("""Beautiful's group:

[ Class      Lv] Status   Name              Hits            Fat             Power         
[Sin         74]         Beautiful        500/500 (100%)  500/500 (100%)  687/731 ( 93%)  
[mob         72]         angel of death   417/417 (100%)  417/417 (100%)  618/618 (100%)  """)
        v.update_gui() # Update once to cache the group

        with patch.object(v, v.refreshGroupDisplay.__name__) as mockedRefresh:
            v.update_gui()

        mockedRefresh.assert_not_called()

    def test_CachedGroupDoesNotMatchCurrentGroup_GroupDisplayRefreshed(self):
        c = Controller.ForTesting()
        v = c.view
        c.receiver.receive("""Beautiful's group:

[ Class      Lv] Status   Name              Hits            Fat             Power         
[Sin         74]         Beautiful        500/500 (100%)  500/500 (100%)  687/731 ( 93%)  
[Skeleton    72]         Bones            417/417 (100%)  417/417 (100%)   50/ 50 (100%)  """)
        v.update_gui() # Update once to cache the group

        c.receiver.receive("""Beautiful's group:

[ Class      Lv] Status   Name              Hits            Fat             Power         
[Sin         74]         Beautiful        75/500 ( 60%)  500/500 (100%)  687/731 ( 93%)  
[Skeleton    72]         Bones            417/417 (100%)  417/417 (100%)   50/ 50 (100%)  """)

        with patch.object(v, v.refreshGroupDisplay.__name__) as mockedRefresh:
            v.update_gui()

        mockedRefresh.assert_called_once()

    class TestBuffOrShieldEndingDisplay:
        @pytest.mark.parametrize("endingEnumMember", [Parser.ParseBuffOrShieldText.Shield_Ended,
                                                        Parser.ParseBuffOrShieldText.Blur_Ended,
                                                        Parser.ParseBuffOrShieldText.Protect_Ended,
                                                        Parser.ParseBuffOrShieldText.ToughDotSkin_Ended,
                                                        #Chaos
                                                        Parser.ParseBuffOrShieldText.BleedDotResist_Ended,
                                                        Parser.ParseBuffOrShieldText.ChaosDotFortitude_Ended,
                                                        Parser.ParseBuffOrShieldText.Combat_Ended,
                                                        Parser.ParseBuffOrShieldText.DiseaseDotResist_Ended,
                                                        Parser.ParseBuffOrShieldText.PoisonDotResist_Ended,
                                                        #Good
                                                        Parser.ParseBuffOrShieldText.Bless_Ended,
                                                        #Evil
                                                        Parser.ParseBuffOrShieldText.Regenerate_Ended,
                                                        Parser.ParseBuffOrShieldText.Vitalize_Ended
                                                    ],
                                                    ids=["Shield refresh",
                                                        "Blur refresh",
                                                        "Protect refresh",
                                                        "Tough Skin refresh",
                                                        #Chaos
                                                        "Chaos - Bleed Resist refresh",
                                                        "Chaos - Chaos Fortitude refresh",
                                                        "Chaos - Combat refresh",
                                                        "Chaos - Disease Resist refresh",
                                                        "Chaos - Poison Resist refresh",
                                                        #Good
                                                        "Good - Bless refresh",
                                                        #Evil
                                                        "Evil - Regenerate refresh",
                                                        "Evil - Vitalize refresh"
                                                    ]
        )
        def test_BuffOrShieldEnds_LabelDisplayed(self, endingEnumMember: Parser.ParseBuffOrShieldText):
            c = Controller.ForTesting()
            v = c.view
            c.receiver.receive(endingEnumMember.value)

            with patch.object(v, f'{v.displayBuffOrShieldEndedLabel.__name__}') as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_called_once_with(endingEnumMember)

        @pytest.mark.parametrize("text", [Parser.ParseBuffOrShieldText.Shield_Ended.value + Parser.ParseBuffOrShieldText.ShieldStarts.value,
                                            Parser.ParseBuffOrShieldText.Blur_Ended.value + Parser.ParseBuffOrShieldText.BlurStarts.value,
                                            Parser.ParseBuffOrShieldText.Protect_Ended.value + Parser.ParseBuffOrShieldText.ProtectStarts.value,
                                            Parser.ParseBuffOrShieldText.ToughDotSkin_Ended.value + Parser.ParseBuffOrShieldText.ToughDotSkinStarts.value,
                                            #Chaos
                                            Parser.ParseBuffOrShieldText.BleedDotResist_Ended.value + Parser.ParseBuffOrShieldText.BleedDotResistStarts.value,
                                            Parser.ParseBuffOrShieldText.ChaosDotFortitude_Ended.value + Parser.ParseBuffOrShieldText.ChaosDotFortitudeStarts.value,
                                            Parser.ParseBuffOrShieldText.Combat_Ended.value + Parser.ParseBuffOrShieldText.CombatStarts.value,
                                            Parser.ParseBuffOrShieldText.DiseaseDotResist_Ended.value + Parser.ParseBuffOrShieldText.DiseaseDotResistStarts.value,
                                            Parser.ParseBuffOrShieldText.PoisonDotResist_Ended.value + Parser.ParseBuffOrShieldText.PoisonDotResistStarts.value,
                                            #Good
                                            Parser.ParseBuffOrShieldText.Bless_Ended.value + Parser.ParseBuffOrShieldText.BlessStarts.value,
                                            #Evil
                                            Parser.ParseBuffOrShieldText.Regenerate_Ended.value + Parser.ParseBuffOrShieldText.RegenerateStarts.value,
                                            Parser.ParseBuffOrShieldText.Vitalize_Ended.value + Parser.ParseBuffOrShieldText.VitalizeStarts.value
                                        ],
                                        ids=["Shield refresh",
                                            "Blur refresh",
                                            "Protect refresh",
                                            "Tough Skin refresh",
                                            #Chaos
                                            "Chaos - Bleed Resist refresh",
                                            "Chaos - Fortitude refresh",
                                            "Chaos - Combat refresh",
                                            "Chaos - Disease Resist refresh",
                                            "Chaos - Poison Resist refresh",
                                            #Good
                                            "Good - Bless refresh",
                                            #Evil
                                            "Evil - Regenerate refresh",
                                            "Evil - Vitalize refresh"
                                        ]
        )
        def test_BuffOrShieldRefreshed_LabelNotDisplayed(self, text):
            c = Controller.ForTesting()
            v = c.view
            c.receiver.receive(text)

            with patch.object(v, f'{v.displayBuffOrShieldEndedLabel.__name__}') as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_not_called()

        def test_NonBuffOrShieldText_LabelNeitherDisplayedNorHidden(self):
            c = Controller.ForTesting()
            v = c.view
            c.receiver.receive("Text not related to buff or shield ending.")

            with patch.object(v, f'{v.displayBuffOrShieldEndedLabel.__name__}') as mockedDisplay:
                with patch.object(v, f'{v.hideBuffOrShieldEndedLabel.__name__}') as mockedHide:
                    v.update_gui()

            mockedDisplay.assert_not_called()
            mockedHide.assert_not_called()

        @pytest.mark.parametrize("input,expectedToContain", [(Parser.ParseBuffOrShieldText.BleedDotResist_Ended.value, "Bleed.Resist"),
                                                             (Parser.ParseBuffOrShieldText.Bless_Ended.value, "Bless Ended")],
                                            ids=["`Dot` in name replaced with `.` (period) character.",
                                                 "`_` (underscore) in name replaced with ` ` (space) character."])
        def test_BuffOrShieldEnded_LabelToBeUpdatedWithEnumMemberValueContaining__SpecificString__ReplacedWith__ExpectedCharacter(self, input, expectedToContain):
            c = Controller.ForTesting()
            v = c.view
            c.receiver.receive(input)

            v.update_gui()
            actualText = v.var_buffOrShieldEndingText.get()

            assert actualText.__contains__(expectedToContain)

    class TestSpellMitigationDisplay:
        def test_SpellMitigationInputReceived_LabelDisplayed(self):
            c = Controller.ForTesting()
            v = c.view
            c.receiver.receive(Parser.ParseSpellMitigationAffect.BleedDotResist.value)

            v.update_gui()
            actualText = v.var_spellMitigatesAffectText.get()

            assert actualText.__contains__("Bleed.Resist")

        def test_NonSpellMitigationText_LabelNotDisplayed(self):
            c = Controller.ForTesting()
            v = c.view
            c.receiver.receive("Text not related to spell mitigation.")

            with patch.object(v, f'{v.displaySpellMitigatesAffectLabel.__name__}') as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_not_called()
