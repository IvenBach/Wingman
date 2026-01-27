from Wingman.core.character import Character
from Wingman.core.group import Group
from Wingman.core.status_indicator import StatusIndicator
from Wingman.core.resource_bar import ResourceBar

class TestGroup:
    def test_GroupCreation(self):
        g = Group([Character("Foo", 
                                "Skeleton", 
                                1, 
                                StatusIndicator(0), 
                                ResourceBar(2, 3), 
                                ResourceBar(4, 5), 
                                ResourceBar(6, 7))])
        assert isinstance(g, Group)
    
    def test_StringName_ReturnsLeader(self):
        c = Character("Foo", 
                        "Skeleton", 
                        1, 
                        StatusIndicator(0), 
                        ResourceBar(2, 3), 
                        ResourceBar(4, 5), 
                        ResourceBar(6, 7))
        member = Character("Foo", 
                            "Bar", 
                            11, 
                            StatusIndicator(0),  
                            ResourceBar(22, 33), 
                            ResourceBar(44, 55), 
                            ResourceBar(66, 77))
        g = Group([c])
        g.AddMembers([member])
        leader = g.Leader

        assert leader == c
    
    def test_CharacterObject_ReturnsLeader(self):
        c = Character("Foo", 
                        "Skeleton", 
                        1, 
                        StatusIndicator(0), 
                        ResourceBar(2, 3), 
                        ResourceBar(4, 5), 
                        ResourceBar(6, 7))
        member = Character("Foo", 
                            "Bar", 
                            11, 
                            StatusIndicator(0), 
                            ResourceBar(22, 33), 
                            ResourceBar(44, 55), 
                            ResourceBar(66, 77))
        g = Group([c])
        g.AddMembers([member])
        leader = g.Leader

        assert leader == c
    
    def test_RemovingMember_BasedOnStringName_SucceedsWhenMemberExists(self):
        c = Character("Foo", 
                        "Skeleton", 
                        1, 
                        StatusIndicator(0), 
                        ResourceBar(2, 3), 
                        ResourceBar(4, 5), 
                        ResourceBar(6, 7))
        member = Character("Foo", 
                            "Bar", 
                            11, 
                            StatusIndicator(0), 
                            ResourceBar(22, 33), 
                            ResourceBar(44, 55), 
                            ResourceBar(66, 77))
        g = Group([c])
        g.AddMembers([member])
        countBeforeRemoval = g.Count

        g.RemoveMembers([member.Name])
        countAfterRemoval = g.Count

        assert countBeforeRemoval == 2
        assert countAfterRemoval == 1

    def test_ClearingGroup_LeaderReturnsNone(self):
        c = Character("Foo", "Troll")
        g = Group([c])
        g.Disband()

        assert g.Leader is None