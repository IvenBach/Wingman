from enum import StrEnum
import unittest.mock
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import configparser
import tkinter.messagebox

from Wingman.core.group import Group

if __name__ == "__main__":
    srcDirectory = Path(__file__).parent.parent.parent.resolve()
    sys.path.append(str(srcDirectory))

from Wingman.core.character import Character
from Wingman.core.controller import Controller
from Wingman.core.parsing.parser import Parser
from Wingman.core.health_Tagger import HealthTagger
from Wingman.core.inventory import Equipment, Inventory
from Wingman.core.item import Item
from Wingman.core.mobs_chasing_you import MobsChasingYou
from Wingman.core.afk_status import AfkStatus

@pytest.fixture(scope="function")
def testController():
    c = Controller.ForTesting()
    yield c

    c.view.root.destroy()

@pytest.fixture(scope="session", autouse=True)
def load_base_item_names():
    srcDirectory = Path(__file__).parent.parent.resolve()
    base_item_names_path = str(Path(srcDirectory).joinpath('data/baseItemNames.txt'))
    Item.load_base_item_names_from_file(base_item_names_path)

class TestProcessQueue:
    def test_process_queue_calculates_xp(self, testController: Controller):
        c = testController
        inputs = ["You gain 1000 experience points.", "Garbage line."]
        for x in inputs:
            c.receiver.receive(x)

        logs = c.process_queue()

        assert c.gameSession.total_xp == 1000
        assert len(logs) == 1

    class TestMobRoomMovement:
        def test_EntersEmptyRoom_DisplayUpdatesAndMobsInRoomMatchesExpected(self, testController: Controller):
            c = testController
            c.model.currentMobsInRoom = []
            v = c.view

            c.receiver.receive("A windfang hatchling enters the room.")
            c.process_queue()

            with patch.object(v, v.updateMobCountDisplay.__name__) as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_called_once_with()
            assert c.model.currentMobsInRoom == ['a windfang hatchling']

        def test_MobArrivesFrom_WithInitially2Mobs_MobCountDisplayUpdateInvoked(self, testController: Controller):
            c = testController
            c.model.currentMobsInRoom = ['a foo bar', 'a bar foo']
            v = c.view

            c.receiver.receive("A windfang hatchling arrives from the east.")
            c.process_queue()

            with patch.object(v, v.updateMobCountDisplay.__name__) as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_called_once_with()

        def test_MobArrivesFrom_WithInitially2Mobs_MobsInRoomMatchesExpected(self, testController: Controller):
            c = testController
            c.model.currentMobsInRoom = ['a foo bar', 'a bar foo']
            v = c.view

            c.receiver.receive("A windfang hatchling arrives from the east.")

            v.update_gui()

            assert c.model.currentMobsInRoom == ['a foo bar', 'a bar foo', 'a windfang hatchling']

        def test_MobChasesAnotherPlayerIn_MobCountDisplayUpdateInvoked(self, testController: Controller):
            c = testController
            c.model.currentMobsInRoom = ['a foo bar']
            v = c.view

            c.receiver.receive("A windfang hatchling chases Foo into the room.")
            c.process_queue()

            with patch.object(v, v.updateMobCountDisplay.__name__) as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_called_once_with()

        def test_MobChasesAnotherPlayerIn_MobsInRoomMatchesExpected(self, testController: Controller):
            c = testController
            c.model.currentMobsInRoom = ['a foo bar']
            v = c.view

            c.receiver.receive("A windfang hatchling chases Foo into the room.")

            v.update_gui()

            assert c.model.currentMobsInRoom == ['a foo bar', 'a windfang hatchling']

        def test_ChasesOut_AsOnlyMobInTheRoom_MobCountDisplayUpdateInvoked(self, testController: Controller):
            c = testController
            c.model.currentMobsInRoom = ['a windfang hatchling']
            v = c.view

            c.receiver.receive("A windfang hatchling chases Foo out of the room.")
            c.process_queue()

            with patch.object(v, v.updateMobCountDisplay.__name__) as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_called_once_with()

        def test_ChasesOut_AsOnlyMobInTheRoom_MobsInRoomMatchesExpected(self, testController: Controller):
            c = testController
            c.model.currentMobsInRoom = ['a windfang hatchling']

            c.receiver.receive("A windfang hatchling chases Foo out of the room.")
            c.process_queue()

            assert c.model.currentMobsInRoom == []

        def test_Dies_With2MobsInRoom_MobCountDisplayUpdateInvoked(self, testController: Controller):
            c = testController
            c.model.currentMobsInRoom = ['a foo bar', 'a windfang hatchling']
            v = c.view

            c.receiver.receive("A windfang hatchling dies.")
            c.process_queue()

            with patch.object(v, v.updateMobCountDisplay.__name__) as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_called_once_with()
            assert c.model.currentMobsInRoom == ['a foo bar']

        def test_Dies_With2MobsInRoom_MobsInRoomMatchesExpected(self, testController: Controller):
            c = testController
            c.model.currentMobsInRoom = ['a foo bar', 'a windfang hatchling']
            v = c.view

            c.receiver.receive("A windfang hatchling dies.")

            v.update_gui()

            assert c.model.currentMobsInRoom == ['a foo bar']

        def test_Leaves_With5MobsInRoom_MobCountDisplayUpdateInvoked(self, testController: Controller):
            c = testController
            c.model.currentMobsInRoom = ['a foo bar', 'a bar foo', 'a dog', 'a cat', 'a windfang hatchling']
            v = c.view

            c.receiver.receive("A cat leaves North.")
            c.process_queue()

            with patch.object(v, v.updateMobCountDisplay.__name__) as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_called_once_with()

        def test_Leaves_With5MobsInRoom_MobsInRoomMatchesExpected(self, testController: Controller):
            c = testController
            c.model.currentMobsInRoom = ['a foo bar', 'a bar foo', 'a dog', 'a cat', 'a windfang hatchling']
            v = c.view

            c.receiver.receive("A cat leaves North.")

            v.update_gui()

            assert c.model.currentMobsInRoom == ['a foo bar', 'a bar foo', 'a dog', 'a windfang hatchling']

        def test_MobDies_ButWasNotListedAsInCurrentRoom_DoesNotRaiseError(self, testController: Controller):
            c = testController
            c.model.currentMobsInRoom = []

            c.receiver.receive("A bar foo dies.")

            try:
                c.process_queue()
            except ValueError:
                pytest.fail("Attempting to delete a non-existent mob from the current room failed.")


    class TestPlayerMovement:
        def test_ClearsMobsInRoomAndHidesMobCountInView(self, testController: Controller):
            c = testController

            c.receiver.receive("Obvious exits: east, northwest, and a small, smelly hut.")
            with patch.object(c, c.clearCountOfMobsInRoom.__name__) as mockedClear:
                with patch.object(c, c.updateMobCountDisplay.__name__) as mockedUpdate:
                    c.process_queue()

            mockedClear.assert_called_once_with()
            mockedUpdate.assert_called_once_with()

        def test_MobCountUpdated(self, testController: Controller):
            c = testController

            c.receiver.receive("Obvious exits: east, northwest, and a small, smelly hut.")
            with patch.object(c, c.updateMobCountDisplay.__name__) as mockedUpdate:
                c.process_queue()

            mockedUpdate.assert_called_once_with()

        def test_ClearsSoughtAfterItemsThatDropped(self, testController: Controller):
            c = testController
            c.model.SoughtAfterItems_ThatDropped = ['A foo bar']

            c.receiver.receive("Obvious exits: east, northwest, and a small, smelly hut.")
            with patch.object(c, c.clearSoughtAfterItemsThatDropped.__name__) as mockedClear:
                c.process_queue()

            mockedClear.assert_called_once_with()

    class TestModelUpdates:
        def test_InventoryCommand__THEN__EquipmentCommand_EquippedGearCorrectlyOverwritesAssumedInventoryPositions(self, testController: Controller):
            expectedEG = Equipment(head=Item("A WISPWEAVE spellbinder's crown"),
                                        jewel1=Item("A mark of vigilance"),
                                        jewel2=Item("A twisted gold torc"),
                                        cloak=Item("A GLOWING worldwalker's cloak"),
                                        body=None,
                                        hands=Item("A GOSSAMER noble's gleaming gloves of intelligence"),
                                        legs=Item("A GLOWING GOSSAMER hierophant's legwraps"),
                                        feet=Item("A GLOWING WISPWEAVE dragon-wing boots"),
                                        held_right=Item("A bright jeweled greatsword of the phoenix"),
                                        held_left=Item("A bright jeweled greatsword of the phoenix"))
            expectedBackpack = [Item("Glowing Ahrimal's shielding scale"),
                        Item("A GLOWING rod of endless repentance"),
                        Item("A goblet of zombie blood", quantity=4),
                        Item("A darkspawned blackened fish fillet", quantity=9),
                        Item("A bunch of restorative roots", quantity=10),
                        Item("A Lucifer's Pride ticket"),
                        Item("A ticket to Arnak's Plague", quantity=2),
                        Item("A scroll of minor resurrection", quantity=6),
                        Item("A scroll of lesser resurrection", quantity=2)]
            expectedInv = Inventory(expectedEG, expectedBackpack)

            c = testController
            inventoryText = """Inventory:
  (w) A WISPWEAVE spellbinder's crown
  (w) A mark of vigilance
  (w) A twisted gold torc
  (w) A GLOWING worldwalker's cloak
  (w) A GOSSAMER noble's gleaming gloves of intelligence
  (w) A GLOWING GOSSAMER hierophant's legwraps
  (w) A GLOWING WISPWEAVE dragon-wing boots
  (h) A bright jeweled greatsword of the phoenix
      Glowing Ahrimal's shielding scale
      A GLOWING rod of endless repentance
 ( 4) A goblet of zombie blood
 ( 9) A darkspawned blackened fish fillet
 (10) A bunch of restorative roots
      A Lucifer's Pride ticket
 ( 2) A ticket to Arnak's Plague
 ( 6) A scroll of minor resurrection
 ( 2) A scroll of lesser resurrection"""
            parsedInv = Parser().parseInventory(inventoryText)
            equipmentText = """Items in use:
     On Head:  a WISPWEAVE spellbinder's crown
    On Jewel:  a mark of vigilance
    On Jewel:  a twisted gold torc
    On Cloak:  a GLOWING worldwalker's cloak
     On Body:  nothing
    On Hands:  a GOSSAMER noble's gleaming gloves of intelligence
     On Legs:  a GLOWING GOSSAMER hierophant's legwraps
     On Feet:  a GLOWING WISPWEAVE dragon-wing boots
  Held Right:  a bright jeweled greatsword of the phoenix
   Held Left:  a bright jeweled greatsword of the phoenix"""
            parsedEG = Parser().parseEquippedGear(equipmentText)
            c.receiver.receive(parsedInv)
            c.receiver.receive(parsedEG)

            c.process_queue()

            assert c.model.inventory == expectedInv

    class TestAffectLabelDisplay:
        def test_AffectsWithoutDuration_NoDisplayedAffectSpellDropLabel(self, testController: Controller):
            c = testController
            v = c.view

            text = """You are affected by: 
Bless.II                                                  """
            _, affects, _ = Parser.ParseAffect().parseAffects(text)
            c.receiver.receive(affects)
            c.process_queue()

            with patch.object(c, c.displayAffectSpellDropWarningLabel.__name__) as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_not_called()

        def test_AffectsWithDuration_DisplayAffectSpellDropLabel(self, testController: Controller):
            c = testController
            v = c.view

            text = """You are affected by: 
Bless.II                                             
Shield.V                       4m 20s                
Blur.V                         4m 5s                """
            _, affects, _ = Parser.ParseAffect().parseAffects(text)
            c.receiver.receive(affects)
            c.process_queue()

            with patch.object(v, v.displayAffectSpellDropWarningLabel.__name__) as mockedDisplay:
                v.update_gui()

            argument = mockedDisplay.mock_calls[0].args[0]
            assert 'Shield.V' in argument
            assert 'Blur.V' in argument

    class TestAlertingItemDrops:
        def test_ItemNameDropsThatIsSoughtAfter_DisplaysDropAlertLabel(self, testController: Controller):
            c = testController
            c.model.SoughtAfterItems_Names, c.model.SoughtAfterItems_BaseItemNames = c.SoughtAfterItems_SemicolonDelimitedTextToTwoSets('a fire root')
            text = "A simple mob drops a fire root."

            c.receiver.receive(text)
            c.process_queue()

            with patch.object(c, c.displayDropAlertLabel.__name__) as mockedDisplay:
                c.view.update_gui()

            assert mockedDisplay.call_args[0][0] == "a fire root"

        def test_BaseItemNameDropsThatIsSoughtAfter_DisplaysDropAlertLabel(self, testController: Controller):
            c = testController
            c.model.SoughtAfterItems_Names, c.model.SoughtAfterItems_BaseItemNames = c.SoughtAfterItems_SemicolonDelimitedTextToTwoSets('dragon-wing boots')
            text = "A simple mob drops a glowing dragon-wing boots."

            c.receiver.receive(text)
            c.process_queue()

            with patch.object(c, c.displayDropAlertLabel.__name__) as mockedDisplay:
                c.view.update_gui()

            assert mockedDisplay.call_args[0][0] == "a glowing dragon-wing boots"

    class TestPausingDoesNotAffect:
        def test_DisbandingGroup_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.gameSession.group.AddMembers([Character("Bar"), Character("Foo")])
            c.view.isPaused = True

            countBeforeDisbanding = c.gameSession.group.Count

            c.receiver.receive("You disband from Quackin's group.")
            c.process_queue()

            assert countBeforeDisbanding == 2
            assert c.gameSession.group.Count == 0

        def test_AddingGroupMember_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.view.isPaused = True
            c.receiver.receive("FooBar follows you")
            c.process_queue()

            assert c.gameSession.group.Count == 1

        def test_GroupMemberLeaving_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.gameSession.group.AddMembers([Character("Bar"), Character("FooBar")])
            c.view.isPaused = True

            c.process_queue()
            countBeforeLeaving = c.gameSession.group.Count

            c.receiver.receive("FooBar disbands from the group.")
            c.process_queue()

            assert countBeforeLeaving == 2
            assert c.gameSession.group.Count == 1

        def test_MobDroppingItemThatIsSoughtAfter_DisplayOfLabel_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.model.SoughtAfterItems_Names, c.model.SoughtAfterItems_BaseItemNames = c.SoughtAfterItems_SemicolonDelimitedTextToTwoSets('a fire root')
            c.view.isPaused = True
            text = "A simple mob drops a fire root."

            c.receiver.receive(text)
            c.process_queue()

            with patch.object(c.view, c.view.displayDropAlertLabel.__name__) as mockedDisplay:
                c.view.update_gui()

            mockedDisplay.assert_called()

        def test_GoingAfk_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.model.isAfk = False
            c.view.isPaused = True

            c.receiver.receive(AfkStatus.BeginAfk.value)
            c.process_queue()

            with patch.object(c.view, c.view.displayAfkLabel.__name__) as mockedDisplay:
                c.view.update_gui()

            mockedDisplay.assert_called_once_with()
            assert c.model.isAfk

        def test_ReturningFromAfk_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.model.isAfk = True
            c.view.isPaused = True

            c.receiver.receive(AfkStatus.EndAfk.value)
            c.process_queue()

            with patch.object(c.view, c.view.hideAfkLabel.__name__) as mockedHide:
                c.view.update_gui()

            mockedHide.assert_called_once_with()
            assert not c.model.isAfk

        def test_MeditationStarting_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.model.isMeditating = False
            c.view.isPaused = True

            c.receiver.receive(Parser.MeditationState.Begin.value)
            c.process_queue()

            with patch.object(c.view, c.view.displayMeditationLabel.__name__) as mockedDisplay:
                c.view.update_gui()

            mockedDisplay.assert_called_once_with()
            assert c.model.isMeditating

        def test_MeditationEnding_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.model.isMeditating = True
            c.view.isPaused = True

            c.receiver.receive(Parser.MeditationState.Termination_ByStanding.value)
            c.process_queue()

            with patch.object(c.view, c.view.hideMeditationLabel.__name__) as mockedHide:
                c.view.update_gui()

            mockedHide.assert_called_once_with()
            assert not c.model.isMeditating

        def test_HidingStarts_DisplayOfLabel_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.model.isHiding = False
            c.view.isPaused = True

            c.receiver.receive(Parser.HideStatus.Begin.value)
            c.process_queue()

            with patch.object(c.view, c.view.displayHidingLabel.__name__) as mockedDisplay:
                c.view.update_gui()

            mockedDisplay.assert_called_once_with()
            assert c.model.isHiding

        def test_HidingEnds_DisplayOfLabel_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.model.isHiding = True
            c.view.isPaused = True

            c.receiver.receive(Parser.HideStatus.EndHiding.value)
            c.process_queue()

            with patch.object(c.view, c.view.hideHidingLabel.__name__) as mockedHide:
                c.view.update_gui()

            mockedHide.assert_called_once_with()
            assert not c.model.isHiding

        def test_PlayerMovement_ClearCountOfMobsInRoomInvoked_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.view.isPaused = True

            c.receiver.receive("Obvious exits: east, northwest, and a small, smelly hut.")
            with patch.object(c, c.clearCountOfMobsInRoom.__name__) as mockedClear:
                c.process_queue()

            mockedClear.assert_called_once_with()

        def test_PlayerMovement_UpdateMobCountDisplayInvoked_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.view.isPaused = True

            c.receiver.receive("Obvious exits: east, northwest, and a small, smelly hut.")
            with patch.object(c, c.updateMobCountDisplay.__name__) as mockedUpdate:
                c.process_queue()

            mockedUpdate.assert_called_once_with()

        def test_PlayerMovement_ClearSoughtAfterItemsThatDroppedInvoked_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.view.isPaused = True

            c.receiver.receive("Obvious exits: east, northwest, and a small, smelly hut.")
            with patch.object(c, c.clearSoughtAfterItemsThatDropped.__name__) as mockedClear:
                c.process_queue()

            mockedClear.assert_called_once_with()

        def test_MobMovement_Enters_UpdateMobCountDisplayInvoked_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.view.isPaused = True

            c.receiver.receive('A cat enters the room.')
            with patch.object(c, c.updateMobCountDisplay.__name__) as mockedUpdate:
                c.process_queue()

            mockedUpdate.assert_called_once_with()

        def test_MobMovement_Leaves_UpdateMobCountDisplayInvoked_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.view.isPaused = True
            c.model.currentMobsInRoom = ['a cat']

            c.receiver.receive('A cat leaves the North.')
            with patch.object(c, c.updateMobCountDisplay.__name__) as mockedUpdate:
                c.process_queue()

            mockedUpdate.assert_called_once_with()

        def test_SpellWithTimeDurationEnds_NotAffectedWhilePaused(self, testController: Controller):
            c = testController
            c.view.isPaused = True
            c.model.BuffOrShieldEnding = None
            c.receiver.receive(Parser.ParseBuffOrShieldText.Blur_Ended.value)

            c.process_queue()

            assert c.model.BuffOrShieldEnding == Parser.ParseBuffOrShieldText.Blur_Ended

        @pytest.mark.parametrize("expectedMitigation",
                                 [Parser.ConstitutionResisted.ConstitutionResistedDisease,
                                  Parser.SpellMitigationAffect.BleedDotResist],
                                ids=['ConstitutionResistedDisease', 'BleedDotResist'])
        def test_AffectMitigation_DisplayMitigatedAffectLabel_NotAffectedWhilePaused(self, testController: Controller, expectedMitigation: StrEnum):
            c = testController
            v = c.view
            c.view.isPaused = True

            c.receiver.receive(expectedMitigation.value)

            with patch.object(v, v.displayMitigatedAffectLabel.__name__) as mockedDisplay:
                c.process_queue()

            mockedDisplay.assert_called_once_with(expectedMitigation)

    class TestPausingDoesAffect:
        def test_GainingExperience_DoesNotUpdateWhilePaused(self, testController: Controller):
            c = testController
            c.view.isPaused = True

            c.receiver.receive("You gain 1000 experience points.")
            c.process_queue()

            assert c.gameSession.total_xp == 0

class TestGrouping:
    def test_GainNewFollower_NewFollowerAddedToGroupForDisplay(self, testController: Controller):
        c = testController
        c.receiver.receive("""Beautiful's group:

[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Sin            69]           Beautiful            500/ 500 (100%)    497/ 500 ( 99%)    592/ 707 ( 83%)   
[Skelton        50]           Skeletor             396/ 396 (100%)    396/ 396 (100%)    554/ 554 (100%) """)
        c.view.update_gui()
        groupCountBeforeNewFollower = len(c.view.groupTreeview.get_children())

        c.receiver.receive("FooBar follows you")
        c.view.update_gui()
        groupCountAfterNewFollower = len(c.view.groupTreeview.get_children())
        assert groupCountBeforeNewFollower == 2
        assert groupCountAfterNewFollower == 3

    def test_LoseFollower_FollowerRemovedFromGroupForDisplay(self, testController: Controller):
        c = testController
        c.receiver.receive("""Beautiful's group:

[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Sin            69]           Beautiful            500/ 500 (100%)    497/ 500 ( 99%)    592/ 707 ( 83%)   
[Apple           1]           Foo                  100/ 200 (100%)    150/ 300 ( 50%)    250/ 500 ( 50%)   
[Skelton        50]           Skeletor             396/ 396 (100%)    396/ 396 (100%)    554/ 554 (100%) """)
        c.view.update_gui()
        groupCountBeforeLosingFollower = len(c.view.groupTreeview.get_children())

        c.receiver.receive("Foo disbands from the group.")
        c.view.update_gui()
        groupCountAfterLosingFollower = len(c.view.groupTreeview.get_children())

        assert groupCountBeforeLosingFollower == 3
        assert groupCountAfterLosingFollower == 2

    def test_GainNewFollowerAndLoseFollower_WithoutInvokingGroupCommand_CountsCorrectlyForAdditionAndRemoval(self, testController: Controller):
        c = testController
        c.receiver.receive("""Beautiful's group:

[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Sin            69]           Beautiful            500/ 500 (100%)    497/ 500 ( 99%)    592/ 707 ( 83%)   
[Skelton        50]           Skeletor             396/ 396 (100%)    396/ 396 (100%)    554/ 554 (100%) """)
        c.view.update_gui()
        groupCountInitial = len(c.view.groupTreeview.get_children())

        c.receiver.receive("NewFollower follows you")
        c.view.update_gui()
        groupCountAfterNewFollower = len(c.view.groupTreeview.get_children())

        c.receiver.receive("NewFollower disbands from the group.")
        c.view.update_gui()
        groupCountAfterLosingFollower = len(c.view.groupTreeview.get_children())

        assert groupCountInitial == 2
        assert groupCountAfterNewFollower == 3
        assert groupCountAfterLosingFollower == 2

    def test_FollowedByTwoIdenticallyDisguisedCharacters_BothAddedToGroupForDisplay(self, testController: Controller):
        c = testController
        c.receiver.receive("""Beautiful's group:

[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Sin            69]           Beautiful            500/ 500 (100%)    497/ 500 ( 99%)    592/ 707 ( 83%)   """)
        c.view.update_gui()
        unfollowedGroupCount = len(c.view.groupTreeview.get_children())

        c.receiver.receive("A primeval eldritch voidwolf follows you")
        c.view.update_gui()
        groupCountAfterFirstFollower = len(c.view.groupTreeview.get_children())

        c.receiver.receive("A primeval eldritch voidwolf follows you")
        c.view.update_gui()
        groupCountAfterSecondFollower = len(c.view.groupTreeview.get_children())

        assert unfollowedGroupCount == 1
        assert groupCountAfterFirstFollower == 2
        assert groupCountAfterSecondFollower == 3    

    def test_GroupMemberZeroed_DisplaysZeroedFormatting(self, testController: Controller):
        c = testController
        c.receiver.receive("""Foo's group:
[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Bar            01]            Foo                 1/ 500 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   """)
        
        c.view.update_gui()
        member = c.view.groupTreeview.get_children()[0]
        healthTags = c.view.groupTreeview.item(member, 'tags')

        assert HealthTagger.HealthLevels.ZEROED.value in healthTags

    def test_GroupMemberInRedHealth_DisplaysRedHealthFormatting(self, testController: Controller):
        c = testController
        c.receiver.receive("[Bar            01]            Foo                 25/ 100 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   """)
        c.view.update_gui()
        member = c.view.groupTreeview.get_children()[0]

        healthTags = c.view.groupTreeview.item(member, 'tags')

        assert HealthTagger.HealthLevels.AT_OR_BELOW_25.value in healthTags

    def test_GroupMemberInYellowHealth_DisplaysYellowHealthFormatting(self, testController: Controller):
        c = testController
        c.receiver.receive("[Bar            01]            Foo                 50/ 100 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   ")
        c.view.update_gui()
        member = c.view.groupTreeview.get_children()[0]

        healthTags = c.view.groupTreeview.item(member, 'tags')

        assert HealthTagger.HealthLevels.AT_OR_BELOW_50.value in healthTags

    def test_GroupMemberInGoodHealth_DisplaysNoHealthFormatting(self, testController: Controller):
        c = testController
        c.receiver.receive("[Bar            01]            Foo                 51/ 100 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   ")
        c.view.update_gui()
        member = c.view.groupTreeview.get_children()[0]

        healthTags = c.view.groupTreeview.item(member, 'tags')

        assert HealthTagger.HealthLevels.HEALTHY.value in healthTags

    def test_UngroupedCharacterGainsNewFollower_NewFollowerAddedToLatestGroupData(self, testController: Controller):
        c = testController

        c.receiver.receive("FooBar follows you")
        c.process_queue()

        assert c.gameSession.group.Count == 1

    def test_LeaderGainsNewFollower_NewFollowerAddedToLatestGroupData(self, testController: Controller):
        c = testController
        groupCommandText = """Beautiful's group:

[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Sin            69]           Beautiful            500/ 500 (100%)    497/ 500 ( 99%)    592/ 707 ( 83%)   
[Skelton        50]           Skeletor             396/ 396 (100%)    396/ 396 (100%)    554/ 554 (100%) """

        c.receiver.receive(groupCommandText)
        c.process_queue()
        groupCountBeforeNewFollower = c.gameSession.group.Count

        c.receiver.receive("FooBar follows you")
        c.process_queue()

        assert groupCountBeforeNewFollower == 2
        assert c.gameSession.group.Count == 3

    def test_LeavingGroup_ClearsLatestGroupData(self, testController: Controller):
        c = testController
        
        groupCommandText = """Foo's group:

    [ Class      Lv] Status   Name              Hits            Fat             Power         
    [Necromance   9]         Foo              100/100 (100%)  100/100 (100%)  119/119 (100%)  

    [Sin         74]         Beautiful        500/500 (100%)  383/500 ( 76%)  503/731 ( 68%)  """

        c.receiver.receive(groupCommandText)
        c.process_queue()

        groupCountWhileMemberOfGroup = c.gameSession.group.Count

        c.receiver.receive("You disband from Foo's group.")
        c.process_queue()

        assert groupCountWhileMemberOfGroup == 2
        assert c.gameSession.group.Count == 0

    def test_nonGroupLeaderLeavesGroup_IsRemovedFromLatestGroupData(self, testController: Controller):
        c = testController

        groupText = """Foo's group:

    [ Class      Lv] Status   Name              Hits            Fat             Power         
    [Necromance   9]         Foo              100/100 (100%)  100/100 (100%)  119/119 (100%)  

    [Sin         74]         Bar              500/500 (100%)  383/500 ( 76%)  503/731 ( 68%)  

    [Hydro       60]         Baz              100/200 (100%)  200/400 ( 50%)  300/600 ( 50%)  """
        c.receiver.receive(groupText)
        c.process_queue()
        initialGroupSize = c.gameSession.group.Count

        c.receiver.receive("Baz disbands from the group.")
        c.process_queue()

        assert initialGroupSize == 3
        assert c.gameSession.group.Count == 2

    def test_IncludeMobsInGroup_MobsDisplayInGroupDisplay(self, testController: Controller):
        c = testController
        c.model.includePetsInGroup = True
        text = """Beautiful's group:

[ Class      Lv] Status   Name              Hits            Fat             Power         
[Sin         74]         Beautiful        500/500 (100%)  500/500 (100%)  687/731 ( 93%)  
[mob         72]         angel of death   417/417 (100%)  417/417 (100%)  618/618 (100%)  """

        c.receiver.receive(text)

        c.process_queue()

        assert c.gameSession.group.Count == 2

    class TestDisbanding:
        def test_ClearsGameSessionGroup(self, testController: Controller):
            c = testController
            c.gameSession.group.AddMembers([Character("Foo"), Character("Bar")])

            initialGroupCount = c.gameSession.group.Count

            c.disbandGroup()

            assert initialGroupCount == 2
            assert c.gameSession.group.Count == 0

        def test_ClearsCachedGroupOnView(self, testController: Controller):
            c = testController
            v = c.view
            v._cachedGroup = Group([Character("Foo"), Character("Bar")])

            initialCachedGroupCount = v._cachedGroup.Count

            c.disbandGroup()

            assert initialCachedGroupCount == 2
            assert v._cachedGroup.Count == 0

class TestDisplayingCentralColumnLabelInView:
    def test_DisplayAfkLabel(self, testController: Controller):
        c = testController
        v = c.view
        c.receiver.receive(AfkStatus.BeginAfk.value)
        c.process_queue()

        with patch.object(v, v.displayAfkLabel.__name__) as mockedMethod:
            v.update_gui()

        mockedMethod.assert_called_once_with()
    
    def test_HideAfkLabel(self, testController: Controller):
        c = testController
        v = c.view
        c.receiver.receive(AfkStatus.EndAfk.value)
        c.process_queue()

        with patch.object(v, v.hideAfkLabel.__name__) as mockedMethod:
            v.update_gui()

        mockedMethod.assert_called_once_with()

    def test_BeginMeditating_MeditationLabelDisplayedInView(self, testController: Controller):
        c = testController
        v = c.view
        c.receiver.receive(Parser.MeditationState.Begin.value)
        c.process_queue()

        with patch.object(v, v.displayMeditationLabel.__name__) as mockedMethod:
            v.update_gui()

        mockedMethod.assert_called_once_with()

    @pytest.mark.parametrize("input_line", [Parser.MeditationState.Termination_ByStanding.value, Parser.MeditationState.Termination_ByInterruption.value],
                                        ids=['VoluntaryTermination', 'NonVoluntaryTermination'])
    def test_StopMeditating_MeditationLabelHiddenInView(self, input_line, testController):
        c = testController
        v = c.view
        c.receiver.receive(input_line)
        c.process_queue()

        with patch.object(v, v.hideMeditationLabel.__name__) as mockedMethod:
            v.update_gui()

        mockedMethod.assert_called_once_with()

    def test_MeditationNotAffectedByNonMeditationInput_NeitherDisplayNorHideInvoked(self, testController: Controller):
        c = testController
        v = c.view
        c.receiver.receive("Any text not relating to meditation.")

        c.process_queue()

        with patch.object(v, v.displayMeditationLabel.__name__) as mockedDisplay:
            with patch.object(v, v.hideMeditationLabel.__name__) as mockedHide:
                v.update_gui()
        
        mockedDisplay.assert_not_called()
        mockedHide.assert_not_called()

    def test_MeditationRegenValueChanges_ObserverNotified(self, testController: Controller):
        c = testController
        c.receiver.receive(Parser.MeditationState.Begin.value)
        c.process_queue()
        md = c.model.meditationDisplay
        with patch.object(md, md.meditationDurationInSeconds.__name__) as mockedDuration:
            mockedDuration.return_value = 40

    def test_ChaseTextNotSentInChaseDataStructure_NoInvocationOfChaseDisplayLabel(self, testController: Controller):
        c = testController
        c.receiver.receive("A ravenous, jeweled scarab chases you into the room.")

        with patch.object(c, c.displayMobIsChasingYouLabel.__name__) as mockedMethod:
            c.process_queue()

        mockedMethod.assert_not_called()

    def test_SingleMobIsChasingYou(self, testController: Controller):
        c = testController
        c.receiver.receive(MobsChasingYou(["a ravenous, jeweled scarab"]))

        with patch.object(c, c.displayMobIsChasingYouLabel.__name__) as mockedMethod:
            c.process_queue()

        assert mockedMethod.call_args[0][0] == 'a ravenous, jeweled scarab'

    def test_TwoMobsAreChasingYou_SingleDisplayLabelInvokedWithNewlineSeparatingMobNames(self, testController: Controller):
        mob1 = "a brilliant bronze-scaled dragon"
        mob2 = "a diabolic infernal nomad"
        c = testController
        c.receiver.receive(MobsChasingYou([mob1, mob2]))

        with patch.object(c, c.displayMobIsChasingYouLabel.__name__) as mockedMethod:
            c.process_queue()

        argument = mockedMethod.mock_calls[0].args[0]
        assert mob1 in argument
        assert mob2 in argument
        assert '\n' in argument

    def test_MobChasingAnotherPlayerIntoRoom_DisplayLabelNotInvoked(self, testController: Controller):
        c = testController
        c.receiver.receive("A ravenous, jeweled scarab chases FooBar into the room.")

        with patch.object(c, c.displayMobIsChasingYouLabel.__name__) as mockedMethod:
            c.process_queue()

        mockedMethod.assert_not_called()

    def test_BeginHiding_HideLabelDisplayedInView(self, testController: Controller):
        c = testController
        v = c.view
        c.receiver.receive(Parser.HideStatus.Begin.value)
        c.process_queue()

        with patch.object(v, v.displayHidingLabel.__name__) as mockedMethod:
            v.update_gui()

        mockedMethod.assert_called_once_with()

    def test_StopHiding_HideLabelHiddenInView(self, testController: Controller):
        c = testController
        v = c.view
        c.receiver.receive(Parser.HideStatus.EndHiding.value)
        c.process_queue()

        with patch.object(v, v.hideHidingLabel.__name__) as mockedMethod:
            v.update_gui()

        mockedMethod.assert_called_once_with()

    def test_HidingNotAffectedByNonHidingInput_NeitherDisplayNorHideInvoked(self, testController: Controller):
        c = testController
        v = c.view
        c.receiver.receive("Any text not relating to hiding.")
        c.process_queue()

        with patch.object(v, v.displayHidingLabel.__name__) as mockedDisplay:
            with patch.object(v, v.hideHidingLabel.__name__) as mockedHide:
                v.update_gui()

        mockedDisplay.assert_not_called()
        mockedHide.assert_not_called()

class TestIgnoredMobsInRoom:
    def test_UpdatingIgnoredMobsPets_WithCsvIncludingWhitespace_WhitespaceTrimmedAndNotIncludedInModel(self, testController: Controller):
        c = testController
        c.updateIgnoredMobsPets(' foo; bar ;baz ')

        assert c.model.ignoreTheseMobsInCurrentRoom == ['foo', 'bar', 'baz']

    def test_UpdatingIgnoredMobsPets_WithEmptyInput_ClearsIgnoredMobs(self, testController: Controller):
        c = testController
        c.updateIgnoredMobsPets('foo;bar;baz')

        c.updateIgnoredMobsPets('')

        assert c.model.ignoreTheseMobsInCurrentRoom == []

    def test_UpdatingIgnoredMobsPets_WhenDifferentCsvMobsEntered_ClearsOldValuesLeavingOnlyNew(self, testController: Controller):
        c = testController
        c.updateIgnoredMobsPets('foo;bar;baz')

        c.updateIgnoredMobsPets('a; b; c; d')

        assert c.model.ignoreTheseMobsInCurrentRoom == ['a', 'b', 'c', 'd']

    def test_InvokingUpdateMobsInRoom_WhenCurrentRoomHasMobListedInIgnoredMobs__RemovesMobFromCurrentRoomMobsOnModel(self, testController: Controller):
        c = testController
        c.model.currentMobsInRoom = ['a foo', 'a bar', 'a baz']
        c.updateIgnoredMobsPets('a foo')

        c.removedIgnoredMobsFromCurrentRoom()

        assert c.model.currentMobsInRoom == ['a bar', 'a baz']

    def test_ClearingCountOfMobsInRoom_ReflectedInModel(self, testController: Controller):
        c = testController
        c.model.currentMobsInRoom = ['a foo', 'a bar', 'a baz']

        c.clearCountOfMobsInRoom()

        assert c.model.currentMobsInRoom == []

class TestSettings:
    def test_ApplySettings_WhenSettingsFileIsMissingAKey_FallbackValueIsUsed_OpenNotInvokedToWriteFile(self, testController: Controller):
        c = testController

        with patch('builtins.open', new_callable=unittest.mock.mock_open()) as mockedOpen:
            c.applySettings(configParser=configparser.ConfigParser())

        mockedOpen.assert_not_called()

    def test_SaveSettings_OpenInvoked(self, testController: Controller):
        c = testController

        with patch('builtins.open', new_callable=unittest.mock.mock_open()) as mockedOpen:
            c.saveSettings()
        
        mockedOpen.assert_called_once_with(unittest.mock.ANY, 'w')

    def test_LoadSettings_AppliesMobPetIgnore(self, testController: Controller):
        c = testController
        cp = configparser.ConfigParser()
        cp.add_section(c._VIEW_SETTINGS)
        cp.add_section(c._APP_SETTINGS)
        cp[c._VIEW_SETTINGS][c._IGNORED_MOB_PETS_SEMICOLON_DELIMITED__OPTION] = 'foo, bar, baz'

        with patch.object(c, c.updateIgnoredMobsPets.__name__) as mockedUpdateIgnoredMobsPets:
            with patch('builtins.open', new_callable=unittest.mock.mock_open()) as mockedOpen:
                c.applySettings(cp)

        mockedOpen.assert_not_called()
        mockedUpdateIgnoredMobsPets.assert_called_once_with('foo, bar, baz')

class TestCheckInvasionSupplies:
    def test_HavingEqualItemInSupplyList_NoEntries(self, testController: Controller):
        c = testController
        inventory = Inventory(Equipment(),
                      [Item("A darkspawned black fish fillet", quantity=2)])
        supplyText = "( 2) A darkspawned black fish fillet"


        items = c.check_supplies(supplyText, inventory)

        assert len(items) == 0

    def test_HavingLessThanItemInSupplyList_ReturnsMissingQuantity(self, testController: Controller):
        c = testController
        inventory = Inventory(Equipment(),
                      [Item("A darkspawned black fish fillet", quantity=1)])
        supplyText = "( 2) A darkspawned black fish fillet"


        items = c.check_supplies(supplyText, inventory)

        assert len(items) == 1
        assert items[0].Name == "A darkspawned black fish fillet"
        assert items[0].Quantity == 1

    def test_HavingMoreThanItemInSupplyList_NoEntries(self, testController: Controller):
        c = testController
        inventory = Inventory(Equipment(),
                      [Item("A darkspawned black fish fillet", quantity=5)])
        supplyText = "( 2) A darkspawned black fish fillet"


        items = c.check_supplies(supplyText, inventory)

        assert len(items) == 0

    def test_NotHavingItemInSupplyList_ReturnsItemAndQuantityFromSupplyList(self, testController: Controller):
        c = testController
        inventory = Inventory(Equipment(),
                      [Item("A darkspawned black fish fillet", quantity=3)])
        supplyText = "( 2) A goblet of zombie blood"


        items = c.check_supplies(supplyText, inventory)

        assert len(items) == 1
        assert items[0].Name == "A goblet of zombie blood"
        assert items[0].Quantity == 2

    def test_AlreadyHaveSomeItems_LackingSomeOnSupplyList_ReturnsOnlyMissingItemsAndTheirQuantities(self, testController: Controller):
        c = testController
        backpack = [Item("A goblet of zombie blood", quantity=2),
                    Item("A darkspawned blackened fish fillet", quantity=4),
                    Item("A bunch of restorative roots", quantity=2),
                    Item("A ticket to Arnak's Plague", quantity=2),
                    Item("A scroll of minor resurrection", quantity=6)]
        inventory = Inventory(Equipment(), backpack)
        supplyText = """( 9) A goblet of zombie blood
( 3) A darkspawned blackened fish fillet
(15) A bunch of restorative roots
( 3) A ticket to Arnak's Plague
( 2) A scroll of minor resurrection"""

        items = c.check_supplies(supplyText, inventory)

        assert len(items) == 3
        assert items[0].Name == "A goblet of zombie blood"
        assert items[0].Quantity == 7
        assert items[1].Name == "A bunch of restorative roots"
        assert items[1].Quantity == 13
        assert items[2].Name == "A ticket to Arnak's Plague"
        assert items[2].Quantity == 1

class TestSuppliesList:
    def test_EmptySupplyList_AlertsViewOfEmptySupplyList(self, testController: Controller):
        c = testController
        v = c.view
        inv = Inventory(Equipment(), [])
        with patch.object(v, v.updateMissingSuppliesLabel.__name__) as mockedUpdateLabel:
            c.updateMissingSuppliesLabel("N/A", "", inv)

        userHelpfulText = mockedUpdateLabel.mock_calls[0].args[0]
        assert '***' in userHelpfulText
        assert type(userHelpfulText) == str

    def test_EmptyBackpack_AlertsViewThatBackpackIsEmpty(self, testController: Controller):
        c = testController
        v = c.view
        inv = Inventory(Equipment(), [])
        with patch.object(v, v.updateMissingSuppliesLabel.__name__) as mockedUpdateLabel:
            c.updateMissingSuppliesLabel("N/A", "( 2) A goblet of zombie blood", inv)

        userHelpfulText = mockedUpdateLabel.mock_calls[0].args[0]
        assert '***' in userHelpfulText
        assert type(userHelpfulText) == str

    @pytest.mark.parametrize("pvpText, pveText, activeTabIndex", [("( 2) A goblet of zombie blood", "", 0),
                                                            ("", "( 2) A goblet of zombie blood", 1)],
                                                        ids=['PvpSuppliesText', 'PvESuppliesText'])
    def test_CorrectSuppliesTextPulledFromSuppliesActiveTab(self, testController: Controller, pvpText: str, pveText: str, activeTabIndex: int):
        c = testController
        v = c.view
        c.model.inventory = Inventory(Equipment(),
                                        [Item("Any item to not have an empty backpack.")])

        v.pvpSuppliesText.insert('1.0', pvpText) #Index0
        v.pveSuppliesText.insert('1.0', pveText) #Index1

        v.suppliesNotebook.select(activeTabIndex)
        actualText =c.suppliesTextFromTab(c.activeTabTextInNotebook(v.suppliesNotebook))

        assert actualText == "( 2) A goblet of zombie blood\n"

    def test_TextSuppliesAccessFromUnexpectedTab_RaisesValueError(self, testController: Controller):
        c = testController
        v = c.view
        mockedTab = MagicMock()
        mockedTab.return_value = 'UnexpectedTab'
        v.suppliesNotebook.tab = mockedTab

        with pytest.raises(ValueError):
            c.suppliesTextFromTab(c.activeTabTextInNotebook(v.suppliesNotebook))

class TestApplySettings:
    def test_IgnoredMobsPetsCsv(self, testController: Controller):
        cp = configparser.ConfigParser()
        c = testController
        cp[c._VIEW_SETTINGS] = {
            c._IGNORED_MOB_PETS_SEMICOLON_DELIMITED__OPTION: "foo; bar; baz"
        }

        c.applySettings(cp)
        appliedText = c.view.var_ignoredMobPetsSemicolonDelimited.get()

        assert appliedText == "foo; bar; baz"
        assert c.model.ignoreTheseMobsInCurrentRoom == ['foo', 'bar', 'baz']

    def test_PvpSupplies(self, testController: Controller):
        cp = configparser.ConfigParser()
        c = testController
        cp[c._VIEW_SETTINGS] = {
            c._PVP_SUPPLIES_TEXT__OPTION: "A safety blanket"
        }

        c.applySettings(cp)
        appliedText = c.view.pvpSuppliesText.get('1.0', 'end')

        assert appliedText == "A safety blanket\n"

    def test_PveSupplies(self, testController: Controller):
        cp = configparser.ConfigParser()
        c = testController
        cp[c._VIEW_SETTINGS] = {
            c._PVE_SUPPLIES_TEXT__OPTION: "( 2) A goblet of zombie blood"
        }

        c.applySettings(cp)
        appliedText = c.view.pveSuppliesText.get('1.0', 'end')

        assert appliedText == "( 2) A goblet of zombie blood\n"

    def test_NotebookTabIdentifierNotFound_GracefullyContinuesUsingDefaultIndex_Zero(self, testController: Controller):
        cp = configparser.ConfigParser()
        c = testController
        cp[c._VIEW_SETTINGS] = {
            c._ACTIVE_SUPPLIES_TAB__OPTION: "`TclError` producing identifier"
        }

        c.applySettings(cp)
        #Gracefully applied settings

    def test_HideDisplayedLabelCallbackTimer(self, testController: Controller):
        cp = configparser.ConfigParser()
        c = testController
        cp[c._VIEW_SETTINGS] = {
            c._HIDE_DISPLAYED_LABEL_CALLBACK_TIMER_IN_MILLISECONDS__OPTION: str(5000)
        }

        c.applySettings(cp)

        assert c.view.var_hideDisplayedLabelCallbackTimerInMilliseconds.get() == 5000

    def test_AlertForSpellsDropping(self, testController: Controller):
        cp = configparser.ConfigParser()
        c = testController
        cp[c._VIEW_SETTINGS] = {
            c._ALERT_FOR_SPELL_DROPPING_DURATION_IN_MINUTES__OPTION: str(10)
        }

        c.applySettings(cp)

        assert c.view.var_timeInMinutesToWarnAboutSpellsDropping.get() == 10

    class TestWindowPosition:
        def test_RootPosition(self, testController: Controller):
            cp = configparser.ConfigParser()
            c = testController
            cp[c._APP_SETTINGS] = {
                c._ROOT_WINDOW_POSITION__OPTION: "+1108+856"
            }

            c.applySettings(cp)
            actual = c.view.root.geometry()

            assert "+1108+856" in actual

        def test_MiscellaneousSettingsPosition(self, testController: Controller):
            cp = configparser.ConfigParser()
            c = testController
            cp[c._APP_SETTINGS] = {
                c._MISCELLANEOUS_SETTINGS_WINDOW_POSITION__OPTION: "+1108+856"
            }

            c.applySettings(cp)
            actual = c.view._miscellaneousSettings.geometry()

            assert "+1108+856" in actual

        def test_SupplyCheckerPosition(self, testController: Controller):
            cp = configparser.ConfigParser()
            c = testController
            cp[c._APP_SETTINGS] = {
                c._SUPPLY_CHECKER_WINDOW_POSITION__OPTION: "+1108+856"
            }

            c.applySettings(cp)
            actual = c.view._supplyCheckerWindow.geometry()

            assert "+1108+856" in actual

        def test_GearSetPosition(self, testController: Controller):
            cp = configparser.ConfigParser()
            c = testController
            cp[c._APP_SETTINGS] = {
                c._GEAR_SETS_WINDOW_POSITION__OPTION: "+1108+856"
            }

            c.applySettings(cp)
            actual = c.view._gearSetsWindow.geometry()

            assert "+1108+856" in actual

    class TestSoughtAfterItems:
        def test_ZeroLengthString_ModelHasEmptySoughtAfterItems_Sets(self, testController: Controller):
            cp = configparser.ConfigParser()
            c = testController
            cp[c._VIEW_SETTINGS] = {
                c._SOUGHT_AFTER_ITEMS__OPTION: ""
            }

            c.applySettings(cp)

            assert c.model.SoughtAfterItems_Names == set()
            assert c.model.SoughtAfterItems_BaseItemNames == set()

        def test_ConfigOptionWithItemName_PutsSoughtStringInto_ItemNameSetLookup(self, testController: Controller):
            expected = set(['a fire root'])
            cp = configparser.ConfigParser()
            c = testController
            cp[c._VIEW_SETTINGS] = {
                c._SOUGHT_AFTER_ITEMS__OPTION: "a fire root"
            }

            c.applySettings(cp)

            assert c.model.SoughtAfterItems_Names == expected

        def test_ConfigOptionWithBaseItemName_PutsSoughtStringInto_BaseItemNameSet(self, testController: Controller):
            expected = set(['fire root'])
            cp = configparser.ConfigParser()
            c = testController
            cp[c._VIEW_SETTINGS] = {
                c._SOUGHT_AFTER_ITEMS__OPTION: "fire root"
            }

            c.applySettings(cp)

            assert c.model.SoughtAfterItems_BaseItemNames == expected

        def test_SequenceOfSemicolonDelimited_ItemNames_AddedToNamesSet(self, testController: Controller):
            expected = set(['a fire root', 'a pound of steel', 'a small vial of magma'])
            cp = configparser.ConfigParser()
            c = testController
            cp[c._VIEW_SETTINGS] = {
                c._SOUGHT_AFTER_ITEMS__OPTION: "a fire root; a pound of steel; a small vial of magma"
            }

            c.applySettings(cp)

            assert c.model.SoughtAfterItems_Names == expected

        def test_SequenceOfSemicolonDelimited_ItemNameAndBaseItemNames_AddedToRespectiveSets(self, testController: Controller):
            expectedNamesSet = set(['a fire root', 'a pound of steel'])
            expectedBaseItemNamesSet = set(['small vial of magma', 'skeletal dragon bone'])
            cp = configparser.ConfigParser()
            c = testController
            cp[c._VIEW_SETTINGS] = {
                c._SOUGHT_AFTER_ITEMS__OPTION: "a fire root; a pound of steel; small vial of magma; skeletal dragon bone"
            }

            c.applySettings(cp)

            assert c.model.SoughtAfterItems_Names == expectedNamesSet
            assert c.model.SoughtAfterItems_BaseItemNames == expectedBaseItemNamesSet

        def test_SequenceOfSemicolonDelimitedValuesWithWhitespaceBetweenDelimiters_WhitespaceNotAddedToLookupSets(self, testController: Controller):
            expected = set(['a fire root', 'a pound of steel', 'a small vial of magma'])
            cp = configparser.ConfigParser()
            c = testController
            cp[c._VIEW_SETTINGS] = {
                c._SOUGHT_AFTER_ITEMS__OPTION: "a fire root;; ; a pound of steel; ; a small vial of magma; "
            }

            c.applySettings(cp)

            assert c.model.SoughtAfterItems_Names == expected

        def test_IdenticalValuesNotAddedToSet_OnlyOneEntryInNamesSet(self, testController: Controller):
            expected = set(['a fire root'])
            cp = configparser.ConfigParser()
            c = testController
            cp[c._VIEW_SETTINGS] = {
                c._SOUGHT_AFTER_ITEMS__OPTION: "a fire root; a fire root; a fire root"
            }

            c.applySettings(cp)

            assert c.model.SoughtAfterItems_Names == expected

    class TestGearSets:
        def test_LastActiveTabInGearSetsNotebook_RestoredToActiveTab(self, testController: Controller):
            cp = configparser.ConfigParser()
            c = testController
            c.view.gearSetsNotebook.select(1)
            cp[c._VIEW_SETTINGS] = {
                c._GEAR_SETS_LAST_ACTIVE_TAB_INDEX__OPTION: c.view.gearSetsNotebook.index(c.view.gearSetsNotebook.select())
            }

            c.applySettings(cp)
            actual = c.activeTabTextInNotebook(c.view.gearSetsNotebook)

            assert actual == "PvE"
        class TestPvpGearSet:
            def test_PvpGearSetOptionEntry_Head(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVP_GEAR_SET_HEAD__OPTION: "a helmet",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPvpHeadEntry.get() == "a helmet"

            def test_PvpGearSetOptionEntry_Jewel1(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVP_GEAR_SET_JEWEL1__OPTION: "a necklace",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPvpJewel1Entry.get() == "a necklace"

            def test_PvpGearSetOptionEntry_Jewel2(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVP_GEAR_SET_JEWEL2__OPTION: "a ring",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPvpJewel2Entry.get() == "a ring"

            def test_PvpGearSetOptionEntry_Cloak(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVP_GEAR_SET_CLOAK__OPTION: "a cloak",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPvpCloakEntry.get() == "a cloak"

            def test_PvpGearSetOptionEntry_Body(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVP_GEAR_SET_BODY__OPTION: "a robe",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPvpBodyEntry.get() == "a robe"

            def test_PvpGearSetOptionEntry_Hands(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVP_GEAR_SET_HANDS__OPTION: "a pair of gloves",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPvpHandsEntry.get() == "a pair of gloves"

            def test_PvpGearSetOptionEntry_Legs(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVP_GEAR_SET_LEGS__OPTION: "a pair of pants",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPvpLegsEntry.get() == "a pair of pants"

            def test_PvpGearSetOptionEntry_Feet(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVP_GEAR_SET_FEET__OPTION: "a pair of boots",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPvpFeetEntry.get() == "a pair of boots"

            def test_PvpGearSetOptionEntry_HeldRight(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVP_GEAR_SET_HELD_RIGHT__OPTION: "a sword",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPvpHeldRightEntry.get() == "a sword"

            def test_PvpGearSetOptionEntry_HeldLeft(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVP_GEAR_SET_HELD_LEFT__OPTION: "a shield",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPvpHeldLeftEntry.get() == "a shield"

        class TestPveGearSet:
            def test_PveGearSetOptionEntry_Head(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVE_GEAR_SET_HEAD__OPTION: "a helmet",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPveHeadEntry.get() == "a helmet"

            def test_PveGearSetOptionEntry_Jewel1(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVE_GEAR_SET_JEWEL1__OPTION: "a necklace",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPveJewel1Entry.get() == "a necklace"

            def test_PveGearSetOptionEntry_Jewel2(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVE_GEAR_SET_JEWEL2__OPTION: "a ring",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPveJewel2Entry.get() == "a ring"

            def test_PveGearSetOptionEntry_Cloak(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVE_GEAR_SET_CLOAK__OPTION: "a cloak",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPveCloakEntry.get() == "a cloak"

            def test_PveGearSetOptionEntry_Body(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVE_GEAR_SET_BODY__OPTION: "a robe",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPveBodyEntry.get() == "a robe"

            def test_PveGearSetOptionEntry_Hands(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVE_GEAR_SET_HANDS__OPTION: "a pair of gloves",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPveHandsEntry.get() == "a pair of gloves"

            def test_PveGearSetOptionEntry_Legs(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVE_GEAR_SET_LEGS__OPTION: "a pair of pants",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPveLegsEntry.get() == "a pair of pants"

            def test_PveGearSetOptionEntry_Feet(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVE_GEAR_SET_FEET__OPTION: "a pair of boots",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPveFeetEntry.get() == "a pair of boots"

            def test_PveGearSetOptionEntry_HeldRight(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVE_GEAR_SET_HELD_RIGHT__OPTION: "a sword",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPveHeldRightEntry.get() == "a sword"

            def test_PveGearSetOptionEntry_HeldLeft(self, testController: Controller):
                cp = configparser.ConfigParser()
                c = testController
                cp[c._VIEW_SETTINGS] = {
                    c._PVE_GEAR_SET_HELD_LEFT__OPTION: "a shield",
                }

                c.applySettings(cp)

                assert c.view.gearSetsPveHeldLeftEntry.get() == "a shield"

class TestIsLookingForItem:
    def test_ItemNameInModel_ReturnsTrue(self, testController: Controller):
        c = testController
        c.model.SoughtAfterItems_Names, c.model.SoughtAfterItems_BaseItemNames = c.SoughtAfterItems_SemicolonDelimitedTextToTwoSets('a darkspawned blackened fish fillet;dragon-wing boots')

        assert c.IsLookingForItem('A darkspawned blackened fish fillet')

    def test_ItemBaseNameInModel_ReturnsTrue(self, testController: Controller):
        c = testController
        c.model.SoughtAfterItems_Names, c.model.SoughtAfterItems_BaseItemNames = c.SoughtAfterItems_SemicolonDelimitedTextToTwoSets('a darkspawned blackened fish fillet;dragon-wing boots')

        assert c.IsLookingForItem('dragon-wing boots')

    def test_ItemNotInModel_ReturnsFalse(self, testController: Controller):
        c = testController
        c.model.SoughtAfterItems_Names, c.model.SoughtAfterItems_BaseItemNames = c.SoughtAfterItems_SemicolonDelimitedTextToTwoSets('a darkspawned blackened fish fillet;dragon-wing boots')

        assert not c.IsLookingForItem('A goblet of zombie blood')

class TestGearSets:
    class TestBankWithdrawalText:
        def test_gearSetWithNoEntriesFilled_DisplaysMessageBoxToUser(self, testController: Controller):
            c = testController
            text: str
            with patch.object(tkinter.messagebox, tkinter.messagebox.showinfo.__name__) as mockedShowInfo:
                text =c.gearSetBankWidthdrawalTextFromActiveGearSetTab()

            assert text == ''
            mockedShowInfo.assert_called()

        def test_gearSetWithAllEntriesFilled_CreatesWithdrawalText(self, testController: Controller):
            expected = 'withdraw ' + ', withdraw '.join(["a wispweave spellbinder's crown",
                                                        "a mark of vigilance",
                                                        "a twisted gold torc",
                                                        "a glowing worldwalker's cloak",
                                                        "a gossamer noble's gleaming raiment of evasion",
                                                        "a gossamer noble's gleaming gloves of intelligence",
                                                        "a glowing gossamer hierophant's legwraps",
                                                        "a glowing wispweave dragon-wing boots",
                                                        "a bright jeweled greatsword of the phoenix"])

            c = testController
            v = c.view

            #deliberate use of non-default index to avoid false positive
            v.gearSetsNotebook.select(0)
            v.gearSetsPvpHeadEntry.insert(0, "A WISPWEAVE spellbinder's crown")
            v.gearSetsPvpJewel1Entry.insert(0, "A mark of vigilance")
            v.gearSetsPvpJewel2Entry.insert(0, "A twisted gold torc")
            v.gearSetsPvpCloakEntry.insert(0, "A GLOWING worldwalker's cloak")
            v.gearSetsPvpBodyEntry.insert(0, "a GOSSAMER noble's gleaming raiment of evasion")
            v.gearSetsPvpHandsEntry.insert(0, "A GOSSAMER noble's gleaming gloves of intelligence")
            v.gearSetsPvpLegsEntry.insert(0, "A GLOWING GOSSAMER hierophant's legwraps")
            v.gearSetsPvpFeetEntry.insert(0, "A GLOWING WISPWEAVE dragon-wing boots")
            v.gearSetsPvpHeldRightEntry.insert(0, "A bright jeweled greatsword of the phoenix")
            v.gearSetsPvpHeldLeftEntry.insert(0, "A bright jeweled greatsword of the phoenix")

            actualText = c.gearSetBankWidthdrawalTextFromActiveGearSetTab()
            assert actualText == expected

        def test_gearSetWithSomeEntriesFilled_CreatesWithdrawalTextWithOnlyFilledEntries(self, testController: Controller):
            expected = 'withdraw ' + ', withdraw '.join(["a wispweave spellbinder's crown",
                                                        "a gossamer noble's gleaming gloves of intelligence",
                                                        "a glowing wispweave dragon-wing boots"])

            c = testController
            v = c.view

            #deliberate use of non-default index to avoid false positive
            v.gearSetsNotebook.select(0)
            v.gearSetsPvpHeadEntry.insert(0, "A WISPWEAVE spellbinder's crown")
            v.gearSetsPvpHandsEntry.insert(0, "A GOSSAMER noble's gleaming gloves of intelligence")
            v.gearSetsPvpFeetEntry.insert(0, "A GLOWING WISPWEAVE dragon-wing boots")

            actualText = c.gearSetBankWidthdrawalTextFromActiveGearSetTab()
            assert actualText == expected

    class TestCopyingPastedEquipmentTextToEntryInputs:
        def test_NothingPastedIntoText_DisplaysMessageBoxToUser(self, testController: Controller):
            c = testController

            with patch.object(tkinter.messagebox, tkinter.messagebox.showinfo.__name__) as mockedShowInfo:
                c.copyPastedGearSetTextToActiveTabEntries('')

            argument = mockedShowInfo.mock_calls[0].args[0]

            assert argument == "No pasted text"

        def test_NothingEquipped_DisplaysMessageBoxToUser(self, testController: Controller):
            c = testController
            text = """     On Head:  nothing
    On Jewel:  nothing
    On Jewel:  nothing
    On Cloak:  nothing
     On Body:  nothing
    On Hands:  nothing
     On Legs:  nothing
     On Feet:  nothing
  Held Right:  nothing
   Held Left:  nothing"""

            with patch.object(tkinter.messagebox, tkinter.messagebox.showinfo.__name__) as mockedShowInfo:
                c.copyPastedGearSetTextToActiveTabEntries(text)

            argument = mockedShowInfo.mock_calls[0].args[0]

            assert argument == "No gear worn"

        @pytest.mark.parametrize('clearMethod, tabIndex', [(Controller.ForTesting().view.clearPveSetEntries, 1),
                                                           (Controller.ForTesting().view.clearPvpSetEntries, 0)],
                                                ids=['PveTab', 'PvpTab'])
        def test_PriorEntriesCleared_BeforeCopyingPastedTextToEntries(self, testController, clearMethod, tabIndex):
            c = testController
            text = """     On Cloak:  A valid cloak"""

            c.view.gearSetsNotebook.select(tabIndex)
            with patch.object(c.view, clearMethod.__name__) as mockedClearMethod:
                c.copyPastedGearSetTextToActiveTabEntries(text)

            mockedClearMethod.assert_called_once()

        def test_SomeGearEquipped_PastedIntoCorrespondingInput(self, testController: Controller):
            c = testController
            text = """     On Head:  nothing
    On Jewel:  nothing
    On Jewel:  A rag doll
    On Cloak:  nothing
     On Body:  nothing
    On Hands:  nothing
     On Legs:  Leggings of the Quackhead
     On Feet:  nothing
  Held Right:  nothing
   Held Left:  nothing"""

            c.view.gearSetsNotebook.select(1)
            c.copyPastedGearSetTextToActiveTabEntries(text)

            assert c.view.gearSetsPveJewel1Entry.get() == "A rag doll"
            assert c.view.gearSetsPveLegsEntry.get() == "Leggings of the Quackhead"

        def test_FullGearSetEquipped_AllPastedIntoCorrespondingInputs(self, testController: Controller):
            c = testController
            text = """     On Head:  hat
    On Jewel:  necklace
    On Jewel:  secondNecklace
    On Cloak:  cloak
     On Body:  shirt
    On Hands:  gloves
     On Legs:  pants
     On Feet:  shoes
  Held Right:  knife
   Held Left:  shield"""

            c.view.gearSetsNotebook.select(1)
            c.copyPastedGearSetTextToActiveTabEntries(text)

            assert c.view.gearSetsPveHeadEntry.get() == "hat"
            assert c.view.gearSetsPveJewel1Entry.get() == "necklace"
            assert c.view.gearSetsPveJewel2Entry.get() == "secondNecklace"
            assert c.view.gearSetsPveCloakEntry.get() == "cloak"
            assert c.view.gearSetsPveBodyEntry.get() == "shirt"
            assert c.view.gearSetsPveHandsEntry.get() == "gloves"
            assert c.view.gearSetsPveLegsEntry.get() == "pants"
            assert c.view.gearSetsPveFeetEntry.get() == "shoes"
            assert c.view.gearSetsPveHeldRightEntry.get() == "knife"
            assert c.view.gearSetsPveHeldLeftEntry.get() == "shield"

    class TestClearingGearSetEntries:
        def test_PveSetsLeavesInputsEmpty(self, testController: Controller):
            c = testController
            v = c.view

            v.gearSetsNotebook.select(1)
            v.gearSetsPveHeadEntry.insert(0, "Any")
            v.gearSetsPveJewel1Entry.insert(0, "text")
            v.gearSetsPveJewel2Entry.insert(0, "to")
            v.gearSetsPveCloakEntry.insert(0, "test")
            v.gearSetsPveBodyEntry.insert(0, "clearing")
            v.gearSetsPveHandsEntry.insert(0, "the")
            v.gearSetsPveLegsEntry.insert(0, "gear")
            v.gearSetsPveFeetEntry.insert(0, "set")
            v.gearSetsPveHeldRightEntry.insert(0, "input")
            v.gearSetsPveHeldLeftEntry.insert(0, "fields")

            c.clearGearSetEntriesOnActiveTab()

            assert v.gearSetsPveHeadEntry.get() == ""
            assert v.gearSetsPveJewel1Entry.get() == ""
            assert v.gearSetsPveJewel2Entry.get() == ""
            assert v.gearSetsPveCloakEntry.get() == ""
            assert v.gearSetsPveBodyEntry.get() == ""
            assert v.gearSetsPveHandsEntry.get() == ""
            assert v.gearSetsPveLegsEntry.get() == ""
            assert v.gearSetsPveFeetEntry.get() == ""
            assert v.gearSetsPveHeldRightEntry.get() == ""
            assert v.gearSetsPveHeldLeftEntry.get() == ""

        def test_PvpSetsLeavesInputsEmpty(self, testController: Controller):
            c = testController
            v = c.view

            v.gearSetsNotebook.select(0)
            v.gearSetsPvpHeadEntry.insert(0, "Any")
            v.gearSetsPvpJewel1Entry.insert(0, "text")
            v.gearSetsPvpJewel2Entry.insert(0, "to")
            v.gearSetsPvpCloakEntry.insert(0, "test")
            v.gearSetsPvpBodyEntry.insert(0, "clearing")
            v.gearSetsPvpHandsEntry.insert(0, "the")
            v.gearSetsPvpLegsEntry.insert(0, "gear")
            v.gearSetsPvpFeetEntry.insert(0, "set")
            v.gearSetsPvpHeldRightEntry.insert(0, "input")
            v.gearSetsPvpHeldLeftEntry.insert(0, "fields")

            c.clearGearSetEntriesOnActiveTab()

            assert v.gearSetsPvpHeadEntry.get() == ""
            assert v.gearSetsPvpJewel1Entry.get() == ""
            assert v.gearSetsPvpJewel2Entry.get() == ""
            assert v.gearSetsPvpCloakEntry.get() == ""
            assert v.gearSetsPvpBodyEntry.get() == ""
            assert v.gearSetsPvpHandsEntry.get() == ""
            assert v.gearSetsPvpLegsEntry.get() == ""
            assert v.gearSetsPvpFeetEntry.get() == ""
            assert v.gearSetsPvpHeldRightEntry.get() == ""
            assert v.gearSetsPvpHeldLeftEntry.get() == ""

    def test_CopyingPvpGearSetToPve(self, testController: Controller):
        c = testController
        v = c.view

        v.gearSetsPvpHeadEntry.insert(0, "hat")
        v.gearSetsPvpJewel1Entry.insert(0, "necklace")
        v.gearSetsPvpJewel2Entry.insert(0, "secondNecklace")
        v.gearSetsPvpCloakEntry.insert(0, "cloak")
        v.gearSetsPvpBodyEntry.insert(0, "shirt")
        v.gearSetsPvpHandsEntry.insert(0, "gloves")
        v.gearSetsPvpLegsEntry.insert(0, "pants")
        v.gearSetsPvpFeetEntry.insert(0, "shoes")
        v.gearSetsPvpHeldRightEntry.insert(0, "knife")
        v.gearSetsPvpHeldLeftEntry.insert(0, "shield")

        c.copyPvpGearSetToPve()

        assert c.view.gearSetsPveHeadEntry.get() == "hat"
        assert c.view.gearSetsPveJewel1Entry.get() == "necklace"
        assert c.view.gearSetsPveJewel2Entry.get() == "secondNecklace"
        assert c.view.gearSetsPveCloakEntry.get() == "cloak"
        assert c.view.gearSetsPveBodyEntry.get() == "shirt"
        assert c.view.gearSetsPveHandsEntry.get() == "gloves"
        assert c.view.gearSetsPveLegsEntry.get() == "pants"
        assert c.view.gearSetsPveFeetEntry.get() == "shoes"
        assert c.view.gearSetsPveHeldRightEntry.get() == "knife"
        assert c.view.gearSetsPveHeldLeftEntry.get() == "shield"

    def test_CopyingPveGearSetToPvp(self, testController: Controller):
        c = testController
        v = c.view

        v.gearSetsPveHeadEntry.insert(0, "hat")
        v.gearSetsPveJewel1Entry.insert(0, "necklace")
        v.gearSetsPveJewel2Entry.insert(0, "secondNecklace")
        v.gearSetsPveCloakEntry.insert(0, "cloak")
        v.gearSetsPveBodyEntry.insert(0, "shirt")
        v.gearSetsPveHandsEntry.insert(0, "gloves")
        v.gearSetsPveLegsEntry.insert(0, "pants")
        v.gearSetsPveFeetEntry.insert(0, "shoes")
        v.gearSetsPveHeldRightEntry.insert(0, "knife")
        v.gearSetsPveHeldLeftEntry.insert(0, "shield")

        c.copyPveGearSetToPvp()

        assert c.view.gearSetsPvpHeadEntry.get() == "hat"
        assert c.view.gearSetsPvpJewel1Entry.get() == "necklace"
        assert c.view.gearSetsPvpJewel2Entry.get() == "secondNecklace"
        assert c.view.gearSetsPvpCloakEntry.get() == "cloak"
        assert c.view.gearSetsPvpBodyEntry.get() == "shirt"
        assert c.view.gearSetsPvpHandsEntry.get() == "gloves"
        assert c.view.gearSetsPvpLegsEntry.get() == "pants"
        assert c.view.gearSetsPvpFeetEntry.get() == "shoes"
        assert c.view.gearSetsPvpHeldRightEntry.get() == "knife"
        assert c.view.gearSetsPvpHeldLeftEntry.get() == "shield"

    class TestCheckGearSetAgainstWornItems:
        def test_NoGearWorn(self, testController: Controller):
            c = testController

            with patch.object(tkinter.messagebox, tkinter.messagebox.showinfo.__name__) as mockedShowInfo:
                c.checkGearSet(Equipment(), Equipment())

            mockedShowInfo.assert_called_once()

        def test_NoGearMissingFromGearSet(self, testController: Controller):
            c = testController
            v = c.view
            viewEq = Equipment(Item("hat"))
            wornEq = Equipment(Item("hat"))
            with patch.object(v, v.displayMissingGearSetItemsLabel.__name__) as mockedDisplay:
                c.checkGearSet(viewEq, wornEq)

            mockedDisplay.assert_called_once_with('')

        def test_GearMissingFromGearSet(self, testController: Controller):
            c = testController
            v = c.view
            viewEq = Equipment(Item("hat"), Item("cloak"))
            wornEq = Equipment(Item("hat"))

            with patch.object(v, v.displayMissingGearSetItemsLabel.__name__) as mockedDisplay:
                c.checkGearSet(viewEq, wornEq)
            argument = mockedDisplay.mock_calls[0].args[0]

            assert 'Missing' in argument

        def test_MoreGearWornThanInGearSet_NoMissingGearDisplayed(self, testController: Controller):
            c = testController
            v = c.view
            viewEq = Equipment(Item("hat"))
            wornEq = Equipment(Item("hat"), Item("cloak"))

            with patch.object(v, v.displayMissingGearSetItemsLabel.__name__) as mockedDisplay:
                c.checkGearSet(viewEq, wornEq)

            mockedDisplay.assert_called_once_with('')
