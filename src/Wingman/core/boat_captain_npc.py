from enum import StrEnum

class BoatCaptainNpcs(StrEnum):
    Soldaratus_KaidBoatForEvil_FromEvilToKaid = "Soldaratus, the ticket merchant"
    Hodge_KaidBoatForEvil_FromKaidToEvil = "Hodge, the one-eyed ticket merchant"
    Mordat_RealmBoatForEvil_GoingToOtherRealm = "Mordat, the cursed demon merchant"
    Gronkus_KaidBoatForChaos_FromChaosToKaid = "Gronkus, the ticket merchant"
    Haddas_KaidBoatForChaos_FromKaidToChaos = "Haddas, the ticket merchant"
    Horduk_RealmBoatForChaos_GoingToOtherRealm = "Horduk, the ticket merchant"
    Thurgood_KaidBoatForGood_FromGoodToKaid = "Thurgood, the ticket merchant"
    Anise_KaidBoatForGood_FromKaidToGood = "Anise, the ticket merchant"
    Petir_RealmBoatForGood_GoingToOtherRealm = "Petir, the ticket merchant"

    @classmethod
    def KaidBoat_RealmDock_Captains(cls):
        return {
            cls.Soldaratus_KaidBoatForEvil_FromEvilToKaid,
            cls.Gronkus_KaidBoatForChaos_FromChaosToKaid,
            cls.Thurgood_KaidBoatForGood_FromGoodToKaid,
        }

    @classmethod
    def KaidBoat_KaidDock_Captains(cls):
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

    @classmethod
    def FromNameToCaptain(cls, name: str) -> 'BoatCaptainNpcs | None':
        if not name in cls:
            return None

        captain = cls._value2member_map_[name]
        assert isinstance(captain, BoatCaptainNpcs)
        return captain