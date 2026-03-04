import pytest
from Wingman.core.item import Item, ItemSlot, QuantityComparer

def test_NonQuantityStringName_MatchesItemName_ReturnsTrue():    
    line = "A goblet of zombie blood"
    item = Item("A goblet of zombie blood")

    assert line == item

def test_QuantityStringName_MatchesItemName_AndSameQuantity_ReturnsTrue():
    line = "( 2) A goblet of zombie blood"
    item = Item("A goblet of zombie blood", quantity=2)

    assert line == item

def test_QuantityStringName_MatchesItemName_DifferentQuantity_ReturnsFalse():
    line = "( 2) A goblet of zombie blood"
    item = Item("A goblet of zombie blood", quantity=3)

    assert line != item

def test_ItemFoundWithinList_ReturnsTrue():
    item = Item("A goblet of zombie blood")
    itemList = [Item("A goblet of zombie blood"), Item("A bright jeweled greatsword of the phoenix")]

    assert item in itemList

def test_ItemOfDifferingQuantityFoundWithinList_Foo():
    item = Item("A goblet of zombie blood", quantity=2)
    itemList = [Item("A goblet of zombie blood", quantity=3), Item("A bright jeweled greatsword of the phoenix")]

    assert item not in itemList

def test_SubtractingItemWithSameName_NoQuantities_ReturnsZero():
    item1 = Item("A goblet of zombie blood")
    item2 = Item("A goblet of zombie blood")
    actual = item1.subtract(item2)

    assert actual == 0

def test_CapitalizationOnNameDoesNotAffectComparison_ReturnsTrue():
    line = "A goblet of zombie blood"
    item = Item("a GOBLET of ZOMBIE BLOOD")

    assert line == item

class TestQuantityComparer:
    def test_DifferentNames_ReturnsInvalidComparison(self):
        item1 = Item("A goblet of zombie blood")
        item2 = Item("A bunch of restorative roots")

        assert item1.QuantityComparison(item2) == QuantityComparer.INVALID_COMPARISON

    def test_BothNonQuantities_ReturnsEqualTo(self):
        item1 = Item("A goblet of zombie blood")
        item2 = Item("A goblet of zombie blood")

        assert item1.QuantityComparison(item2) == QuantityComparer.EQUAL_TO

    @pytest.mark.parametrize("item1, item2, expected", [(Item("A goblet of zombie blood"), Item("A goblet of zombie blood", quantity=2), QuantityComparer.LESS_THAN),
                                            (Item("A goblet of zombie blood", quantity=2), Item("A goblet of zombie blood"), QuantityComparer.GREATER_THAN)
                                            ],
                                            ids=[f"{QuantityComparer.LESS_THAN}",
                                                f"{QuantityComparer.GREATER_THAN}"])
    def test_SameName_NonQuantityComparedAgainstQuantity(self, item1, item2, expected):
        assert item1.QuantityComparison(item2) == expected

    @pytest.mark.parametrize("item1, item2, expected", [(Item("A goblet of zombie blood", quantity=2), Item("A goblet of zombie blood", quantity=2), QuantityComparer.EQUAL_TO),
                                            (Item("A goblet of zombie blood", quantity=2), Item("A goblet of zombie blood", quantity=3), QuantityComparer.LESS_THAN),
                                            (Item("A goblet of zombie blood", quantity=3), Item("A goblet of zombie blood", quantity=2), QuantityComparer.GREATER_THAN)
                                            ],
                                            ids=[f"{QuantityComparer.EQUAL_TO}",
                                                f"{QuantityComparer.LESS_THAN}",
                                                f"{QuantityComparer.GREATER_THAN}"])
    def test_SameName_BothQuantities(self, item1, item2, expected):
        assert item1.QuantityComparison(item2) == expected

    def test_SelfCompare_ReturnsEqualTo(self):
        a = Item("A goblet of zombie blood", quantity=2)

        assert a.QuantityComparison(a) == QuantityComparer.EQUAL_TO
    
    def test_A_ComparedTo_B__ReturnsTrue__And__B_ComparedTo_A_ReturnsEqualTo(self):
        a = Item("A goblet of zombie blood", quantity=2)
        b = Item("A goblet of zombie blood", quantity=2)

        assert a.QuantityComparison(b) == QuantityComparer.EQUAL_TO
        assert b.QuantityComparison(a) == QuantityComparer.EQUAL_TO

    def test_A_ComparedTo_B_ReturnsZero__B_ComparedTo_C_ReturnsZero__Then__A_ComparedTo_C_ReturnsZero(self):
        a = Item("A goblet of zombie blood", quantity=2)
        b = Item("A goblet of zombie blood", quantity=2)
        c = Item("A goblet of zombie blood", quantity=2)

        assert a.QuantityComparison(b) == QuantityComparer.EQUAL_TO
        assert b.QuantityComparison(c) == QuantityComparer.EQUAL_TO
        assert a.QuantityComparison(c) == QuantityComparer.EQUAL_TO

    def test_A_ComparedTo_B_ReturnsLessThan__B_ComparedTo_C_ReturnsLessThan__Then__A_ComparedTo_C_ReturnsSameSignAs_A_To_B_Comparison(self):
        a = Item("A goblet of zombie blood", quantity=2)
        b = Item("A goblet of zombie blood", quantity=3)
        c = Item("A goblet of zombie blood", quantity=4)

        assert a.QuantityComparison(b) == QuantityComparer.LESS_THAN
        assert b.QuantityComparison(c) == QuantityComparer.LESS_THAN
        assert a.QuantityComparison(c) == QuantityComparer.LESS_THAN
