import pytest
from Wingman.core.parser import parse_xp_message, parse_group_status, parse_leaveGroup
from Wingman.core.parser import Character, StatusIndicator, Group, ResourceBar

class TestXPParser:
    def test_parse_compound_xp(self):
        log_line = "You gain 17325 (+43312) experience points."
        assert parse_xp_message(log_line) == 60637

    def test_parse_simple_xp(self):
        log_line = "You gain 150 experience points."
        assert parse_xp_message(log_line) == 150

    def test_ignore_irrelevant_lines(self):
        log_line = "You hit the dragon for 150 damage."
        assert parse_xp_message(log_line) == 0

    def test_parse_strange_formatting(self):
        log_line = "   You gain    10 (+5)    experience points.   "
        assert parse_xp_message(log_line) == 15


class TestGroupParser:
    def test_parse_valid_group_block(self):
        """
        Tests that we can extract multiple members from a raw text block.
        """
        # This simulates a raw chunk from the game
        raw_block = """
        [ Class         Lvl] Status      Name                 Hits                Fat                Power             
        [Orc            40]  B        Earthquack           227/ 394 ( 57%)     354/ 394 ( 89%)     326/ 326 (100%)    
        [Kenku          70]           Big                  550/ 550 (100%)     538/ 550 ( 97%)      63/  73 ( 86%)  
        """

        results = parse_group_status(raw_block)

        assert len(results) == 2

        # Check first member details
        p1 = results[0]
        assert p1.ClassProfession == "Orc"
        assert p1.Level == 40
        assert p1.Status == "B"
        assert p1.Name == "Earthquack"
        assert p1.Hp == "227/ 394"

        # Check second member details
        p2 = results[1]
        assert p2.ClassProfession == "Kenku"
        assert p2.Name == "Big"

    def test_parse_single_line_update(self):
        """
        Tests parsing a single line, which is how the session often processes data.
        """
        line = "[Kenku          58]  B        Quacamole            360/ 510 ( 70%)    479/ 510 ( 93%)     37/  69 ( 53%)  "
        results = parse_group_status(line)

        assert len(results) == 1
        assert results[0].Status == "B"
        assert results[0].Name == "Quacamole"
    
    @pytest.mark.parametrize("input,expected", argvalues= [
                                        ("[Sin         74] B       Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", "B"),
                                        ("[Sin         74] P       Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", "P"),
                                        ("[Sin         74] D       Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", "D"),
                                        ("[Sin         74] S       Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", "S"),
                                        ], ids=[
                                            "Bleed",
                                            "Poison",
                                            "Disease",
                                            "Stun"
                                        ]
    )
    def test_individual_status_flags(self, input, expected):
        results = parse_group_status(input)
        actual = results[0].Status

        assert actual == expected

    def test_ignores_headers_and_noise(self):
        """
        Ensures table headers don't crash the parser or create fake members.
        """
        line = "[ Class         Lvl] Status      Name                 Hits                Fat                Power"
        results = parse_group_status(line)
        assert len(results) == 0

    @pytest.mark.parametrize("input,expected", argvalues=[
                                        ("[Sin         74] B P     Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", StatusIndicator.BLEED | StatusIndicator.POISON),
                                        ("[Sin         74] B D     Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", StatusIndicator.BLEED | StatusIndicator.DISEASE),
                                        ("[Sin         74] B S     Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", StatusIndicator.BLEED | StatusIndicator.STUN),
                                        ("[Sin         74] P D     Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", StatusIndicator.POISON | StatusIndicator.DISEASE),
                                        ("[Sin         74] P S     Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", StatusIndicator.POISON | StatusIndicator.STUN),
                                        ("[Sin         74] D S     Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", StatusIndicator.DISEASE | StatusIndicator.STUN),
                                        ("[Sin         74] B P D   Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.DISEASE),
                                        ("[Sin         74] B P S   Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.STUN),
                                        ("[Sin         74] B D S   Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", StatusIndicator.BLEED | StatusIndicator.DISEASE | StatusIndicator.STUN),
                                        ("[Sin         74] P D S   Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", StatusIndicator.POISON | StatusIndicator.DISEASE | StatusIndicator.STUN),
                                        ("[Sin         74] B P D S Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.DISEASE | StatusIndicator.STUN)
                                        ], ids=[
                                            "Bleed + Poison",
                                            "Bleed + Disease",
                                            "Bleed + Stun",
                                            "Poison + Disease",
                                            "Poison + Stun",
                                            "Disease + Stun",
                                            "Bleed + Poison + Disease",
                                            "Bleed + Poison + Stun",
                                            "Bleed + Disease + Stun",
                                            "Poison + Disease + Stun",
                                            "Bleed + Poison + Disease + Stun"
                                        ]
                                    )
    def test_multiple_status_flags(self, input, expected: StatusIndicator):        
        actual = parse_group_status(input)[0].Status

        assert actual == expected


    @pytest.mark.parametrize("input,expected", argvalues=[
                                                ("NewFollower follows you", "NewFollower"),
                                                ("A vapor-shrouded mistwolf follows you", "A vapor-shrouded mistwolf")
                                                ],
                                                ids=[
                                                "Non-Disguised_Non-Shapeshifted_Follower", 
                                                "Disguised-Follower"
                                                ]
    )
    def test_new_follower_results_in_new_group_member(self, input, expected):
        results = parse_group_status(input)

        assert len(results) == 1
        assert results[0].Name == expected

    
    def test_existingGroupFollowedByNewMember_IndicatesNewMemberWithoutUpdatesToExpected(self):
        raw_input = """Beautiful's group:
[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Sin            69]           Foo                  100/ 500 (100%)    474/ 500 ( 94%)    638/ 707 ( 90%)  
[Skeleton       15]           Bar                  200/ 500 (100%)    300/ 500 ( 94%)    400/ 707 ( 90%)  

A vapor-shrouded mistwolf follows you"""

        matches = parse_group_status(raw_input) #  pattern.findall(raw_input)

        assert len(matches) == 3

    @pytest.mark.parametrize("includePets,expectedCount", [
        (False, 1),
        (True, 2)
    ])
    def test_include_pets_in_group_parse(self, includePets: bool, expectedCount: int):
        raw_input = """Beautiful's group:

[ Class      Lv] Status   Name              Hits            Fat             Power         
[Sin         74]         Beautiful        500/500 (100%)  500/500 (100%)  556/731 ( 76%)  

[mob         72]         angel of death   445/445 (100%)  445/445 (100%)  547/547 (100%)  """

        groupMembers = parse_group_status(raw_input, includePets=includePets)

        assert len(groupMembers) == expectedCount

    def test_InputPrefixedWithCharstateBeforeInput_IgnoresCharstateAndCorrectlyParsesMember(self):
        raw_input = r'���charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}��\x009\x00\x00\x00\x00\\2\x00\x00\x00\x00���charvitals {"hp":500,"maxhp":500,"mana":436,"maxmana":731,"moves":500,"maxmoves":500,"poisoned":false,"bleeding":false,"diseased":false,"stunned":false}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}���,\x00\x00\x00\x00���comm.channel {"chan":"say","msg":"You say \'follow again\'","player":"Beautiful"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charvitals {"hp":500,"maxhp":500,"mana":438,"maxmana":731,"moves":500,"maxmoves":500,"poisoned":false,"bleeding":false,"diseased":false,"stunned":false}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}��AnonymizedName follows you'
        
        matches = parse_group_status(raw_input)

        assert len(matches) == 1
        assert matches[0].Name == 'AnonymizedName'

class TestLeavingGroupParser:
    @pytest.mark.parametrize('input,expected', [
                                                ('foo disbands from your group', 'foo'),
                                                ('Foo disbands from your group', 'Foo'),
                                                ('FOO DISBANDS FROM YOUR GROUP', 'FOO')
                                                ],
                                                ids=[
                                                    'Lowercase input',
                                                    'Mixedcase input',
                                                    'Uppercase input',
                                                ])
    def test_GroupedMemberDisbands_IsCorrectlyParsed(self, input, expected):
        leaver = parse_leaveGroup(input)
        nameOfLeaver = leaver[0]

        assert len(leaver) == 1
        assert nameOfLeaver == expected
    
    @pytest.mark.parametrize('input,expected', [
                                                ('foo disbands from the group', 'foo'),
                                                ('foo disbands from your group', 'foo'),
                                                ],
                                                ids=[
                                                    'Party you are PART-OF',
                                                    'Party you are LEADING'
                                                    ])
    def test_WhetherMemberOfAPartyOrLeader_IsCorrectlyParsed(self, input, expected):
        leaver = parse_leaveGroup(input)
        nameOfLeaver = leaver[0]

        assert len(leaver) == 1
        assert nameOfLeaver == expected


    @pytest.mark.parametrize('input,expected', [
                                                ('An angel of death disbands from your group', 'An angel of death'),
                                                ('A hand of justice disbands from your group.', 'A hand of justice'),
                                                ],
    )
    def test_GroupedPetMember_DiesWhichIsConsideredLeaving_IsCorrectlyParsed(self, input, expected):
        leavers = parse_leaveGroup(input)
        nameOfLeaver = leavers[0]
        
        assert len(leavers) == 1
        assert nameOfLeaver == expected
    

    def test_InputTextPrefixedWithCharstateBeforeInput_IgnoresCharstateAndCorrectlyParsesLeaver(self):
        leavers = parse_leaveGroup(r'{"combat":"NORMAL","currentWeight":126,"maxWeight":438,"pos":"Standing"}��%U\x00\x00\x00\x00An angel of death disbands from your group.')
        nameOfLeaver = leavers[0]

        assert len(leavers) == 1
        assert nameOfLeaver == 'An angel of death'

    def test_ShapeshiftedMemberLeaves_IsCorrectlyParsed(self):
        leavers = parse_leaveGroup('A vapor-shrouded mistwolf disbands from your group.')
        nameOfLeaver = leavers[0]

        assert len(leavers) == 1
        assert nameOfLeaver == 'A vapor-shrouded mistwolf'


class TestStatusIndicator:
    @pytest.mark.parametrize("statusIndicator,stringRepresentation", argvalues=[
                                                                    (StatusIndicator.BLEED, "B"),
                                                                    (StatusIndicator.POISON, "P"),
                                                                    (StatusIndicator.DISEASE, "D"),
                                                                    (StatusIndicator.STUN, "S"),
                                                                    (StatusIndicator.BLEED | StatusIndicator.POISON, "BP"),
                                                                    (StatusIndicator.BLEED | StatusIndicator.DISEASE, "BD"),
                                                                    (StatusIndicator.BLEED | StatusIndicator.STUN, "BS"),
                                                                    (StatusIndicator.POISON | StatusIndicator.DISEASE, "PD"),
                                                                    (StatusIndicator.POISON | StatusIndicator.STUN, "PS"),
                                                                    (StatusIndicator.DISEASE | StatusIndicator.STUN, "DS"),
                                                                    (StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.DISEASE, "BPD"),
                                                                    (StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.STUN, "BPS"),
                                                                    (StatusIndicator.BLEED | StatusIndicator.DISEASE | StatusIndicator.STUN, "BDS"),
                                                                    (StatusIndicator.POISON | StatusIndicator.DISEASE | StatusIndicator.STUN, "PDS"),
                                                                    (StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.DISEASE | StatusIndicator.STUN, "BPDS")
                                                                    ]
    )
    def test_CompareStatusIndicators_AgainstTheirStringRepresentation(self, statusIndicator, stringRepresentation):
        assert statusIndicator == stringRepresentation
    
    def test_Against_None_NotEqualPasses(self):
        statusIndicator = StatusIndicator.BLEED
        assert statusIndicator != None
    
    def test_Against_None_EqualPasses(self):
        statusIndicator = StatusIndicator.BLEED
        assert not statusIndicator == None
    
    def test_NoStatusAilment(self):
        assert '' == StatusIndicator(0)
    
    @pytest.mark.parametrize("stringRepresentation,expectedStatusIndicator", argvalues=[
                                                                            ("B", StatusIndicator.BLEED),
                                                                            ("P", StatusIndicator.POISON),
                                                                            ("D", StatusIndicator.DISEASE),
                                                                            ("S", StatusIndicator.STUN),
                                                                            ("BP", StatusIndicator.BLEED | StatusIndicator.POISON),
                                                                            ("BD", StatusIndicator.BLEED | StatusIndicator.DISEASE),
                                                                            ("BS", StatusIndicator.BLEED | StatusIndicator.STUN),
                                                                            ("PD", StatusIndicator.POISON | StatusIndicator.DISEASE),
                                                                            ("PS", StatusIndicator.POISON | StatusIndicator.STUN),
                                                                            ("DS", StatusIndicator.DISEASE | StatusIndicator.STUN),
                                                                            ("BPD", StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.DISEASE),
                                                                            ("BPS", StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.STUN),
                                                                            ("BDS", StatusIndicator.BLEED | StatusIndicator.DISEASE | StatusIndicator.STUN),
                                                                            ("PDS", StatusIndicator.POISON | StatusIndicator.DISEASE | StatusIndicator.STUN),
                                                                            ("BPDS", StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.DISEASE | StatusIndicator.STUN)
                                                                            ]
    )
    def test_CreateStatusIndicatorFromString(self, stringRepresentation, expectedStatusIndicator: StatusIndicator):
        statusIndicator: StatusIndicator = StatusIndicator.FromString(stringRepresentation)

        assert statusIndicator == expectedStatusIndicator

class TestCharacter:
    def test_CharacterInitialization(self):
        c = Character(classProfession="Sin", 
                         level=1, 
                         status=StatusIndicator(0), 
                         name="Beautiful", 
                         hp=ResourceBar(2, 3), 
                         fat=ResourceBar(4, 5), 
                         pow=ResourceBar(6, 7))

        assert c.ClassProfession == "Sin"
        assert c.Level == 1
        assert c.Status == StatusIndicator(0)
        assert c.Name == "Beautiful"
        assert c.Hp == '2/3'
        assert c.Fat == '4/5'
        assert c.Pow == '6/7'

    @pytest.mark.parametrize("statusAilments,expected", argvalues=[
                                                                (StatusIndicator.BLEED | StatusIndicator.POISON, StatusIndicator.BLEED | StatusIndicator.POISON),
                                                                (StatusIndicator.BLEED | StatusIndicator.DISEASE, StatusIndicator.BLEED | StatusIndicator.DISEASE),
                                                                (StatusIndicator.BLEED | StatusIndicator.STUN, StatusIndicator.BLEED | StatusIndicator.STUN),
                                                                (StatusIndicator.POISON | StatusIndicator.DISEASE, StatusIndicator.POISON | StatusIndicator.DISEASE),
                                                                (StatusIndicator.POISON | StatusIndicator.STUN, StatusIndicator.POISON | StatusIndicator.STUN),
                                                                (StatusIndicator.DISEASE | StatusIndicator.STUN, StatusIndicator.DISEASE | StatusIndicator.STUN),
                                                                (StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.DISEASE, StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.DISEASE),
                                                                (StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.STUN, StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.STUN),
                                                                (StatusIndicator.BLEED | StatusIndicator.DISEASE | StatusIndicator.STUN, StatusIndicator.BLEED | StatusIndicator.DISEASE | StatusIndicator.STUN),
                                                                (StatusIndicator.POISON | StatusIndicator.DISEASE | StatusIndicator.STUN, StatusIndicator.POISON | StatusIndicator.DISEASE | StatusIndicator.STUN),
                                                                (StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.DISEASE | StatusIndicator.STUN, StatusIndicator.BLEED | StatusIndicator.POISON | StatusIndicator.DISEASE | StatusIndicator.STUN)
                                                                ],
                                                                ids=[
                                                                    "BP",
                                                                    "BD",
                                                                    "BS",
                                                                    "PD",
                                                                    "PS",
                                                                    "DS",
                                                                    "BPD",
                                                                    "BPS",
                                                                    "BDS",
                                                                    "PDS",
                                                                    "BPDS"
                                                                ]
    )
    def test_MultipleStatusAilments(self, statusAilments: StatusIndicator, expected: StatusIndicator):
        char = Character("Foo", 
                         "Skeleton", 
                         1, 
                         statusAilments, 
                         ResourceBar(2, 3), 
                         ResourceBar(4, 5), 
                         ResourceBar(6, 7))

        assert char.Status == expected
        
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

class TestResourceBar:

    def test_Initialization(self):
        rb = ResourceBar(current=50, maximum=100)
        assert rb.Current == 50
        assert rb.Maximum == 100
    
    def test_MakingIntoString(self):
        rb = ResourceBar(current=75, maximum=150)
        assert str(rb) == "75/150"

    def test_Equality_SameValues_FromDifferentInstances_Passes(self):
        rb1 = ResourceBar(current=30, maximum=60)
        rb2 = ResourceBar(current=30, maximum=60)

        assert rb1 == rb2
    
    def test_Inequality_DifferentValues_FromDifferentInstances_Fails(self):
        rb1 = ResourceBar(current=30, maximum=61)
        rb2 = ResourceBar(current=31, maximum=60)

        assert rb1 != rb2
    
    @pytest.mark.parametrize("input,expected", argvalues=[
                                                ("75/150", ResourceBar(75, 150)),
                                                ("75/ 150", ResourceBar(75, 150))
                                                ], 
                                                ids=[
                                                    "NoSpaceBeforeMaximum",
                                                    "WithSpacesBeforeMaximum"
                                                    ]
    )
    def test_Initialization_FromString(self, input: str, expected: ResourceBar):
        rb = ResourceBar.FromString(input)

        assert rb == expected
    
    @pytest.mark.parametrize("input,stringRepresentation", argvalues=[
                                                            (ResourceBar(100, 100), "100/100"),
                                                            (ResourceBar(100, 100), "100/ 100")
                                                            ],
                                                            ids=[
                                                                "NoSpaceBeforeMaximum",
                                                                "WithSpaceBeforeMaximum"
                                                            ]
    )
    def test_Equality_ResourceBarAndStringRepresentation(self, input: ResourceBar, stringRepresentation: str):
        assert input == stringRepresentation
