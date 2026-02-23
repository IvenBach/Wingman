import unittest.mock
import pytest
from unittest.mock import patch
from pathlib import Path
import sys
import configparser
import tkinter as tk

if __name__ == "__main__":
    srcDirectory = Path(__file__).parent.parent.parent.resolve()
    sys.path.append(str(srcDirectory))

from Wingman.core.controller import Controller
from Wingman.core.parser import Parser
from Wingman.core.health_Tagger import HealthTagger
from Wingman.core.inventory import EquippedGear, Inventory
from Wingman.core.item import Item

class TestProcessQueue():
    def test_process_queue_calculates_xp(self):
        c = Controller.ForTesting()
        inputs = ["You gain 1000 experience points.", "Garbage line."]
        for x in inputs:
            c.receiver.receive(x)

        logs = c.process_queue()

        assert c.gameSession.total_xp == 1000
        assert len(logs) == 1

    class TestMobRoomMovement:
        def test_MobMovement_Enters_EmptyRoom_DisplayUpdatesAndMobsInRoomMatchesExpected(self):
            c = Controller.ForTesting()
            c.model.currentMobsInRoom = []
            v = c.view

            c.receiver.receive("A windfang hatchling enters the room.")
            c.process_queue()

            with patch.object(v, v.updateMobCountDisplay.__name__) as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_called_once_with()
            assert c.model.currentMobsInRoom == ['a windfang hatchling']

        def test_MobMovement_ArrivesFrom_With2Mobs_DisplayUpdatesAndMobsInRoomMatchesExpected(self):
            c = Controller.ForTesting()
            c.model.currentMobsInRoom = ['a foo bar', 'a bar foo']
            v = c.view

            c.receiver.receive("A windfang hatchling arrives from the east.")
            c.process_queue()

            with patch.object(v, v.updateMobCountDisplay.__name__) as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_called_once_with()
            assert c.model.currentMobsInRoom == ['a foo bar', 'a bar foo', 'a windfang hatchling']

        def test_MobMovement_ChasesIn_With1Mob_DisplayUpdatesAndMobsInRoomMatchesExpected(self):
            c = Controller.ForTesting()
            c.model.currentMobsInRoom = ['a foo bar']
            v = c.view

            c.receiver.receive("A windfang hatchling chases Foo into the room.")
            c.process_queue()

            with patch.object(v, v.updateMobCountDisplay.__name__) as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_called_once_with()
            assert c.model.currentMobsInRoom == ['a foo bar', 'a windfang hatchling']

        def test_MobMovement_Dies_With2MobsInRoom_DisplayUpdatesAndMobsInRoomMatchesExpected(self):
            c = Controller.ForTesting()
            c.model.currentMobsInRoom = ['a foo bar', 'a windfang hatchling']
            v = c.view

            c.receiver.receive("A windfang hatchling dies.")
            c.process_queue()

            with patch.object(v, v.updateMobCountDisplay.__name__) as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_called_once_with()
            assert c.model.currentMobsInRoom == ['a foo bar']

        def test_MobMovement_Leaves_With5MobsInRoom_DisplayUpdatesAndMobsInRoomMatchesExpected(self):
            c = Controller.ForTesting()
            c.model.currentMobsInRoom = ['a foo bar', 'a bar foo', 'a dog', 'a cat', 'a windfang hatchling']
            v = c.view

            c.receiver.receive("A cat leaves North.")
            c.process_queue()

            with patch.object(v, v.updateMobCountDisplay.__name__) as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_called_once_with()
            assert c.model.currentMobsInRoom == ['a foo bar', 'a bar foo', 'a dog', 'a windfang hatchling']

        def test_MobMovement_ChasesOut_AsOnlyMobInTheRoom_DisplayUpdatesAndMobsInRoomMatchesExpected(self):
            c = Controller.ForTesting()
            c.model.currentMobsInRoom = ['a windfang hatchling']
            v = c.view

            c.receiver.receive("A windfang hatchling chases Foo out of the room.")
            c.process_queue()

            with patch.object(v, v.updateMobCountDisplay.__name__) as mockedDisplay:
                v.update_gui()

            mockedDisplay.assert_called_once_with()
            assert c.model.currentMobsInRoom == []

    class TestPlayerMovement:
        def test_PlayerMovement_ClearsMobsInRoomAndHidesMobCountInView(self):
            c = Controller.ForTesting()
            
            c.receiver.receive("Obvious exits: east, northwest, and a small, smelly hut.")
            with patch.object(c, c.clearCountOfMobsInRoom.__name__) as mockedClear:
                with patch.object(c, c.updateMobCountDisplay.__name__) as mockedUpdate:
                    c.process_queue()
            
            mockedClear.assert_called_once_with()
            mockedUpdate.assert_called_once_with()

    class TestModelUpdates:
        def test_InventoryCommand__THEN__EquipmentCommand_EquippedGearCorrectlyOverwritesAssumedInventoryPositions(self):
            expectedEG = EquippedGear(head=Item("A WISPWEAVE spellbinder's crown"),
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

            c = Controller.ForTesting()
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

class TestGrouping:
    def test_GainNewFollower_NewFollowerAddedToGroupForDisplay(self):
        c = Controller.ForTesting()
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
    
    def test_LoseFollower_FollowerRemovedFromGroupForDisplay(self):
        c = Controller.ForTesting()
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
    
    def test_GainNewFollowerAndLoseFollower_WithoutInvokingGroupCommand_CountsCorrectlyForAdditionAndRemoval(self):        
        c = Controller.ForTesting()
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

    def test_FollowedByTwoIdenticallyDisguisedCharacters_BothAddedToGroupForDisplay(self):
        c = Controller.ForTesting()
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

    def test_GroupMemberZeroed_DisplaysZeroedFormatting(self):
        c = Controller.ForTesting()
        c.receiver.receive("""Foo's group:
[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Bar            01]            Foo                 1/ 500 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   """)
        
        c.view.update_gui()
        member = c.view.groupTreeview.get_children()[0]
        healthTags = c.view.groupTreeview.item(member, 'tags')

        assert HealthTagger.HealthLevels.ZEROED.value in healthTags
    
    def test_GroupMemberInRedHealth_DisplaysRedHealthFormatting(self):
        c = Controller.ForTesting()
        c.receiver.receive("[Bar            01]            Foo                 25/ 100 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   """)
        c.view.update_gui()
        member = c.view.groupTreeview.get_children()[0]

        healthTags = c.view.groupTreeview.item(member, 'tags')

        assert HealthTagger.HealthLevels.AT_OR_BELOW_25.value in healthTags

    def test_GroupMemberInYellowHealth_DisplaysYellowHealthFormatting(self):
        c = Controller.ForTesting()
        c.receiver.receive("[Bar            01]            Foo                 50/ 100 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   ")
        c.view.update_gui()
        member = c.view.groupTreeview.get_children()[0]

        healthTags = c.view.groupTreeview.item(member, 'tags')

        assert HealthTagger.HealthLevels.AT_OR_BELOW_50.value in healthTags
    
    def test_GroupMemberInGoodHealth_DisplaysNoHealthFormatting(self):
        c = Controller.ForTesting()
        c.receiver.receive("[Bar            01]            Foo                 51/ 100 (  0%)      497/ 500 ( 99%)    592/ 707 ( 83%)   ")
        c.view.update_gui()
        member = c.view.groupTreeview.get_children()[0]

        healthTags = c.view.groupTreeview.item(member, 'tags')

        assert HealthTagger.HealthLevels.HEALTHY.value in healthTags

    def test_UngroupedCharacterGainsNewFollower_NewFollowerAddedToLatestGroupData(self):
        c = Controller.ForTesting()

        c.receiver.receive("FooBar follows you")
        c.process_queue()

        assert c.gameSession.group.Count == 1

    def test_LeaderGainsNewFollower_NewFollowerAddedToLatestGroupData(self):
        c = Controller.ForTesting()
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

    def test_LeavingGroup_ClearsLatestGroupData(self):
        c = Controller.ForTesting()
        
        groupCommandText = """Foo's group:

    [ Class      Lv] Status   Name              Hits            Fat             Power         
    [Necromance   9]         Foo              100/100 (100%)  100/100 (100%)  119/119 (100%)  

    [Sin         74]         Beautiful        500/500 (100%)  383/500 ( 76%)  503/731 ( 68%)  """

        c.receiver.receive(groupCommandText)
        c.process_queue()

        groupCountWhileMemberOfGroup = c.gameSession.group.Count

        c.receiver.receive("You disband from the group.")
        c.process_queue()

        assert groupCountWhileMemberOfGroup == 2
        assert c.gameSession.group.Count == 0
    
    def test_nonGroupLeaderLeavesGroup_IsRemovedFromLatestGroupData(self):
        c = Controller.ForTesting()

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
    
    def test_IncludeMobsInGroup_MobsDisplayInGroupDisplay(self):
        c = Controller.ForTesting()
        c.model.includePetsInGroup = True
        text = """Beautiful's group:

[ Class      Lv] Status   Name              Hits            Fat             Power         
[Sin         74]         Beautiful        500/500 (100%)  500/500 (100%)  687/731 ( 93%)  
[mob         72]         angel of death   417/417 (100%)  417/417 (100%)  618/618 (100%)  """

        c.receiver.receive(text)

        c.process_queue()

        assert c.gameSession.group.Count == 2

class TestDisplayingCentralColumnLabelInView:
    def test_DisplayAfkLabel(self):
        c = Controller.ForTesting()
        v = c.view
        c.receiver.receive(Parser.AfkStatus.BeginAfk.value)
        c.process_queue()

        with patch.object(v, v.displayAfkLabel.__name__) as mockedMethod:
            v.update_gui()

        mockedMethod.assert_called_once_with()
    
    def test_HideAfkLabel(self):
        c = Controller.ForTesting()
        v = c.view
        c.receiver.receive(Parser.AfkStatus.EndAfk.value)
        c.process_queue()

        with patch.object(v, v.hideAfkLabel.__name__) as mockedMethod:
            v.update_gui()

        mockedMethod.assert_called_once_with()

    def test_BeginMeditating_MeditationLabelDisplayedInView(self):
        c = Controller.ForTesting()
        v = c.view
        c.receiver.receive(Parser.MeditationState.Begin.value)
        c.process_queue()

        with patch.object(v, v.displayMeditationLabel.__name__) as mockedMethod:
            v.update_gui()

        mockedMethod.assert_called_once_with()

    @pytest.mark.parametrize("input_line", [Parser.MeditationState.Termination_ByStanding.value, Parser.MeditationState.Termination_ByInterruption.value],
                                        ids=['VoluntaryTermination', 'NonVoluntaryTermination'])
    def test_StopMeditating_MeditationLabelHiddenInView(self, input_line):
        c = Controller.ForTesting()
        v = c.view
        c.receiver.receive(input_line)
        c.process_queue()

        with patch.object(v, v.hideMeditationLabel.__name__) as mockedMethod:
            v.update_gui()

        mockedMethod.assert_called_once_with()

    def test_MeditationNotAffectedByNonMeditationInput_NeitherDisplayNorHideInvoked(self):
        c = Controller.ForTesting()
        v = c.view
        c.receiver.receive("Any text not relating to meditation.")

        c.process_queue()

        with patch.object(v, v.displayMeditationLabel.__name__) as mockedDisplay:
            with patch.object(v, v.hideMeditationLabel.__name__) as mockedHide:
                v.update_gui()
        
        mockedDisplay.assert_not_called()
        mockedHide.assert_not_called()

    def test_MeditationRegenValueChanges_ObserverNotified(self):
        c = Controller.ForTesting()
        c.receiver.receive(Parser.MeditationState.Begin.value)
        c.process_queue()
        md = c.model.meditationDisplay
        with patch.object(md, md.meditationDurationInSeconds.__name__) as mockedDuration:
            mockedDuration.return_value = 40


    def test_BeginHiding_HideLabelDisplayedInView(self):
        c = Controller.ForTesting()
        v = c.view
        c.receiver.receive(Parser.HideStatus.Begin.value)
        c.process_queue()

        with patch.object(v, v.displayHidingLabel.__name__) as mockedMethod:
            v.update_gui()

        mockedMethod.assert_called_once_with()

    def test_StopHiding_HideLabelHiddenInView(self):
        c = Controller.ForTesting()
        v = c.view
        c.receiver.receive(Parser.HideStatus.EndHiding.value)
        c.process_queue()

        with patch.object(v, v.hideHidingLabel.__name__) as mockedMethod:
            v.update_gui()

        mockedMethod.assert_called_once_with()
    
    def test_HidingNotAffectedByNonHidingInput_NeitherDisplayNorHideInvoked(self):
        c = Controller.ForTesting()
        v = c.view
        c.receiver.receive("Any text not relating to hiding.")
        c.process_queue()

        with patch.object(v, v.displayHidingLabel.__name__) as mockedDisplay:
            with patch.object(v, v.hideHidingLabel.__name__) as mockedHide:
                v.update_gui()
        
        mockedDisplay.assert_not_called()
        mockedHide.assert_not_called()

class TestIgnoredMobsInRoom:
    def test_UpdatingIgnoredMobsPets_WithCsvIncludingWhitespace_WhitespaceTrimmedAndNotIncludedInModel(self):
        c = Controller.ForTesting()
        c.updateIgnoredMobsPets(' foo, bar ,baz ')

        assert c.model.ignoreTheseMobsInCurrentRoom == ['foo', 'bar', 'baz']

    def test_UpdatingIgnoredMobsPets_WithEmptyInput_ClearsIgnoredMobs(self):
        c = Controller.ForTesting()
        c.updateIgnoredMobsPets('foo,bar,baz')

        c.updateIgnoredMobsPets('')
        
        assert c.model.ignoreTheseMobsInCurrentRoom == []

    def test_UpdatingIgnoredMobsPets_WhenDifferentCsvMobsEntered_ClearsOldValuesLeavingOnlyNew(self):
        c = Controller.ForTesting()
        c.updateIgnoredMobsPets('foo,bar,baz')
        
        c.updateIgnoredMobsPets('a, b, c, d')

        assert c.model.ignoreTheseMobsInCurrentRoom == ['a', 'b', 'c', 'd']

    def test_InvokingUpdateMobsInRoom_WhenCurrentRoomHasMobListedInIgnoredMobs__RemovesMobFromCurrentRoomMobsOnModel(self):
        c = Controller.ForTesting()
        c.model.currentMobsInRoom = ['a foo', 'a bar', 'a baz']
        c.updateIgnoredMobsPets('a foo')

        c.removedIgnoredMobsFromCurrentRoom()

        assert c.model.currentMobsInRoom == ['a bar', 'a baz']

    def test_ClearingCountOfMobsInRoom_ReflectedInModel(self):
        c = Controller.ForTesting()
        c.model.currentMobsInRoom = ['a foo', 'a bar', 'a baz']

        c.clearCountOfMobsInRoom()

        assert c.model.currentMobsInRoom == []

class TestSettings:
    def test_ApplySettings_WhenSettingsFileIsMissingAKey_FallbackValueIsUsed_OpenNotInvokedToWriteFile(self):
        c = Controller.ForTesting()

        with patch('builtins.open', new_callable=unittest.mock.mock_open()) as mockedOpen:
            c.applySettings(configParser=configparser.ConfigParser())
        
        mockedOpen.assert_not_called()
    
    def test_SaveSettings_OpenInvoked(self):
        c = Controller.ForTesting()

        with patch('builtins.open', new_callable=unittest.mock.mock_open()) as mockedOpen:
            c.saveSettings()
        
        mockedOpen.assert_called_once_with(unittest.mock.ANY, 'w')

    def test_LoadSettings_AppliesMobPetIgnore(self):
        c = Controller.ForTesting()
        cp = configparser.ConfigParser()
        cp.add_section(c._VIEW_SETTINGS)
        cp.add_section(c._APP_SETTINGS)
        cp[c._VIEW_SETTINGS][c._IGNORED_MOB_PETS_CSV__OPTION] = 'foo, bar, baz'
        
        with patch.object(c, c.updateIgnoredMobsPets.__name__) as mockedUpdateIgnoredMobsPets:
            with patch('builtins.open', new_callable=unittest.mock.mock_open()) as mockedOpen:
                c.applySettings(cp)
        
        mockedOpen.assert_not_called()
        mockedUpdateIgnoredMobsPets.assert_called_once_with('foo, bar, baz')

class TestCheckInvasionSupplies:
    def test_HavingEqualItemInSupplyList_NoEntries(self):
        c = Controller.ForTesting()
        inventory = Inventory(EquippedGear(),
                      [Parser.parseQuantityItem("(2) A darkspawned black fish fillet")])
        supplyText = "( 2) A darkspawned black fish fillet"


        items = c.check_invasion_supplies(supplyText, inventory)

        assert len(items) == 0

    def test_HavingLessThanItemInSupplyList_ReturnsMissingQuantity(self):
        c = Controller.ForTesting()
        inventory = Inventory(EquippedGear(),
                      [Parser.parseQuantityItem("(1) A darkspawned black fish fillet")])
        supplyText = "( 2) A darkspawned black fish fillet"


        items = c.check_invasion_supplies(supplyText, inventory)

        assert len(items) == 1
        assert items[0].Name == "A darkspawned black fish fillet"
        assert items[0].Quantity == 1

    def test_HavingMoreThanItemInSupplyList_NoEntries(self):
        c = Controller.ForTesting()
        inventory = Inventory(EquippedGear(),
                      [Parser.parseQuantityItem("(5) A darkspawned black fish fillet")])
        supplyText = "( 2) A darkspawned black fish fillet"


        items = c.check_invasion_supplies(supplyText, inventory)

        assert len(items) == 0

    def test_NotHavingItemInSupplyList_ReturnsItemAndQuantityFromSupplyList(self):
        c = Controller.ForTesting()
        inventory = Inventory(EquippedGear(),
                      [Parser.parseQuantityItem("(3) A darkspawned black fish fillet")])
        supplyText = "( 2) A goblet of zombie blood"


        items = c.check_invasion_supplies(supplyText, inventory)

        assert len(items) == 1
        assert items[0].Name == "A goblet of zombie blood"
        assert items[0].Quantity == 2

    def test_AlreadyHaveSomeItems_LackingSomeOnSupplyList_ReturnsOnlyMissingItemsAndTheirQuantities(self):
        c = Controller.ForTesting()
        backpack = [Parser.parseQuantityItem("( 2) A goblet of zombie blood"),
                    Parser.parseQuantityItem("( 4) A darkspawned blackened fish fillet"),
                    Parser.parseQuantityItem("( 2) A bunch of restorative roots"),
                    Parser.parseQuantityItem("( 2) A ticket to Arnak's Plague"),
                    Parser.parseQuantityItem("( 6) A scroll of minor resurrection")]
        inventory = Inventory(EquippedGear(), backpack)
        supplyText = """( 9) A goblet of zombie blood
( 3) A darkspawned blackened fish fillet
(15) A bunch of restorative roots
( 3) A ticket to Arnak's Plague
( 2) A scroll of minor resurrection"""

        items = c.check_invasion_supplies(supplyText, inventory)

        assert len(items) == 3
        assert items[0].Name == "A goblet of zombie blood"
        assert items[0].Quantity == 7
        assert items[1].Name == "A bunch of restorative roots"
        assert items[1].Quantity == 13
        assert items[2].Name == "A ticket to Arnak's Plague"
        assert items[2].Quantity == 1

class TestUpdateInvadeSupplyListLabel:
    def test_EmptySupplyList_AlertsViewOfEmptySupplyList(self):
        c = Controller.ForTesting()
        v = c.view
        inv = Inventory(EquippedGear(), [])
        with patch.object(v, v.updateInvadeSupplyListLabel.__name__) as mockedUpdateLabel:
            c.updateInvadeSupplyListLabel("", inv)

        userHelpfulText = mockedUpdateLabel.mock_calls[0].args[0]
        assert '***' in userHelpfulText
        assert type(userHelpfulText) == str

    def test_EmptyBackpack_AlertsViewThatBackpackIsEmpty(self):
        c = Controller.ForTesting()
        v = c.view
        inv = Inventory(EquippedGear(), [])
        with patch.object(v, v.updateInvadeSupplyListLabel.__name__) as mockedUpdateLabel:
            c.updateInvadeSupplyListLabel("( 2) A goblet of zombie blood", inv)

        userHelpfulText = mockedUpdateLabel.mock_calls[0].args[0]
        assert '***' in userHelpfulText
        assert type(userHelpfulText) == str
