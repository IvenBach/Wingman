from enum import Enum, auto

class BoatCaptainNpc(Enum):
    Soldaratus_KaidBoatForEvil_FromEvilToKaid = auto()
    Hodge_KaidBoatForEvil_FromKaidToEvil = auto()
    Mordat_RealmBoatForEvil_GoingToOtherRealm = auto()
    Gronkus_KaidBoatForChaos_FromChaosToKaid = auto()
    Haddas_KaidBoatForChaos_FromKaidToChaos = auto()
    Horduk_RealmBoatForChaos_GoingToOtherRealm = auto()
    Thurgood_KaidBoatForGood_FromGoodToKaid = auto()
    Anise_KaidBoatForGood_FromKaidToGood = auto()
    Petir_RealmBoatForGood_GoingToOtherRealm = auto()

    @classmethod
    def KaidCaptains(cls):
        return {
            cls.Soldaratus_KaidBoatForEvil_FromEvilToKaid,
            cls.Hodge_KaidBoatForEvil_FromKaidToEvil,

            cls.Gronkus_KaidBoatForChaos_FromChaosToKaid,
            cls.Haddas_KaidBoatForChaos_FromKaidToChaos,

            cls.Thurgood_KaidBoatForGood_FromGoodToKaid,
            cls.Anise_KaidBoatForGood_FromKaidToGood
        }

    @classmethod
    def ReturningFromKaidCaptains(cls):
        return {
            cls.Hodge_KaidBoatForEvil_FromKaidToEvil,
            cls.Haddas_KaidBoatForChaos_FromKaidToChaos,
            cls.Anise_KaidBoatForGood_FromKaidToGood
        }

    @classmethod
    def GoingToOtherRealmCaptains(cls):
        return {
            cls.Mordat_RealmBoatForEvil_GoingToOtherRealm,
            cls.Horduk_RealmBoatForChaos_GoingToOtherRealm,
            cls.Petir_RealmBoatForGood_GoingToOtherRealm
        }
