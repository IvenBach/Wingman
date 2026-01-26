import pytest
from Wingman.core.input_receiver import InputReceiver

@pytest.fixture
def receiver() -> InputReceiver:
    """Fixture to provide a fresh instance for every test."""
    return InputReceiver()

def test_clean_message_removes_ansi(receiver):
    # Log line with ANSI color codes (e.g., Red text for damage)
    dirty_input = "\x1b[31mA greater mummy attacks you!\x1b[0m"
    clean = receiver.remove_ANSI_color_codes(dirty_input)
    assert clean == "A greater mummy attacks you!", "ANSI codes were not stripped."

def test_clean_message_handles_partial_ansi(receiver):
    # Sometimes codes are malformed or stuck to text
    dirty_input = "You gain \x1b[1m100\x1b[0m experience."
    clean = receiver.remove_ANSI_color_codes(dirty_input)
    assert clean == "You gain 100 experience.", "Mid-string ANSI codes failed."

def test_queue_fifo_order(receiver):
    # Verify First-In-First-Out behavior
    receiver.receive("First")
    receiver.receive("Second")
    receiver.receive("Third")

    assert receiver.dequeue() == "First"
    assert receiver.dequeue() == "Second"
    assert receiver.dequeue() == "Third"
    assert receiver.dequeue() is None