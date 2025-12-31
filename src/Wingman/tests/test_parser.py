import pytest
from Wingman.core.parser import parse_xp_message, parse_group_status


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
        assert p1['cls'] == "Orc"
        assert p1['lvl'] == "40"
        assert results[0]['status'] == "B"
        assert p1['name'] == "Earthquack"
        assert p1['hp'] == "227/ 394"

        # Check second member details
        p2 = results[1]
        assert p2['cls'] == "Kenku"
        assert p2['name'] == "Big"

    def test_parse_single_line_update(self):
        """
        Tests parsing a single line, which is how the session often processes data.
        """
        line = "[Kenku          58]  B        Quacamole            360/ 510 ( 70%)    479/ 510 ( 93%)     37/  69 ( 53%)  "
        results = parse_group_status(line)

        assert len(results) == 1
        assert results[0]['status'] == "B"
        assert results[0]['name'] == "Quacamole"
    
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
        actual = results[0]['status']

        assert actual == expected

    def test_ignores_headers_and_noise(self):
        """
        Ensures table headers don't crash the parser or create fake members.
        """
        line = "[ Class         Lvl] Status      Name                 Hits                Fat                Power"
        results = parse_group_status(line)
        assert len(results) == 0

    @pytest.mark.parametrize("input,expected", argvalues=[
                                        ("[Sin         74] B P     Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", 'B P'),
                                        ("[Sin         74] B D     Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", 'B D'),
                                        ("[Sin         74] B S     Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", 'B S'),
                                        ("[Sin         74] P D     Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", 'P D'),
                                        ("[Sin         74] P S     Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", 'P S'),
                                        ("[Sin         74] D S     Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", 'D S'),
                                        ("[Sin         74] B P D   Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", 'B P D'),
                                        ("[Sin         74] B P S   Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", 'B P S'),
                                        ("[Sin         74] B D S   Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", 'B D S'),
                                        ("[Sin         74] P D S   Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", 'P D S'),
                                        ("[Sin         74] B P D S Beautiful        500/500 (100%)  500/500 (100%)  418/731 ( 57%)", 'B P D S')
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
    def test_multiple_status_flags(self, input, expected):        
        actual = parse_group_status(input)[0]['status']

        assert actual == expected
