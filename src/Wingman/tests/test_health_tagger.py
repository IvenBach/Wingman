
import pytest
from Wingman.core.character import Character
from Wingman.core.health_Tagger import HealthTagger
from Wingman.core.resource_bar import ResourceBar


class TestHealthTagger():
    @pytest.mark.parametrize('currentHp, maximumHp, expectedTag', [
                                                    (1, 100, HealthTagger.HealthLevels.ZEROED),
                                                    (2, 100, HealthTagger.HealthLevels.AT_OR_BELOW_25),
                                                    (24, 100, HealthTagger.HealthLevels.AT_OR_BELOW_25),
                                                    (25, 100, HealthTagger.HealthLevels.AT_OR_BELOW_25),
                                                    (26, 100, HealthTagger.HealthLevels.AT_OR_BELOW_50),
                                                    (49, 100, HealthTagger.HealthLevels.AT_OR_BELOW_50),
                                                    (50, 100, HealthTagger.HealthLevels.AT_OR_BELOW_50),
                                                    (51, 100, HealthTagger.HealthLevels.HEALTHY)
                                                    ])
    def test_HealthBelowOne_Error(self, currentHp, maximumHp, expectedTag):
        c = Character("_", hp=ResourceBar(current=currentHp, maximum=maximumHp))

        tag = HealthTagger.HealthTag(c)
        
        assert  tag == expectedTag
    
    
    def test_HealthBelow_1_RaisesValueError(self):
        c = Character("_", hp=ResourceBar(current=0, maximum=100))

        with pytest.raises(ValueError):
            tag = HealthTagger.HealthTag(c)

if __name__ == "__main__":
    TestHealthTagger().test_HealthBelow_1_RaisesValueError()