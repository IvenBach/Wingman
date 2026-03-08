import pytest
from Wingman.core.input_receiver import InputReceiver
from Wingman.core.parsing.parser import Parser
from Wingman.core.controller import Controller

@pytest.fixture
def receiver() -> InputReceiver:
    """Fixture to provide a fresh instance for every test."""
    return InputReceiver() 

def test_queue_fifo_order(receiver: InputReceiver):
    # Verify First-In-First-Out behavior
    receiver.receive("First")
    receiver.receive("Second")
    receiver.receive("Third")

    assert receiver.dequeue() == "First"
    assert receiver.dequeue() == "Second"
    assert receiver.dequeue() == "Third"
    assert receiver.dequeue() is None

@pytest.mark.parametrize("inputMember", [Parser.MeditationState.Termination_ByStanding,
                                         Parser.MeditationState.Termination_ByFullPower])
def test_MeditationStateValue_ReturnsMeditationStateMember(inputMember):
    c = Controller.ForTesting()
    c.receiver.receive(inputMember.value)
    
    value = c.receiver.dequeue()

    assert value == inputMember
