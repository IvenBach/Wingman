import pytest
from unittest.mock import MagicMock
from scapy.all import IP, TCP
import time
from unittest.mock import patch, call
from Wingman.core.network_listener import NetworkListener
from Wingman.core.input_receiver import InputReceiver
from Wingman.core.controller import Controller
from Wingman.core.parser import Parser
from Wingman.core.affect import Affect

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
    c = Controller.ForTesting()
    listener = NetworkListener(receiver, c, target_ip=c.listener.target_ip, target_port=c.listener.target_port)
    listener._buffer = "" # Ensure buffer is empty
    listener.controller.receiver = receiver #Use same receiver
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

def test_ignores_wrong_port(listener_stack):
    listener, receiver = listener_stack

    # Packet from wrong Port
    pkt = MockPacket("1.2.3.4", 4000, b"You gain 100 XP.\n")
    listener.packet_callback(pkt)

    assert receiver.dequeue() is None

def test_ignores_wrong_ip(listener_stack):
    listener, receiver = listener_stack

    # Packet from wrong server address
    pkt = MockPacket("2.3.4.5", 1234, b"Text that won't be received.\n")
    listener.packet_callback(pkt)

    assert receiver.dequeue() is None

def test_MatchingIpAddressAndPort_DequeuesPayload(listener_stack):
    listener, receiver = listener_stack
    pkt = MockPacket(listener.target_ip, listener.target_port, b"Queued and dequeued just fine.\n")
    listener.packet_callback(pkt)

    assert receiver.dequeue() == "Queued and dequeued just fine."

def test_PayloadWithoutNewline_NotAddedToReceiver(listener_stack):
    listener, receiver = listener_stack
    pkt = MockPacket(listener.target_ip, listener.target_port, b"Line without newline character *shouldn't* occur, but testing for safety.")
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

def test_MeditationWithTrailingCharStateInfo_ExpectedMeditationStateIsReceived_TrailingContinuesOnToReceiver(listener_stack):
    listener, receiver = listener_stack
    listener.controller.receiver = receiver #Use same receiver
    target_ip = listener.target_ip
    target_port = listener.target_port

    postFixedCharState = '\n\n\x1b[8m���charstate {"combat":"AGGRESSIVE","currentWeight":67,"maxWeight":230,"pos":"Standing"}\n'
    text = Parser.MeditationState.Begin.value + postFixedCharState
    payload = (text).encode('utf-8')
    pkt = MockPacket(target_ip, target_port, payload)

    with patch.object(receiver, receiver.receive.__name__) as mockedReceiveMethod:
        listener.packet_callback(pkt)

    mockedReceiveMethod.assert_has_calls([call(Parser.MeditationState.Begin),
                                          call(''), #These zero-length strings aren't dealt with in the non-mocked receiver
                                          call(''),
                                          call('���charstate {"combat":"AGGRESSIVE","currentWeight":67,"maxWeight":230,"pos":"Standing"}')],
                                        any_order=False)

def test_AffectsWithAnsiColorCoding_CleanedBeforeSentToReceiver_AsListOfAffect(listener_stack):
    listener, receiver = listener_stack
    target_ip = listener.target_ip
    target_port = listener.target_port

    text = """\x1b[1mYou are affected by: \x1b[0;0m\x1b[1;30m
\x1b[0;33mCombat.II                \x1b[0;0m\x1b[1;30m                                 
\x1b[0;33mAgility.II               \x1b[0;0m\x1b[1;30m                                 
\x1b[0;33mDirect.Enhance.II        \x1b[0;0m\x1b[1;30m                                 
\x1b[0;33mEvade.Enhance.III        \x1b[0;0m\x1b[1;30m                                 
\x1b[0;33mIntelligence.III         \x1b[0;0m\x1b[1;30m                                 
\x1b[0;33mPercept.Enhance.I        \x1b[0;0m\x1b[1;30m                                 
\x1b[0;33mBless.II                 \x1b[0;0m\x1b[1;30m                                 
\x1b[0;33mBlur.V                    \x1b[0;0m\x1b[1;30m1h 34m 28s\x1b[0;0m\x1b[1;30m                      
\x1b[0;33mShield.V                  \x1b[0;0m\x1b[1;30m1h 14m 38s\x1b[0;0m\x1b[1;30m                      \x1b[1;30m
\n\n\n\x1b[8m"""
    payload = (text).encode('utf-8')
    pkt = MockPacket(target_ip, target_port, payload)

    with patch.object(receiver, receiver.receive.__name__) as mockedReceiveMethod:
        listener.packet_callback(pkt)

    now = time.time()
    argument = mockedReceiveMethod.mock_calls[0].args[0]
    assert isinstance(argument, list)
    assert all(isinstance(affect, Affect) for affect in argument)
    assert argument[0].Name == "Combat.II"
    assert argument[0].DurationEndsAt is None
    assert argument[1].Name == "Agility.II"
    assert argument[1].DurationEndsAt is None
    assert argument[2].Name == "Direct.Enhance.II"
    assert argument[2].DurationEndsAt is None
    assert argument[3].Name == "Evade.Enhance.III"
    assert argument[3].DurationEndsAt is None
    assert argument[4].Name == "Intelligence.III"
    assert argument[4].DurationEndsAt is None
    assert argument[5].Name == "Percept.Enhance.I"
    assert argument[5].DurationEndsAt is None
    assert argument[6].Name == "Bless.II"
    assert argument[6].DurationEndsAt is None
    assert argument[7].Name == "Blur.V"
    assert argument[7].DurationEndsAt == pytest.approx(now + 3600 + 34*60 + 28, abs=1)
    assert argument[8].Name == "Shield.V"
    assert argument[8].DurationEndsAt == pytest.approx(now + 3600 + 14*60 + 38, abs=1)

def test_AffectsWithPrefixedAndSuffixedInfo_PrefixedAndSuffixedInfoContinueOnToReceiver(listener_stack):
    listener, receiver = listener_stack
    target_ip = listener.target_ip
    target_port = listener.target_port

    affectText = """\x1b[1mYou are affected by: \x1b[0;0m\x1b[1;30m
\x1b[0;33mCombat.II                \x1b[0;0m\x1b[1;30m                                 
\n\n\n\x1b[8m"""

    payload = ("Some text before.\n" + affectText + "\nSome text after.\n").encode('utf-8')
    pkt = MockPacket(target_ip, target_port, payload)

    with patch.object(receiver, receiver.receive.__name__) as mockedReceiveMethod:
        listener.packet_callback(pkt)

    mockCalls = mockedReceiveMethod.mock_calls

    assert all(isinstance(affect, Affect) for affect in mockCalls[0].args[0])
    assert mockCalls[1].args[0] == "Some text before."
    assert mockCalls[2].args[0] == ''
    assert mockCalls[3].args[0] == "Some text after."
