import time
import pytest
from unittest.mock import MagicMock
from Wingman.core.parser import Character
from Wingman.core.session import GameSession
from Wingman.core.input_receiver import InputReceiver
from Wingman.core.controller import Controller

@pytest.fixture
def session():
    mock_receiver = MagicMock(spec=InputReceiver)
    sess = GameSession(mock_receiver)
    return sess, mock_receiver

def test_xp_per_hour_calculation():
    c = Controller.ForTesting()
    c.gameSession.total_xp = 10000
    c.gameSession.start_time = time.time() - 1800
    rate = c.gameSession.get_xp_per_hour()
    assert 19000 < rate < 21000

def test_reset_clears_state():
    c = Controller.ForTesting()
    c.gameSession.total_xp = 50000
    c.gameSession.group.AddMembers([Character("Foo")])
    countBeforeReset = c.gameSession.group.Count
    c.gameSession.reset()

    assert c.gameSession.total_xp == 0
    assert countBeforeReset == 1
    assert c.gameSession.group.Count == 0  # Should be empty now
    assert (time.time() - c.gameSession.start_time) < 1.0

def test_group_data_flow():
    c = Controller.ForTesting()
    c.gameSession.group.AddMembers([Character("Foo")])
    
    inputs = [
        "<10:00:00> Earthquack's group:",
        "[Orc  40] B Earthquack 100/100 (100%) 100/100 (100%) 100/100 (100%)",
        "[Elf  50] B Legolas    200/200 (100%) 200/200 (100%) 200/200 (100%)",
    ]
    for line in inputs:
        c.receiver.receive(line)

    c.process_queue()

    
    group = c.gameSession.group

    assert group.Count == 2
    assert group.Members[0].Name == 'Earthquack'
    assert group.Members[1].Name == 'Legolas'
