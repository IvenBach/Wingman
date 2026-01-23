from tkinter import Widget
from unittest.mock import Mock, patch
import pytest
from Wingman.core.health_Tagger import HealthTagger
from Wingman.gui.app import WingmanApp
from Wingman.core.session import GameSession
from Wingman.core.input_receiver import InputReceiver

class TestApp():
    def test_GainNewFollower_NewFollowerAddedToGroupForDisplay(self):
        receiver = InputReceiver()
        session = GameSession(receiver)
        app = WingmanApp(session)
        receiver.receive("""Beautiful's group:

[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Sin            69]           Beautiful            500/ 500 (100%)    497/ 500 ( 99%)    592/ 707 ( 83%)   
[Skelton        50]           Skeletor             396/ 396 (100%)    396/ 396 (100%)    554/ 554 (100%) """)
        app.update_gui()
        groupCountBeforeNewFollower = len(app.tree.get_children())

        receiver.receive("FooBar follows you")
        app.update_gui()
        groupCountAfterNewFollower = len(app.tree.get_children())

        assert groupCountBeforeNewFollower == 2
        assert groupCountAfterNewFollower == 3
    
    def test_LoseFollower_FollowerRemovedFromGroupForDisplay(self):
        receiver = InputReceiver()
        session = GameSession(receiver)
        app = WingmanApp(session)
        receiver.receive("""Beautiful's group:

[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Sin            69]           Beautiful            500/ 500 (100%)    497/ 500 ( 99%)    592/ 707 ( 83%)   
[Apple           1]           Foo                  100/ 200 (100%)    150/ 300 ( 50%)    250/ 500 ( 50%)   
[Skelton        50]           Skeletor             396/ 396 (100%)    396/ 396 (100%)    554/ 554 (100%) """)
        app.update_gui()
        groupCountBeforeLosingFollower = len(app.tree.get_children())

        receiver.receive("Foo disbands from the group.")
        app.update_gui()
        groupCountAfterLosingFollower = len(app.tree.get_children())

        assert groupCountBeforeLosingFollower == 3
        assert groupCountAfterLosingFollower == 2
    
    def test_GainNewFollowerAndLoseFollower_WithoutInvokingGroupCommand_CountsCorrectlyForAdditionAndRemoval(self):
        receiver = InputReceiver()
        session = GameSession(receiver)
        app = WingmanApp(session)
        receiver.receive("""Beautiful's group:

[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Sin            69]           Beautiful            500/ 500 (100%)    497/ 500 ( 99%)    592/ 707 ( 83%)   
[Skelton        50]           Skeletor             396/ 396 (100%)    396/ 396 (100%)    554/ 554 (100%) """)
        app.update_gui()
        groupCountInitial = len(app.tree.get_children())

        receiver.receive("NewFollower follows you")
        app.update_gui()
        groupCountAfterNewFollower = len(app.tree.get_children())

        receiver.receive("NewFollower disbands from the group.")
        app.update_gui()
        groupCountAfterLosingFollower = len(app.tree.get_children())

        assert groupCountInitial == 2
        assert groupCountAfterNewFollower == 3
        assert groupCountAfterLosingFollower == 2

    def test_FollowedByTwoIdenticallyDisguisedCharacters_BothAddedToGroupForDisplay(self):
        receiver = InputReceiver()
        session = GameSession(receiver)
        app = WingmanApp(session)
        receiver.receive("""Beautiful's group:

[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Sin            69]           Beautiful            500/ 500 (100%)    497/ 500 ( 99%)    592/ 707 ( 83%)   """)
        app.update_gui()
        unfollowedGroupCount = len(app.tree.get_children())

        receiver.receive("A primeval eldritch voidwolf follows you")
        app.update_gui()
        groupCountAfterFirstFollower = len(app.tree.get_children())

        receiver.receive("A primeval eldritch voidwolf follows you")
        app.update_gui()
        groupCountAfterSecondFollower = len(app.tree.get_children())

        assert unfollowedGroupCount == 1
        assert groupCountAfterFirstFollower == 2
        assert groupCountAfterSecondFollower == 3    

    def test_GroupMemberZeroed_DisplaysZeroedFormatting(self):
        receiver = InputReceiver()
        session = GameSession(receiver)
        app = WingmanApp(session)
        receiver.receive("""Foo's group:
[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Bar            01]            Foo                 1/ 500 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   """)
        
        app.update_gui()
        member = app.tree.get_children()[0]
        healthTags = app.tree.item(member, 'tags')

        assert HealthTagger.HealthLevels.ZEROED.value in healthTags
    
    def test_GroupMemberInRedHealth_DisplaysRedHealthFormatting(self):
        receiver = InputReceiver()
        session = GameSession(receiver)
        app = WingmanApp(session)
        receiver.receive("[Bar            01]            Foo                 25/ 100 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   """)
        app.update_gui()
        member = app.tree.get_children()[0]

        healthTags = app.tree.item(member, 'tags')

        assert HealthTagger.HealthLevels.AT_OR_BELOW_25.value in healthTags

    def test_GroupMemberInYellowHealth_DisplaysYellowHealthFormatting(self):
        receiver = InputReceiver()
        session = GameSession(receiver)
        app = WingmanApp(session)
        receiver.receive("[Bar            01]            Foo                 50/ 100 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   ")
        app.update_gui()
        member = app.tree.get_children()[0]
        
        healthTags = app.tree.item(member, 'tags')

        assert HealthTagger.HealthLevels.AT_OR_BELOW_50.value in healthTags
    
    def test_GroupMemberInGoodHealth_DisplaysNoHealthFormatting(self):
        receiver = InputReceiver()
        session = GameSession(receiver)
        app = WingmanApp(session)
        receiver.receive("[Bar            01]            Foo                 51/ 100 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   ")
        app.update_gui()
        member = app.tree.get_children()[0]

        healthTags = app.tree.item(member, 'tags')

        assert HealthTagger.HealthLevels.HEALTHY.value in healthTags

    def test_HealGroupIcon_DisplaysWhenAnyGroupMemberZeroed(self):
        receiver = InputReceiver()
        session = GameSession(receiver)
        app = WingmanApp(session)
        receiver.receive("""Foo's group:
[Bar            01]            Foo                 51/ 100 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   
[Baz            01]            Fuzz                 1/ 50  (  0%)       50/  50 (100%)     50/ 50  (100%)
[Duck           01]            Head               500/ 500 (  0%)      500/ 500 (100%)     50/ 50  (100%)""")
        
        patchMember = WingmanApp.displayHealGroupImage.__name__
        with patch.object(WingmanApp, patchMember) as mockedMethod:
            app.update_gui()
        
        
        assert app._healGroupLabel.winfo_viewable() == 0  # display updates aren't performed (unreliable state) until `mainloop` is able to run freely
        mockedMethod.assert_called_once_with()

    def test_HealGroupIcon_WhileInitiallyDisplayed_RemovedAfterHealthUpdateShowsNonZeroed(self):
        receiver = InputReceiver()
        session = GameSession(receiver)
        app = WingmanApp(session)
        receiver.receive('[Baz            01]            Fuzz                 1/ 50  (  0%)       50/  50 (100%)     50/ 50  (100%)')
        app.update_gui()
        receiver.receive("""Fuzz's group:
[Baz            01]            Fuzz                 2/ 50  (  0%)       50/  50 (100%)     50/ 50  (100%)""")

        patchPath = f'{__name__}.{WingmanApp.__name__}.{WingmanApp.hideHealGroupImage.__name__}'
        with patch(patchPath, Mock()) as mockedMethod:
            app.update_gui()


        assert mockedMethod.assert_called_once_with()

if __name__ == "__main__":
    TestApp().test_HealGroupIcon_WhileInitiallyDisplayed_RemovedAfterHealthUpdateShowsNonZeroed()