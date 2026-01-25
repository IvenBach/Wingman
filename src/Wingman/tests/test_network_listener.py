import pytest
from unittest.mock import MagicMock
from Wingman.core.network_listener import NetworkListener
from Wingman.core.input_receiver import InputReceiver
from scapy.all import IP, TCP


# Helper class to mock Scapy packet behavior cleanly
class MockPacket:
    def __init__(self, src_ip, sport, payload):
        self.ip_layer = MagicMock()
        self.ip_layer.src = src_ip

        self.tcp_layer = MagicMock()
        self.tcp_layer.sport = sport
        self.tcp_layer.payload = payload

    def __contains__(self, item):
        # Allow "IP in packet" checks
        if item == IP: return True
        if item == TCP: return True
        return False

    def __getitem__(self, item):
        # Allow packet[IP] access
        if item == IP: return self.ip_layer
        if item == TCP: return self.tcp_layer
        raise KeyError


@pytest.fixture
def listener_stack():
    receiver = InputReceiver()
    listener = NetworkListener(receiver)
    # Ensure buffer is empty
    listener._buffer = ""
    return listener, receiver


def test_packet_callback_buffers_split_lines(listener_stack):
    listener, receiver = listener_stack
    target_ip = listener.target_ip
    target_port = listener.target_port

    # Packet 1: "You gain 1" (Incomplete)
    pkt1 = MockPacket(target_ip, target_port, b"You gain 1")
    listener.packet_callback(pkt1)

    # Receiver should be empty, buffer should hold data
    assert receiver.dequeue_from_left() is None
    assert listener._buffer == "You gain 1"

    # Packet 2: "00 XP.\n" (Completes the line)
    pkt2 = MockPacket(target_ip, target_port, b"00 XP.\n")
    listener.packet_callback(pkt2)

    # Now receiver should have the line
    assert receiver.dequeue_from_left() == "You gain 100 XP."
    assert listener._buffer == ""  # Buffer should be cleared


def test_ignores_wrong_ip(listener_stack):
    listener, receiver = listener_stack

    # Packet from wrong IP
    pkt = MockPacket("1.2.3.4", 4000, b"You gain 100 XP.\n")
    listener.packet_callback(pkt)

    assert receiver.dequeue_from_left() is None


def test_clean_payload_decoding(listener_stack):
    listener, receiver = listener_stack
    target_ip = listener.target_ip
    target_port = listener.target_port

    # Packet with standard text
    payload = b"Testing output.\n"
    pkt = MockPacket(target_ip, target_port, payload)
    listener.packet_callback(pkt)

    assert receiver.dequeue_from_left() == "Testing output."
