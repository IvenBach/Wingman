from enum import StrEnum

from Wingman.core.character import Character

class HealthTagger():
    """
    Used for adding tags to Tkinter ttk.Treeview items.
    """
    class HealthLevels(StrEnum):
        ZEROED = 'zeroed'
        AT_OR_BELOW_25 = 'below25percent'
        AT_OR_BELOW_50 = 'below50percent'
        HEALTHY = 'healthy'

    @staticmethod
    def HealthTag(c: Character) -> str:
        """
        Creates a health tag from a characters health.
        """

        if c.Hp.Current <= 0: # should not occur
            raise ValueError("Health below 1 should never occur.")


        if c.Hp.Current == 1:
            return HealthTagger.HealthLevels.ZEROED.value

        if c.Hp.Current / c.Hp.Maximum <= 0.25:
            return HealthTagger.HealthLevels.AT_OR_BELOW_25.value

        if c.Hp.Current / c.Hp.Maximum <= 0.5:
            return HealthTagger.HealthLevels.AT_OR_BELOW_50.value

        return HealthTagger.HealthLevels.HEALTHY.value