from unittest.mock import patch
import pytest
from Wingman.core.input_receiver import InputReceiver
from Wingman.core.parser import Parser
from Wingman.core.controller import Controller

@pytest.fixture
def receiver() -> InputReceiver:
    """Fixture to provide a fresh instance for every test."""
    return InputReceiver()

def test_clean_message_removes_ansi(receiver: InputReceiver):
    # Log line with ANSI color codes (e.g., Red text for damage)
    dirty_input = "\x1b[31mA greater mummy attacks you!\x1b[0m"
    clean = receiver.remove_ANSI_color_codes(dirty_input)
    assert clean == "A greater mummy attacks you!", "ANSI codes were not stripped."

def test_clean_message_handles_partial_ansi(receiver: InputReceiver):
    # Sometimes codes are malformed or stuck to text
    dirty_input = "You gain \x1b[1m100\x1b[0m experience."
    clean = receiver.remove_ANSI_color_codes(dirty_input)
    assert clean == "You gain 100 experience.", "Mid-string ANSI codes failed."

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
