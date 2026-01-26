import pytest
from Wingman.core.parser import Parser
from Wingman.core.input_receiver import InputReceiver


@pytest.fixture
def parser():
    return Parser()

# --- TEST 1: The XP Parser ---
# We verify that the regex handles Single Kills AND Multi-Kills correctly.
def test_parser_single_kill(parser):
    log_line = "You gain 17325 (+43312) experience points."
    xp = parser.parse_xp_message(log_line)
    # 17325 + 43312 = 60637
    assert xp == 60637, f"Expected 60637, got {xp}"


def test_parser_multi_kill_block(parser):
    # This is the "Icicle.Rain" scenario that was failing before
    log_block = """
    A golden sphinx dies!
    You gain 17325 (+43312) experience points.
    A high priest of Ghict dies!
    You gain 20625 (+51562) experience points.
    """
    xp = parser.parse_xp_message(log_block)

    # Sphinx: 60,637
    # Priest: 72,187
    # Total: 132,824
    assert xp == 132824, f"Expected 132824 (sum of both), got {xp}"


def test_parser_no_xp(parser):
    log_line = "A golden sphinx attacks you for 69 damage!"
    xp = parser.parse_xp_message(log_line)
    assert xp == 0, "Should return 0 for combat text"


# --- TEST 2: The Input Receiver ---
# We verify the queue behaves First-In-First-Out (FIFO)

def test_receiver_queue_order():
    receiver = InputReceiver()
    receiver.receive("Line 1")
    receiver.receive("Line 2")
    receiver.receive("Line 3")

    assert receiver.dequeue() == "Line 1"
    assert receiver.dequeue() == "Line 2"
    assert receiver.dequeue() == "Line 3"
    assert receiver.dequeue() is None


# --- TEST 3: The Network Buffering Logic ---
# This simulates the logic we added to NetworkListener.
# We want to see if it correctly handles "fragmented" TCP packets.

class MockNetworkListenerLogic:
    def __init__(self):
        self._buffer = ""
        self.output_lines = []

    def process_chunk(self, chunk_text):
        """
        This mirrors the logic inside your packet_callback
        """
        self._buffer += chunk_text

        # While there is a newline in the buffer, peel off lines
        while '\n' in self._buffer:
            line, self._buffer = self._buffer.split('\n', 1)
            # Simulate 'cleaning' and sending to receiver
            if line.strip():
                self.output_lines.append(line.strip())


def test_network_fragmentation():
    listener = MockNetworkListenerLogic()

    # Simulate Packet 1: "You gain 100" (Incomplete!)
    listener.process_chunk("You gain 100")

    # assert nothing has been output yet because no newline
    assert len(listener.output_lines) == 0

    # Simulate Packet 2: " XP.\nAnd die!" (Completes the line)
    listener.process_chunk(" XP.\nAnd die!\n")

    # Now we should have the full line
    assert len(listener.output_lines) == 2
    assert listener.output_lines[0] == "You gain 100 XP."
    assert listener.output_lines[1] == "And die!"


def test_network_carriage_returns():
    # MUDs often send \r\n. Python split('\n') leaves the \r on the end.
    # We need to make sure our logic handles that cleanly.
    listener = MockNetworkListenerLogic()

    listener.process_chunk("Line 1\r\nLine 2\r\n")

    assert len(listener.output_lines) == 2
    # If the logic doesn't strip \r, this might fail or have hidden chars
    assert listener.output_lines[0] == "Line 1"
    assert listener.output_lines[1] == "Line 2"