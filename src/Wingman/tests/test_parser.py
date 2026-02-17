import pytest
from typing import Callable, List
from pathlib import Path
import sys
if __name__ == "__main__":
    srcDirectory = Path(__file__).parent.parent.parent.resolve()
    sys.path.append(str(srcDirectory))


from Wingman.core.parser import MobMovement, Parser
from Wingman.core.status_indicator import StatusIndicator
from Wingman.core.group import Group
from Wingman.core.character import Character



@pytest.fixture
def parser():
    return Parser()

class TestXpParser:
    def test_parse_compound_xp(self, parser):
        log_line = "You gain 17325 (+43312) experience points."
        assert parser.parse_xp_message(log_line) == 60637

    def test_parse_simple_xp(self, parser):
        log_line = "You gain 150 experience points."
        assert parser.parse_xp_message(log_line) == 150

    def test_ignore_irrelevant_lines(self, parser):
        log_line = "You hit the dragon for 150 damage."
        assert parser.parse_xp_message(log_line) == 0

    def test_parse_strange_formatting(self, parser):
        log_line = "   You gain    10 (+5)    experience points.   "
        assert parser.parse_xp_message(log_line) == 15


@pytest.fixture
def groupParser():
    return Parser().parse_group_status

class TestGroupParser:

    def test_parse_valid_group_block(self, groupParser: Callable[[str], List[Character]]):
        """
        Tests that we can extract multiple members from a raw text block.
        """
        # This simulates a raw chunk from the game
        raw_block = """
        [ Class         Lvl] Status      Name                 Hits                Fat                Power
        [Orc            40]  B        Earthquack           227/ 394 ( 57%)     354/ 394 ( 89%)     326/ 326 (100%)
        [Kenku          70]           Big                  550/ 550 (100%)     538/ 550 ( 97%)      63/  73 ( 86%)
        """

        results = groupParser(raw_block)

        assert len(results) == 2

        # Check first member details
        p1 = results[0]
        assert p1.Class_ == "Orc"
        assert p1.Level == 40
        assert p1.Status == "B"
        assert p1.Name == "Earthquack"
        assert p1.Hp == "227/ 394"

        # Check second member details
        p2 = results[1]
        assert p2.Class_ == "Kenku"
        assert p2.Name == "Big"

    def test_parse_single_line_update(self, groupParser: Callable[[str], List[Character]]):
        """
        Tests parsing a single line, which is how the session often processes data.
        """
        line = "[Kenku          58]  B        Quacamole            360/ 510 ( 70%)    479/ 510 ( 93%)     37/  69 ( 53%)  "
        results = groupParser(line)

        assert len(results) == 1
        assert results[0].Status == "B"
        assert results[0].Name == "Quacamole"

    @pytest.mark.parametrize("input, expected", argvalues= [
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
    def test_individual_status_flags(self, input, expected, groupParser: Callable[[str], List[Character]]):
        results = groupParser(input)
        actual = results[0].Status

        assert actual == expected

    def test_ignores_headers_and_noise(self, groupParser: Callable[[str], List[Character]]):
        """
        Ensures table headers don't crash the parser or create fake members.
        """
        line = "[ Class         Lvl] Status      Name                 Hits                Fat                Power"
        results = groupParser(line)
        assert len(results) == 0

    @pytest.mark.parametrize("input, expected", argvalues=[
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
    def test_multiple_status_flags(self, input, expected: StatusIndicator, groupParser: Callable[[str], List[Character]]):
        actual = groupParser(input)[0].Status

        assert actual == expected


    @pytest.mark.parametrize("input, expected", argvalues=[
                                                ("NewFollower follows you", "NewFollower"),
                                                ("A vapor-shrouded mistwolf follows you", "A vapor-shrouded mistwolf")
                                                ],
                                                ids=[
                                                "Non-Disguised_Non-Shapeshifted_Follower",
                                                "Disguised-Follower"
                                                ]
    )
    def test_new_follower_results_in_new_group_member(self, input, expected, groupParser: Callable[[str], List[Character]]):
        results = groupParser(input)

        assert len(results) == 1
        assert results[0].Name == expected


    def test_existingGroupFollowedByNewMember_IndicatesNewMemberWithoutUpdatesToExpected(self, groupParser: Callable[[str], List[Character]]):
        raw_input = """Beautiful's group:
[ Class        Lvl] Status     Name                 Hits               Fat                Power
[Sin            69]           Foo                  100/ 500 (100%)    474/ 500 ( 94%)    638/ 707 ( 90%)
[Skeleton       15]           Bar                  200/ 500 (100%)    300/ 500 ( 94%)    400/ 707 ( 90%)

A vapor-shrouded mistwolf follows you"""

        matches = groupParser(raw_input) #  pattern.findall(raw_input)

        assert len(matches) == 3

    @pytest.mark.parametrize("includePets, expectedCount", [
        (False, 1),
        (True, 2)
    ])
    def test_include_pets_in_group_parse(self, includePets: bool, expectedCount: int, groupParser: Callable[[str], List[Character]]):
        raw_input = """Beautiful's group:

[ Class      Lv] Status   Name              Hits            Fat             Power
[Sin         74]         Beautiful        500/500 (100%)  500/500 (100%)  556/731 ( 76%)

[mob         72]         angel of death   445/445 (100%)  445/445 (100%)  547/547 (100%)  """

        groupMembers = groupParser(raw_input, includePets=includePets)

        assert len(groupMembers) == expectedCount

    def test_InputPrefixedWithCharstateBeforeInput_IgnoresCharstateAndCorrectlyParsesMember(self, groupParser: Callable[[str], List[Character]]):
        raw_input = r'���charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}��\x009\x00\x00\x00\x00\\2\x00\x00\x00\x00���charvitals {"hp":500,"maxhp":500,"mana":436,"maxmana":731,"moves":500,"maxmoves":500,"poisoned":false,"bleeding":false,"diseased":false,"stunned":false}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}���,\x00\x00\x00\x00���comm.channel {"chan":"say","msg":"You say \'follow again\'","player":"Beautiful"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charvitals {"hp":500,"maxhp":500,"mana":438,"maxmana":731,"moves":500,"maxmoves":500,"poisoned":false,"bleeding":false,"diseased":false,"stunned":false}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}��AnonymizedName follows you'

        matches = groupParser(raw_input)

        assert len(matches) == 1
        assert matches[0].Name == 'AnonymizedName'

class TestLeavingGroupParser:
    @pytest.fixture
    def leaveGroupParser(self):
        return Parser().parse_leaveGroup

    @pytest.mark.parametrize('input, expected', [
                                                ('foo disbands from your group', 'foo'),
                                                ('Foo disbands from your group', 'Foo'),
                                                ('FOO DISBANDS FROM YOUR GROUP', 'FOO')
                                                ],
                                                ids=[
                                                    'Lowercase input',
                                                    'Mixedcase input',
                                                    'Uppercase input',
                                                ])
    def test_GroupedMemberDisbands_IsCorrectlyParsed(self, input, expected, leaveGroupParser):
        leaver = leaveGroupParser(input)
        nameOfLeaver = leaver[0]

        assert len(leaver) == 1
        assert nameOfLeaver == expected

    @pytest.mark.parametrize('input, expected', [
                                                ('foo disbands from the group', 'foo'),
                                                ('foo disbands from your group', 'foo'),
                                                ],
                                                ids=[
                                                    'Party you are PART-OF',
                                                    'Party you are LEADING'
                                                    ])
    def test_WhetherMemberOfAPartyOrLeader_IsCorrectlyParsed(self, input, expected, leaveGroupParser):
        leaver = leaveGroupParser(input)
        nameOfLeaver = leaver[0]

        assert len(leaver) == 1
        assert nameOfLeaver == expected


    @pytest.mark.parametrize('input, expected', [
                                                ('An angel of death disbands from your group', 'angel of death'),
                                                ('A hand of justice disbands from your group.', 'hand of justice'),
                                                ],
    )
    def test_GroupedPetMember_DiesWhichIsConsideredLeaving_IsCorrectlyParsed(self, input, expected, leaveGroupParser):
        leavers = leaveGroupParser(input)
        nameOfLeaver = leavers[0]

        assert len(leavers) == 1
        assert nameOfLeaver == expected


    def test_InputTextPrefixedWithCharstateBeforeInput_IgnoresCharstateAndCorrectlyParsesLeaver(self, leaveGroupParser):
        leavers = leaveGroupParser(r'{"combat":"NORMAL","currentWeight":126,"maxWeight":438,"pos":"Standing"}%U\x00\x00\x00\x00An angel of death disbands from your group.')
        nameOfLeaver = leavers[0]

        assert len(leavers) == 1
        assert nameOfLeaver == 'angel of death'

    def test_ShapeshiftedMemberLeaves_IsCorrectlyParsed(self, leaveGroupParser):
        leavers = leaveGroupParser('A vapor-shrouded mistwolf disbands from your group.')
        nameOfLeaver = leavers[0]

        assert len(leavers) == 1
        assert nameOfLeaver == 'vapor-shrouded mistwolf'

class TestPartyDisbands:
    def test_NonPartyRelatedText_ReturnsFalse(self):
        actual = Parser().parse_has_group_leader_disbanded_party("You move east", Group())

        assert actual == False

    def test_YourLeaderDisbandsParty_ReturnsTrue(self):
        cLead = Character("Foo", 'Skeleton')
        cFollower = Character('Bar', 'Zombie')
        g = Group([cLead, cFollower])
        actual = Parser().parse_has_group_leader_disbanded_party("Foo disbanded their group.", g)

        assert actual
    
    def test_NonLeaderParty_ReturnsFalse(self): #Recently disbanded and no `group` command executed, hence empty group
        actual = Parser().parse_has_group_leader_disbanded_party("Bar disbanded their group.", Group())
    
        assert actual == False
    
    def test_OtherPartyLeaderDisbands_ReturnsFalse(self):
        yourLead = Character("You", "Sin")
        yourFollower = Character("Pet", "mob")
        yourGroup = Group([yourLead, yourFollower])

        actual = Parser().parse_has_group_leader_disbanded_party("Foo disbanded their group.", yourGroup)

        assert actual == False

class TestAfkParser:
    def test_SentAfkLine_ReturnsTrue(self):
        actual = Parser().parseAfkStatus("You are now listed as AFK.")
        
        assert actual
    
    def test_SentAfkReturnLine_ReturnsFalse(self):
        actual = Parser().parseAfkStatus("You are no longer AFK.")
        
        assert actual == False

    def test_SentNonAfkRelatedLine_ReturnsNone(self):
        actual = Parser().parseAfkStatus("Anything not related to being AFK.")
        
        assert actual is None

class TestMeditationParse:
    def test_StartedMeditating_ReturnsTrue(self):
        isMeditating = Parser().parseMeditation(Parser.Meditation.Begin.value)

        assert isMeditating
    
    def test_EndedMeditatingVoluntarily_ReturnsFalse(self):
        isMeditating = Parser().parseMeditation(Parser.Meditation.Termination_Voluntary.value)

        assert isMeditating == False
    
    def test_EndedMeditationNonVoluntarily_ReturnsFalse(self):
        isMeditating = Parser().parseMeditation(Parser.Meditation.Termination_NonVoluntary.value)

        assert isMeditating == False
    
    def test_NonMeditationRelatedLine_CurrentlyMeditating_ReturnsNone(self):
        isMeditating = Parser().parseMeditation("Some other line unrelated to meditation.")

        assert isMeditating == None
    
    def test_NonMeditationRelatedLine_NotCurrentlyMeditating_ReturnsNone(self):
        isMeditating = Parser().parseMeditation("Some other line unrelated to meditation.")

        assert isMeditating == None

class TestHidingParse:
    def test_StartHiding_ReturnsTrue(self):
        actual = Parser().parseHideStatus(Parser.HideStatus.Begin.value)

        assert actual
    
    def test_EndHiding_ReturnsFalse(self):
        actual = Parser().parseHideStatus(Parser.HideStatus.EndHiding.value)

        assert actual == False
    
    def test_NonHidingRelatedLine_ReturnsNone(self):
        actual = Parser().parseHideStatus("Some line unrelated to hiding.")

        assert actual is None

class TestMobParse:
    def test_SingleMob_ReturnsMob(self):
        expected = ["a mithril dealer"]
        text = "\x1b[1;30m\x1b[1;30m\n\nAlso there is \x1b[1;31ma mithril dealer\x1b[1;30m\x1b[1;30m\x1b[1;30m.\n\n\n\x1b[8m"
        
        actual = Parser().ParseMobs().parsePreAnsiScrubbingForMobs(text)

        assert expected == actual
    
    def test_OrderOfMobs_RemainsUnchanged(self):
        expected = ["Foo", "Bar", "Bazz"]
        text = "\x1b[1;30m\x1b[1;30m\n\nAlso there is \x1b[1;31mFoo\x1b[1;30m\x1b[0;37m,\x1b[0;0m\x1b[1;30m \x1b[1;30m\x1b[1;30m\x1b[1;31mBar\x1b[1;30m\x1b[0;37m,\x1b[0;0m\x1b[1;30m \x1b[1;30mand\x1b[0;0m\x1b[1;30m \x1b[1;30m\x1b[1;30m\x1b[1;31mBazz\x1b[1;30m\x1b[1;30m\x1b[1;30m.\n\n\n\x1b[8m"

        actual = Parser().ParseMobs().parsePreAnsiScrubbingForMobs(text)

        assert expected == actual
    
    def test_NonMobRelatedText_ReturnsEmptyList(self):
        text = "This is a line of text with no mobs present."
        expected = []

        actual = Parser().ParseMobs().parsePreAnsiScrubbingForMobs(text)

        assert expected == actual

    def test_MobText_ButItIsAGreenMob_ReturnsEmptyList(self):
        text = "\x1b[1;30m\x1b[1;30m\n\nAlso there is \x1b[1;31m\x1b[1;32mGreenMob\x1b[0;0m\x1b[1;31m\x1b[1;30m\x1b[1;30m\x1b[1;30m.\n\n\n\x1b[8m"
        expected = []

        actual = Parser().ParseMobs().parsePreAnsiScrubbingForMobs(text)

        assert expected == actual

    def test_PredeterminedChunk_GreenMobShouldNotCreateAPredeterminedChunk(self):
        text = "\x1b[1;30m\x1b[1;30m\n\nAlso there is \x1b[1;31m\x1b[1;32mGreenMob\x1b[0;0m\x1b[1;31m\x1b[1;30m\x1b[1;30m\x1b[1;30m.\n\n\n\x1b[8m"
        outList = ['any values will be cleared']

        actual = Parser().ParseMobs().hasAnsiColorCodedMobs(text, outList)

        assert actual == False
        assert outList == []

    def test_PredeterminedChunk_StandardMobsShouldCreateAPredeterminedChunk(self):
        text = "\x1b[1;30m\x1b[1;30m\n\nAlso there is \x1b[1;31ma mithril dealer\x1b[1;30m\x1b[1;30m\x1b[1;30m.\n\n\n\x1b[8m"
        list = []

        actual = Parser().ParseMobs().hasAnsiColorCodedMobs(text, list)

        assert actual
        assert list == ["a mithril dealer"]

    @pytest.mark.parametrize("text", ["A Kaidite zombie general dies!",
                                      "a Kaidite zombie general dies!"],
                                      ids=["Indefinite article capitalized",
                                           "Indefinite article lowercase"])
    def test_MobRelatedMovement_LeavingBy_Death_UnaffectedByIndefiniteArticleCasing(self, text):
        mobsInRoom = ['a Kaidite zombie general', 'a Kaidite lady']

        actual = Parser().ParseMovement().mobRelatedMovement(text, mobsInRoom)

        assert actual == (True, MobMovement.LEAVING, 'a Kaidite zombie general')
    
    def test_MobRelatedMovement_LeavingBy_RoomMovement(self):
        text = "A windfang hatchling leaves West"
        mobsInRoom = ['a razor-backed windfang', 'a windfang hatchling', 'a guardian of the nameless']

        actual = Parser().ParseMovement().mobRelatedMovement(text, mobsInRoom)

        assert actual == (True, MobMovement.LEAVING, 'a windfang hatchling')
    
    def test_MobRelatedMovement_LeavingBy_Chasing(self):
        text = 'A windfang hatchling chases Foo out of the room.'
        mobsInRoom = ['a windfang hatchling']

        actual = Parser().ParseMovement().mobRelatedMovement(text, mobsInRoom)

        assert actual == (True, MobMovement.LEAVING, 'a windfang hatchling')

    def test_MobRelatedMovement_EnteringBy_RoomMovement(self):
        text = 'A windfang hatchling arrives from the north.'
        mobsInRoom = ['a windfang hatchling']

        actual = Parser().ParseMovement().mobRelatedMovement(text, mobsInRoom)

        assert actual == (True, MobMovement.ENTERING, 'a windfang hatchling')

    def test_MobRelatedMovement_EnteringBy_SpawningInRoom(self):
        text = 'A mermaid temptress enters the room.'
        mobsInRoom = ['a mermaid temptress']

        actual = Parser().ParseMovement().mobRelatedMovement(text, mobsInRoom)

        assert actual == (True, MobMovement.ENTERING, 'a mermaid temptress')

    def test_MobRelatedMovement_EnteringBy_ChasingIntoRoom(self):
        text = 'A windfang hatchling chases Foo into the room.'
        mobsInRoom = ['a windfang hatchling']

        actual = Parser().ParseMovement().mobRelatedMovement(text, mobsInRoom)

        assert actual == (True, MobMovement.ENTERING, 'a windfang hatchling')

class TestBuffOrShieldEndingParse:
    @pytest.mark.parametrize("enumMember", [Parser.ParseBuffOrShieldText.Shield_Ended,
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
                                            Parser.ParseBuffOrShieldText.Vitalize_Ended,
                                            ],
                                        ids=["Shield Ends",
                                            "Blur Ends",
                                            "Protect Ends",
                                            "Tough Skin Ends",
                                            "Chaos - Bleed Resist Ends",
                                            "Chaos - Chaos Fortitude Ends",
                                            "Chaos - Combat Ends",
                                            "Chaos - Disease Resist Ends",
                                            "Chaos - Poison Resist Ends",
                                            "Good - Bless Ends",
                                            "Evil - Regenerate Ends",
                                            "Evil - Vitalize Ends"
                                        ])
    def test_BuffOrShieldTextEndingOnly_ReturnsTrue(self, enumMember: Parser.ParseBuffOrShieldText):
        isBuffOrShieldRefreshing, whatEnded = Parser().parseBuffOrShieldIsRefreshing(enumMember.value)

        assert isBuffOrShieldRefreshing == False
        assert whatEnded is not None
        assert whatEnded == enumMember

    @pytest.mark.parametrize("text", [Parser.ParseBuffOrShieldText.Shield_Ended.value + "\n" + Parser.ParseBuffOrShieldText.ShieldStarts.value,
                                        Parser.ParseBuffOrShieldText.Blur_Ended.value + "\n" + Parser.ParseBuffOrShieldText.BlurStarts.value,
                                        Parser.ParseBuffOrShieldText.Protect_Ended.value + "\n" + Parser.ParseBuffOrShieldText.ProtectStarts.value,
                                        Parser.ParseBuffOrShieldText.ToughDotSkin_Ended.value + "\n" + Parser.ParseBuffOrShieldText.ToughDotSkinStarts.value,
                                        #Chaos
                                        Parser.ParseBuffOrShieldText.BleedDotResist_Ended.value + "\n" + Parser.ParseBuffOrShieldText.BleedDotResistStarts.value,
                                        Parser.ParseBuffOrShieldText.ChaosDotFortitude_Ended.value + "\n" + Parser.ParseBuffOrShieldText.ChaosDotFortitudeStarts.value,
                                        Parser.ParseBuffOrShieldText.Combat_Ended.value + "\n" + Parser.ParseBuffOrShieldText.CombatStarts.value,
                                        Parser.ParseBuffOrShieldText.DiseaseDotResist_Ended.value + "\n" + Parser.ParseBuffOrShieldText.DiseaseDotResistStarts.value,
                                        Parser.ParseBuffOrShieldText.PoisonDotResist_Ended.value + "\n" + Parser.ParseBuffOrShieldText.PoisonDotResistStarts.value,
                                        #Good
                                        Parser.ParseBuffOrShieldText.Bless_Ended.value + "\n" + Parser.ParseBuffOrShieldText.BlessStarts.value,
                                        #Evil
                                        Parser.ParseBuffOrShieldText.Regenerate_Ended.value + "\n" + Parser.ParseBuffOrShieldText.RegenerateStarts.value,
                                        Parser.ParseBuffOrShieldText.Vitalize_Ended.value + "\n" + Parser.ParseBuffOrShieldText.VitalizeStarts.value
                                    ],
                                    ids=["Shield Refresh",
                                        "Blur Refresh",
                                        "Protect Refresh",
                                        "Tough Skin Refresh",
                                        "Chaos - Bleed Resist Refresh",
                                        "Chaos - Chaos Fortitude Refresh",
                                        "Chaos - Combat Refresh",
                                        "Chaos - Disease Resist Refresh",
                                        "Chaos - Poison Resist Refresh",
                                        "Good - Bless Refresh",
                                        "Evil - Regenerate Refresh",
                                        "Evil - Vitalize Refresh"
                                        ])
    def test_BuffOrShieldRefreshedBySpell_EndingTextAndApplyingTextInSameInput_ReturnsFalse(self, text):
        isBuffOrShieldRefreshing, _ = Parser().parseBuffOrShieldIsRefreshing(text)

        assert isBuffOrShieldRefreshing

class TestSpellMitigationAffectParse:
    def test_SpellMitigationText_IndicatesSpell(self):
        isMitigatingText, mitigatingSpell = Parser().parseSpellMitigationAffect(Parser.ParseSpellMitigationAffect.BleedDotResist)

        assert isMitigatingText
        assert mitigatingSpell == Parser.ParseSpellMitigationAffect.BleedDotResist