import pytest
from unittest.mock import MagicMock
from scapy.all import IP, TCP
from unittest.mock import patch, call
from Wingman.core.network_listener import NetworkListener
from Wingman.core.input_receiver import InputReceiver
from Wingman.core.controller import Controller
from Wingman.core.parser import Parser

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
def listener_stack() -> tuple[NetworkListener, InputReceiver]:
    receiver = InputReceiver()
    listener = NetworkListener(receiver, Controller.ForTesting())
    # Ensure buffer is empty
    listener._buffer = ""
    return listener, receiver


def test_packet_callback_buffers_split_lines(listener_stack):
    listener, receiver  = listener_stack
    target_ip = listener.target_ip
    target_port = listener.target_port

    # Packet 1: "You gain 1" (Incomplete)
    pkt1 = MockPacket(target_ip, target_port, b"You gain 1")
    listener.packet_callback(pkt1)

    # Receiver should be empty, buffer should hold data
    assert receiver.dequeue() is None
    assert listener._buffer == "You gain 1"

    # Packet 2: "00 XP.\n" (Completes the line)
    pkt2 = MockPacket(target_ip, target_port, b"00 XP.\n")
    listener.packet_callback(pkt2)
    
    # Now receiver should have the line
    assert receiver.dequeue() == "You gain 100 XP."
    assert listener._buffer == ""  # Buffer should be cleared


def test_ignores_wrong_ip(listener_stack):
    listener, receiver = listener_stack

    # Packet from wrong IP
    pkt = MockPacket("1.2.3.4", 4000, b"You gain 100 XP.\n")
    listener.packet_callback(pkt)

    assert receiver.dequeue() is None


def test_clean_payload_decoding(listener_stack):
    listener, receiver = listener_stack
    target_ip = listener.target_ip
    target_port = listener.target_port

    # Packet with standard text
    payload = b"Testing output.\n"
    pkt = MockPacket(target_ip, target_port, payload)
    listener.packet_callback(pkt)

    assert receiver.dequeue() == "Testing output."

def test_AnyInformationIncludedWithBuffOrShieldRefresh_BeforeSpellEndingValueAndAfterSpellStartsValue_ContinuesOnToReceiverForProcessing(listener_stack):
    listener, receiver = listener_stack
    listener.controller.receiver = receiver #Use same receiver
    assert isinstance(receiver, InputReceiver)
    target_ip = listener.target_ip
    target_port = listener.target_port

    text = f"""{Parser.AfkStatus.BeginAfk.value}
{Parser.AfkStatus.EndAfk.value}
You cast a Chaos.Fortitude.I spell!
You invoke a prayer to Ra'Kur, filling you with an unnatural energy!
{Parser.ParseBuffOrShieldText.ChaosDotFortitude_Ended.value}
{Parser.ParseBuffOrShieldText.ChaosDotFortitudeStarts.value}
Text that trails in case it too needs to be forwarded.\n""" #Lines before the buff/shield ending value are still forwarded on
    payload = (text).encode('utf-8')
    pkt = MockPacket(target_ip, target_port, payload)

    #Testing a bit of implementation details. Not sure how else to test lines before the buff/shield ending value are still forwarded on without this.
    with patch.object(receiver, receiver.receive.__name__) as mockedReceiveMethod:
        listener.packet_callback(pkt)


    assert mockedReceiveMethod.call_args_list == [call(Parser.AfkStatus.BeginAfk.value),
                                                    call(Parser.AfkStatus.EndAfk.value),
                                                    call("You cast a Chaos.Fortitude.I spell!"),
                                                    call("You invoke a prayer to Ra'Kur, filling you with an unnatural energy!"),
                                                    call("Text that trails in case it too needs to be forwarded.")]
