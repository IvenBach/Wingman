from Wingman.core.controller import Controller

class TestProcessQueue():
    def test_process_queue_calculates_xp(self):
        c = Controller.ForTesting()
        inputs = ["You gain 1000 experience points.", "Garbage line."]
        for x in inputs:
            c.receiver.receive(x)

        logs = c.process_queue()

        assert c.gameSession.total_xp == 1000
        assert len(logs) == 1

class TestGrouping():
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

