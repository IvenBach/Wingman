import time

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
from Wingman.core.item import Item, ItemSlot
from Wingman.core.affect import Affect

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

        matches = groupParser(raw_input)

        assert len(matches) == 3

    @pytest.mark.parametrize("includePets, expectedCount", [
        (False, 1),
        (True, 2)
    ])
    def test_include_pets_in_group_parse(self, includePets: bool, expectedCount: int, groupParser: Callable[[str, bool], List[Character]]):
        raw_input = """Beautiful's group:

[ Class      Lv] Status   Name              Hits            Fat             Power
[Sin         74]         Beautiful        500/500 (100%)  500/500 (100%)  556/731 ( 76%)

[mob         72]         angel of death   445/445 (100%)  445/445 (100%)  547/547 (100%)  """

        groupMembers = groupParser(raw_input, includePets)

        assert len(groupMembers) == expectedCount

    def test_InputPrefixedWithCharstateBeforeInput_IgnoresCharstateAndCorrectlyParsesMember(self, groupParser: Callable[[str], List[Character]]):
        raw_input = r'���charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}��\x009\x00\x00\x00\x00\\2\x00\x00\x00\x00���charvitals {"hp":500,"maxhp":500,"mana":436,"maxmana":731,"moves":500,"maxmoves":500,"poisoned":false,"bleeding":false,"diseased":false,"stunned":false}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}���,\x00\x00\x00\x00���comm.channel {"chan":"say","msg":"You say \'follow again\'","player":"Beautiful"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charvitals {"hp":500,"maxhp":500,"mana":438,"maxmana":731,"moves":500,"maxmoves":500,"poisoned":false,"bleeding":false,"diseased":false,"stunned":false}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}�����charstate {"combat":"NORMAL","currentWeight":83,"maxWeight":250,"pos":"Standing"}��AnonymizedName follows you'

        matches = groupParser(raw_input)

        assert len(matches) == 1
        assert matches[0].Name == 'AnonymizedName'

    def test_DraggingCorpse_AddsToGroup(self):
        text = "You drag FooBar's corpse."
        chars = Parser().parse_group_status(text)

        assert len(chars) == 1
        assert chars[0].Name == "FooBar"

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
    def test_StartedMeditating(self):
        isMeditating, meditationState = Parser().parseMeditation(Parser.MeditationState.Begin.value)

        assert isMeditating
        assert meditationState == Parser.MeditationState.Begin
    
    def test_EndedMeditating_ByStandingUp(self):
        isMeditating, meditationState = Parser().parseMeditation(Parser.MeditationState.Termination_ByStanding.value)

        assert isMeditating == False
        assert meditationState == Parser.MeditationState.Termination_ByStanding
    
    def test_EndedMeditating_ByNotStandingUp_ExpectedFullPower(self):
        isMeditating, meditationState = Parser().parseMeditation(Parser.MeditationState.Termination_ByFullPower.value)

        assert isMeditating == False
        assert meditationState == Parser.MeditationState.Termination_ByFullPower

    def test_EndedMeditation_ByInterruption(self):
        isMeditating, meditationState = Parser().parseMeditation(Parser.MeditationState.Termination_ByInterruption.value)

        assert isMeditating == False
        assert meditationState == Parser.MeditationState.Termination_ByInterruption
    
    def test_NonMeditationRelatedLine_ReturnsNone(self):
        isMeditating, meditationState = Parser().parseMeditation("Some other line unrelated to meditation.")

        assert isMeditating == None
        assert meditationState == None

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

    def test_MobWithDashInName_IsCorrectlyParsed(self):
        text = "\x1b[1;30m\x1b[1;30m\n\nAlso there is \x1b[1;31ma brilliant bronze-scaled dragon\x1b[1;30m\x1b[1;30m\x1b[1;30m.\n\nAn angel of death follows Beautiful in.\n\n\x1b[8m"
        mobList: list[str] = []
        result = Parser().ParseMobs().hasAnsiColorCodedMobs(text, mobList)

        assert result
        assert mobList == ["a brilliant bronze-scaled dragon"]

    def test_MobWithCommaInName_IsCorrectlyParsed(self):
        text = "\x1b[1;30m\x1b[1;30m\n\nAlso there is \x1b[1;31ma disturbed, headless mummy corpse\x1b[1;30m\x1b[1;30m\x1b[1;30m.\n\nAn angel of death follows Beautiful in.\n\n\x1b[8m"
        mobList: list[str] = []
        result = Parser().ParseMobs().hasAnsiColorCodedMobs(text, mobList)

        assert result
        assert mobList == ["a disturbed, headless mummy corpse"]

    class TestMobRelatedMovement:
        @pytest.mark.parametrize("mobName, expectedName", [("A Kaidite zombie general", "a Kaidite zombie general"),
                                                           ("A brilliant bronze-scaled dragon", "a brilliant bronze-scaled dragon"),
                                                           ("A disturbed, headless mummy corpse", "a disturbed, headless mummy corpse")],
                                            ids=["Mob with [a-zA-Z] simple name",
                                                 "Mob with dash in name",
                                                 "Mob with comma in name"])
        def test_MobRelatedMovement_LeavingByDeath(self, mobName, expectedName):
            text = f"{mobName} dies!"
            mobsInRoom = [mobName, 'a Kaidite lady']

            isMobMovement, movementType, actualMobName = Parser().ParseMovement().mobRelatedMovement(text, mobsInRoom)

            assert isMobMovement == True
            assert movementType == MobMovement.LEAVING
            assert actualMobName == expectedName

        @pytest.mark.parametrize("text", ["A windfang hatchling dies!",
                                        "��X�\x00\x00\x00\x00Hc\x00\x00\x00\x00A windfang hatchling dies!"],
                                        ids=["Only mob text",
                                            "Prefixed with extraneous sequence"])
        def test_MobRelatedMovement_LeavingBy_RoomMovement(self, text):
            mobsInRoom = ['a razor-backed windfang', 'a windfang hatchling', 'a guardian of the nameless']

            isMobMovement, movementType, mobName = Parser().ParseMovement().mobRelatedMovement(text, mobsInRoom)

            assert isMobMovement == True
            assert movementType == MobMovement.LEAVING
            assert mobName == 'a windfang hatchling'

        def test_MobRelatedMovement_LeavingBy_Chasing(self):
            text = "A windfang hatchling chases Foo out of the room."
            mobsInRoom = ['a windfang hatchling']

            isMobMovement, movementType, mobName = Parser().ParseMovement().mobRelatedMovement(text, mobsInRoom)

            assert isMobMovement == True
            assert movementType == MobMovement.LEAVING
            assert mobName == 'a windfang hatchling'

        def test_MobRelatedMovement_EnteringBy_RoomMovement(self):
            text = 'A windfang hatchling arrives from the north.'
            mobsInRoom = ['a windfang hatchling']

            isMobMovement, movementType, mobName = Parser().ParseMovement().mobRelatedMovement(text, mobsInRoom)

            assert isMobMovement == True
            assert movementType == MobMovement.ENTERING
            assert mobName == 'a windfang hatchling'

        def test_MobRelatedMovement_EnteringBy_SpawningInRoom(self):
            text = 'A mermaid temptress enters the room.'
            mobsInRoom = ['a mermaid temptress']

            isMobMovement, movementType, mobName = Parser().ParseMovement().mobRelatedMovement(text, mobsInRoom)

            assert isMobMovement == True
            assert movementType == MobMovement.ENTERING
            assert mobName == 'a mermaid temptress'

        def test_MobRelatedMovement_EnteringBy_ChasingIntoRoom(self):
            text = 'A windfang hatchling chases Foo into the room.'
            mobsInRoom = ['a windfang hatchling']

            isMobMovement, movementType, mobName = Parser().ParseMovement().mobRelatedMovement(text, mobsInRoom)

            assert isMobMovement == True
            assert movementType == MobMovement.ENTERING
            assert mobName == 'a windfang hatchling'

        def test_PlayerMovement_EnteringBy_RoomMovement_NotConsideredMobRelatedMovement(self):
            text = 'Foo arrives from the north.'
            mobsInRoom = ['a windfang hatchling']

            isMobMovement, movementType, mobName = Parser().ParseMovement().mobRelatedMovement(text, mobsInRoom)

            assert isMobMovement == False
            assert movementType == None
            assert mobName == None

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
        isMitigatingText, mitigatingSpell = Parser().parseSpellMitigationAffect(Parser.SpellMitigationAffect.BleedDotResist)

        assert isMitigatingText
        assert mitigatingSpell == Parser.SpellMitigationAffect.BleedDotResist

class TestInventoryParse:
    def test_FullyEquippedItemSlots_PlacesThemIntoGearSlots(self):
        text = """Inventory:
  (w) A WISPWEAVE spellbinder's crown
  (w) A twisted gold torc
  (w) A mark of vigilance
  (w) A GLOWING worldwalker's cloak
  (w) A GOSSAMER noble's gleaming raiment of evasion
  (w) A GOSSAMER noble's gleaming gloves of intelligence
  (w) A GLOWING GOSSAMER hierophant's legwraps
  (w) A GLOWING WISPWEAVE dragon-wing boots
  (h) A GLOWING rod of endless repentance
  (h) Glowing Ahrimal's shielding scale

Inventory:   46 / 60
Encumbrance: 85 / 230"""

        inventory = Parser().parseInventory(text)
        assert inventory is not None
        assert inventory.EquippedGear_.Head.Name == "A WISPWEAVE spellbinder's crown"
        assert inventory.EquippedGear_.Jewel1.Name == "A twisted gold torc"
        assert inventory.EquippedGear_.Jewel2.Name == "A mark of vigilance"
        assert inventory.EquippedGear_.Cloak.Name == "A GLOWING worldwalker's cloak"
        assert inventory.EquippedGear_.Body.Name == "A GOSSAMER noble's gleaming raiment of evasion"
        assert inventory.EquippedGear_.Hands.Name == "A GOSSAMER noble's gleaming gloves of intelligence"
        assert inventory.EquippedGear_.Legs.Name == "A GLOWING GOSSAMER hierophant's legwraps"
        assert inventory.EquippedGear_.Feet.Name == "A GLOWING WISPWEAVE dragon-wing boots"
        assert inventory.EquippedGear_.Held_Right.Name == "A GLOWING rod of endless repentance"
        assert inventory.EquippedGear_.Held_Left.Name == "Glowing Ahrimal's shielding scale"

    def test_NoEquippedItems_PlacesThemIntoBackpack(self):
        text = """Inventory:
      A bright jeweled greatsword of the phoenix
 ( 4) A goblet of zombie blood
 (10) A bunch of restorative roots
 (11) A darkspawned blackened fish fillet
 ( 2) A ticket to Arnak's Plague
 ( 6) A scroll of minor resurrection
 ( 2) A scroll of lesser resurrection

Inventory:   xx / XX
Encumbrance: yy / YYY"""

        inventory = Parser().parseInventory(text)
        assert inventory is not None
        assert len(inventory.Backpack) == 7
        assert inventory.Backpack[0].Name == "A bright jeweled greatsword of the phoenix"
        assert inventory.Backpack[1].Name == "A goblet of zombie blood" and inventory.Backpack[1].Quantity == 4
        assert inventory.Backpack[2].Name == "A bunch of restorative roots" and inventory.Backpack[2].Quantity == 10
        assert inventory.Backpack[3].Name == "A darkspawned blackened fish fillet" and inventory.Backpack[3].Quantity == 11
        assert inventory.Backpack[4].Name == "A ticket to Arnak's Plague" and inventory.Backpack[4].Quantity == 2
        assert inventory.Backpack[5].Name == "A scroll of minor resurrection" and inventory.Backpack[5].Quantity == 6
        assert inventory.Backpack[6].Name == "A scroll of lesser resurrection" and inventory.Backpack[6].Quantity == 2

    def test_EquippedGearWithSomeEmptySlots_PlacesEquippedItemIntoFirstOpenSlots(self):
        #TODO: Make gear aware of which slot it should occupy in the future
        text = """Inventory:
  (w) A WISPWEAVE spellbinder's crown
  (w) A mark of vigilance
  (w) A GLOWING worldwalker's cloak
  (w) A GOSSAMER noble's gleaming gloves of intelligence
  (h) A bright jeweled greatsword of the phoenix
      A GLOWING WISPWEAVE dragon-wing boots
      A GLOWING GOSSAMER hierophant's legwraps
      A twisted gold torc
      A GOSSAMER noble's gleaming raiment of evasion
      Glowing Ahrimal's shielding scale
      A GLOWING rod of endless repentance
 ( 4) A goblet of zombie blood
 ( 9) A darkspawned blackened fish fillet
 (10) A bunch of restorative roots
      A Lucifer's Pride ticket
 ( 2) A ticket to Arnak's Plague
 ( 6) A scroll of minor resurrection
 ( 2) A scroll of lesser resurrection"""

        inventory = Parser().parseInventory(text)
        eg = inventory.EquippedGear_

        assert inventory is not None
        assert eg.Head == "A WISPWEAVE spellbinder's crown"
        assert eg.Jewel1 == "A mark of vigilance"
        assert eg.Jewel2 == "A GLOWING worldwalker's cloak" #Known wrong position, was first open slot
        assert eg.Cloak == "A GOSSAMER noble's gleaming gloves of intelligence" #Known wrong position, was first open slot
        assert eg.Body is None
        assert eg.Hands is None
        assert eg.Legs is None
        assert eg.Feet is None
        assert eg.Held_Right == "A bright jeweled greatsword of the phoenix"
        assert eg.Held_Left is None
        assert len(inventory.Backpack) == 13

    def test_ParseHeldTwoHandedWeapon_EquipsItInHeldRight__DoesNotAlsoHoldInOffhand(self):
        text = """Inventory:
  (h) A bright jeweled greatsword of the phoenix

Inventory:   xx / XX
Encumbrance: yy / YYY"""

        inventory = Parser().parseInventory(text)
        assert inventory is not None
        assert inventory.EquippedGear_.Held_Right.Name == "A bright jeweled greatsword of the phoenix"

    class TestFootersWithEitherDigitsOrWords:
        @pytest.mark.parametrize("inventoryFooter", ["Inventory:   45 / 60",
                                                    "Inventory:   xx / XX",]
                                                    , ids=["Inventory footer with digits",
                                                        "Inventory footer with non-digit characters"])
        def test_InventoryCountFooterWorksWithEitherDigitOrWordCharacters(self, inventoryFooter):
            text = f"""Inventory:
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
 ( 2) A scroll of lesser resurrection

{inventoryFooter}
Encumbrance: 83 / 230"""

            inventory = Parser().parseInventory(text)

            assert len(inventory.Backpack) == 9

        @pytest.mark.parametrize("encumbranceFooter", ["Encumbrance:   45 / 60",
                                                    "Encumbrance:   yy / YYY",]
                                                    , ids=["Encumbrance footer with digits",
                                                        "Encumbrance footer with non-digit characters"])
        def test_EncumbranceFooterWorksWithEitherDigitOrWordCharacters(self, encumbranceFooter):
            text = f"""Inventory:
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
 ( 2) A scroll of lesser resurrection

Inventory:   xx / XX
{encumbranceFooter}"""

            inventory = Parser().parseInventory(text)

            assert len(inventory.Backpack) == 9

    class TestOmitFooterlines:
        def test_Omit__InventoryCount__InInventoryFooter_DoesNotCutOffLastItemsInInventory(self):
            text = """Inventory:
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
 ( 2) A scroll of lesser resurrection

Encumbrance: yy / YYY"""
            inventory = Parser().parseInventory(text)
            assert inventory is not None
            assert len(inventory.Backpack) == 9

        def test_Omit__Encumbrance__InInventoryFooter_DoesNotCutOffLastItemsInInventory(self):
            text = """Inventory:
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
      A Lucifer's Pride ticket
 ( 2) A ticket to Arnak's Plague
 ( 6) A scroll of minor resurrection
 ( 2) A scroll of lesser resurrection

Inventory:   xx / XX"""

            inventory = Parser().parseInventory(text)
            assert inventory is not None
            assert len(inventory.Backpack) == 8

        def test_Omit__EmptyLine__InInventoryFooter_DoesNotCutOffLastItemsInInventory(self):
            text = """Inventory:
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
 ( 9) A darkspawned blackened fish fillet
      A Lucifer's Pride ticket
 ( 2) A ticket to Arnak's Plague
 ( 6) A scroll of minor resurrection
 ( 2) A scroll of lesser resurrection
Inventory:   xx / XX
Encumbrance: yy / YYY"""

            inventory = Parser().parseInventory(text)
            assert inventory is not None
            assert len(inventory.Backpack) == 7

        def test_Omit__AllInventoryFooterLines__DoesNotCutOffLastItemsInInventory(self):
            text = """Inventory:
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
 ( 9) A darkspawned blackened fish fillet
      A Lucifer's Pride ticket
 ( 6) A scroll of minor resurrection
 ( 2) A scroll of lesser resurrection"""

            inventory = Parser().parseInventory(text)
            assert inventory is not None
            assert len(inventory.Backpack) == 6

class TestQuantityItemParse:
    @pytest.mark.parametrize("input, expectedQuantity, expectedName",
                             [(" ( 4) A goblet of zombie blood", 4, "A goblet of zombie blood"),
                              ("( 4) A goblet of zombie blood", 4, "A goblet of zombie blood"),
                              ("(4) A goblet of zombie blood", 4, "A goblet of zombie blood"),
                            ],
                            ids=["Copied from logs",
                                 "Excluding leading space before quantity",
                                 "Single digit quantity with no leading space"])
    def test_ParseItemWithQuantity_MatchesQuantity(self, input, expectedQuantity, expectedName):
        item = Parser.parseQuantityItem(input)
        
        assert item is not None
        assert item.Quantity == expectedQuantity
        assert item.Name == expectedName
    
    def test_ParseItemWithoutQuantityParenthesis_AssumedToBeNoneQuantityItem(self):
        input = "A goblet of zombie blood"

        item = Parser.parseQuantityItem(input)

        assert item.Quantity == None

    @pytest.mark.parametrize("input, expectedName",
                             [("      A GLOWING rod of endless repentance", "A GLOWING rod of endless repentance"),
                              ("A GLOWING rod of endless repentance", "A GLOWING rod of endless repentance")
                            ],
                            ids=["Copied from logs with leading spaces",
                                 "No leading spaces"])
    def test_ParseItemWithoutQuantity_ReturnsItem(self, input, expectedName):
        item = Parser.parseQuantityItem(input)

        assert item.Quantity == None
        assert item.Name == expectedName

class TestEquippedGearParse:
    def test_ParseFullyEquippedGear_PlacesItemsInCorrectGearSlots(self):
        text = """Items in use:
     On Head:  a WISPWEAVE spellbinder's crown
    On Jewel:  a twisted gold torc
    On Jewel:  a mark of vigilance
    On Cloak:  a GLOWING worldwalker's cloak
     On Body:  a GOSSAMER noble's gleaming raiment of evasion
    On Hands:  a GOSSAMER noble's gleaming gloves of intelligence
     On Legs:  a GLOWING GOSSAMER hierophant's legwraps
     On Feet:  a GLOWING WISPWEAVE dragon-wing boots
  Held Right:  a bright jeweled greatsword of the phoenix
   Held Left:  a bright jeweled greatsword of the phoenix"""

        eg = Parser().parseEquippedGear(text)

        assert eg.Head.Name == "a WISPWEAVE spellbinder's crown"
        assert eg.Jewel1.Name == "a twisted gold torc"
        assert eg.Jewel2.Name == "a mark of vigilance"
        assert eg.Cloak.Name == "a GLOWING worldwalker's cloak"
        assert eg.Body.Name == "a GOSSAMER noble's gleaming raiment of evasion"
        assert eg.Hands.Name == "a GOSSAMER noble's gleaming gloves of intelligence"
        assert eg.Legs.Name == "a GLOWING GOSSAMER hierophant's legwraps"
        assert eg.Feet.Name == "a GLOWING WISPWEAVE dragon-wing boots"
        assert eg.Held_Right.Name == "a bright jeweled greatsword of the phoenix"
        assert eg.Held_Left.Name == "a bright jeweled greatsword of the phoenix"
    
    def test_NoEquippedGear_PlacesNoItemsInGearSlots(self):
        text = """Items in use:
     On Head:  nothing
    On Jewel:  nothing
    On Jewel:  nothing
    On Cloak:  nothing
     On Body:  nothing
    On Hands:  nothing
     On Legs:  nothing
     On Feet:  nothing
  Held Right:  nothing
   Held Left:  nothing"""

        eg = Parser().parseEquippedGear(text)

        assert eg.Head == None
        assert eg.Jewel1 == None
        assert eg.Jewel2 == None
        assert eg.Cloak == None
        assert eg.Body == None
        assert eg.Hands == None
        assert eg.Legs == None
        assert eg.Feet == None
        assert eg.Held_Right == None
        assert eg.Held_Left == None
    
    def test_SomeEquippedGear_PlacesItemsInCorrectGearSlotsAndLeavesEmptySlotsAsNone(self):
        text = """Items in use:
     On Head:  a WISPWEAVE spellbinder's crown
    On Jewel:  nothing
    On Jewel:  nothing
    On Cloak:  a GLOWING worldwalker's cloak
     On Body:  nothing
    On Hands:  a GOSSAMER noble's gleaming gloves of intelligence
     On Legs:  nothing
     On Feet:  a GLOWING WISPWEAVE dragon-wing boots
  Held Right:  a bright jeweled greatsword of the phoenix
   Held Left:  a bright jeweled greatsword of the phoenix"""
        
        eg = Parser().parseEquippedGear(text)

        assert eg.Head.Name == "a WISPWEAVE spellbinder's crown"
        assert eg.Cloak.Name == "a GLOWING worldwalker's cloak"
        assert eg.Hands.Name == "a GOSSAMER noble's gleaming gloves of intelligence"
        assert eg.Feet.Name == "a GLOWING WISPWEAVE dragon-wing boots"
        assert eg.Held_Right.Name == "a bright jeweled greatsword of the phoenix"
        assert eg.Held_Left.Name == "a bright jeweled greatsword of the phoenix"

        assert eg.Jewel1 == None
        assert eg.Jewel2 == None
        assert eg.Body == None
        assert eg.Legs == None

class TestAffectParse:
    class TestSingleAffect:
        def test_AffectWithoutEndDuration_MatchesExpectations(self):
            text = """You are affected by: 
Bleed.Dot.Resist.V             """
            isAffect, affects, _ = Parser.ParseAffect().parseAffects(text)

            assert isAffect == True
            assert len(affects) == 1
            assert affects[0].Name == "Bleed.Dot.Resist.V"
            assert affects[0].DurationEndsAt == None

        def test_AffectWithEndDuration_MatchesExpectations(self):
            text = """You are affected by: 
Shield.V                  42m 23s """
            isAffect, affects, _ = Parser.ParseAffect().parseAffects(text)
            now = time.time()

            assert isAffect == True
            assert len(affects) == 1
            assert affects[0].Name == "Shield.V"
            assert affects[0].DurationEndsAt == pytest.approx(now + 42*60 + 23, rel=1)

    def test_NoAffects_ReturnsFalse(self):
        text = """You are affected by:
"""
        isAffect, affects, _ = Parser.ParseAffect().parseAffects(text)

        assert isAffect == False
        assert len(affects) == 0

    def test_TwoAffectsWithTimeDurations_ReturnsTwoAffectsWithCorrectNamesAndTimes(self):
        text = """You are affected by:
Shield.V                  42m 23s
Blur.V                    1h 42m 26s"""

        isAffect, affects, _ = Parser.ParseAffect().parseAffects(text)
        now = time.time()

        assert isAffect == True
        assert len(affects) == 2
        assert affects[0].Name == "Shield.V"
        assert affects[0].DurationEndsAt == pytest.approx(now + 42*60 + 23, rel=1)
        assert affects[1].Name == "Blur.V"
        assert affects[1].DurationEndsAt == pytest.approx(now + 60*60 + 42*60 + 26, rel=1)

    def test_AffectsWithValidCombinationOfTimesFor__Hours__Minutes__Seconds(self):
        text = """You are affected by: 
Bless.II                                                  
Percept.Enhance.I         15s                             
Shield.V                  42m                             
Blur.V                    1h                              
Protect.V                 10m 28s                         
Tough.Skin.V              1h 30s                          
Regenerate.V              2h 15m                          
Vitalize.V                4h 28m 12s                      """

        _, affects, _ = Parser.ParseAffect().parseAffects(text)
        now = time.time()

        assert len(affects) == 8
        assert affects[0].Name == "Bless.II"
        assert affects[0].DurationEndsAt == None
        assert affects[1].Name == "Percept.Enhance.I"
        assert affects[1].DurationEndsAt == pytest.approx(now + 15, rel=1)
        assert affects[2].Name == "Shield.V"
        assert affects[2].DurationEndsAt == pytest.approx(now + 42*60, rel=1)
        assert affects[3].Name == "Blur.V"
        assert affects[3].DurationEndsAt == pytest.approx(now + 1*60*60, rel=1)
        assert affects[4].Name == "Protect.V"
        assert affects[4].DurationEndsAt == pytest.approx(now + 10*60 + 28, rel=1)
        assert affects[5].Name == "Tough.Skin.V"
        assert affects[5].DurationEndsAt == pytest.approx(now + 1*60*60 + 30, rel=1)
        assert affects[6].Name == "Regenerate.V"
        assert affects[6].DurationEndsAt == pytest.approx(now + 2*60*60 + 15*60, rel=1)
        assert affects[7].Name == "Vitalize.V"
        assert affects[7].DurationEndsAt == pytest.approx(now + 4*60*60 + 28*60 + 12, rel=1)

class TestDroppedItemParse:
    @pytest.mark.parametrize("text, expected", [("A stone giant drops a bright ironwood white-oak staff.", "a bright ironwood white-oak staff"),
                                        ("A Tiny Mouse drops giant candycane, dangerously sharp.", "giant candycane, dangerously sharp"),
                                        ("A white dragon elder drops a elder's pendant of dedication.", "a elder's pendant of dedication"),
                                        ("A blood stirge drops a blood-drinker's stiletto.", "a blood-drinker's stiletto"),
                                        ],
                                        ids=["Dash",
                                            "Comma",
                                            "Apostrophe",
                                            "Dash then Comma"])
    def test_NameWithSpecialCharacters_IsParsedCorrectly(self, text: str, expected: str):
        _, itemName = Parser.parseMobDroppedItem(text)

        assert itemName == expected

    @pytest.mark.parametrize("text, expected", [("A Tamian peasant drops a few silver coins.", "a few silver coins"),
                                                ("A Tamian Trapper drops a bag of silver.", "a bag of silver")],
                                            ids=["A few coins",
                                                 "Bag of silver"])
    def test_DropsSilver_IsParsedCorrectly(self, text: str, expected: str):
        _, itemName = Parser.parseMobDroppedItem(text)

        assert itemName == expected

    def test_DropsItem_IsParsedCorrectly(self):
        text = "A greater obsidian basilisk drops a hardened black basilisk boots."

        _, itemName = Parser.parseMobDroppedItem(text)

        assert itemName == "a hardened black basilisk boots"

    @pytest.mark.parametrize("shapeshiftedWerewolfName", ["A small wolf",
                                                            "A fierce wolf",
                                                            "A berserking wolf",
                                                            "A crimson-furred wolf",
                                                            "An ebon-furred stonewolf",
                                                            "An ice-blue frostwolf",
                                                            "A fiery-maned hellwolf",
                                                            "An arctic ghostwolf",
                                                            "A white-fanged banewolf",
                                                            "An ethereal wraithwolf",
                                                            "A storm-grey thunderwolf",
                                                            "An icy cobalt tundrawolf",
                                                            "A fierce ancient ba'alwolf",
                                                            "A vapor-shrouded mistwolf",
                                                            "An azure-eyed stormwolf",
                                                            "A primeval eldritch voidwolf"])
    def test_ShapeshiftedWerewolf_DropsItem_NotConsideredDropByMob(self, shapeshiftedWerewolfName):
        text = f"{shapeshiftedWerewolfName} drops item for testing."

        isMobDroppedItem, _ = Parser.parseMobDroppedItem(text)

        assert not isMobDroppedItem
