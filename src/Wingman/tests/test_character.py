import pytest
from Wingman.core.character import Character
from Wingman.core.status_indicator import StatusIndicator
from Wingman.core.resource_bar import ResourceBar

class TestCharacter:
    def test_CharacterInitialization(self):
        c = Character(class_="Sin", 
                         level=1, 
                         status=StatusIndicator(0), 
                         name="Beautiful", 
                         hp=ResourceBar(2, 3), 
                         fat=ResourceBar(4, 5), 
                         pow=ResourceBar(6, 7))

        assert c.Class_ == "Sin"
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
