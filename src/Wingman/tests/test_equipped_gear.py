import pytest

from Wingman.core.inventory import Item
from Wingman.core.equipment import Equipment

def test_BothGearSetsEmpty_Equal():
    eg1 = Equipment()
    eg2 = Equipment()

    assert eg1 == eg2

def test_SameSlot_OneGearSetEmpty_NotEqual():
    eg1 = Equipment(head=Item("Helmet"))
    eg2 = Equipment()

    assert eg1 != eg2

def test_SameSlot_CapitalizationDifference_Equal():
    eg1 = Equipment(head=Item("Helmet"))
    eg2 = Equipment(head=Item("helmet"))

    assert eg1 == eg2

def test_SameSlot_DifferentItem_NotEqual():
    eg1 = Equipment(head=Item("Helmet"))
    eg2 = Equipment(head=Item("Cap"))

    assert eg1 != eg2

def test_SameSlot_SameItem_Equal():
    eg1 = Equipment(head=Item("Helmet"))
    eg2 = Equipment(head=Item("Helmet"))

    assert eg1 == eg2

def test_AllSlots_SameItems_Equal():
    eg1 = Equipment(head=Item("Helmet"),
                      jewel1=Item("Jewel1"),
                      jewel2=Item("Jewel2"),
                      cloak=Item("Cloak"),
                      body=Item("Body"),
                      hands=Item("Hands"),
                      legs=Item("Legs"),
                      feet=Item("Feet"),
                      held_right=Item("Held_Right"),
                      held_left=Item("Held_Left"))
    
    eg2 = Equipment(head=Item("Helmet"),
                      jewel1=Item("Jewel1"),
                      jewel2=Item("Jewel2"),
                      cloak=Item("Cloak"),
                      body=Item("Body"),
                      hands=Item("Hands"),
                      legs=Item("Legs"),
                      feet=Item("Feet"),
                      held_right=Item("Held_Right"),
                      held_left=Item("Held_Left"))

    assert eg1 == eg2
