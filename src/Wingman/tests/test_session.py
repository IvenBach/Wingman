import time
import pytest
from unittest.mock import MagicMock
from Wingman.core.parser import Character
from Wingman.core.session import GameSession
from Wingman.core.input_receiver import InputReceiver


@pytest.fixture
def session():
    mock_receiver = MagicMock(spec=InputReceiver)
    sess = GameSession(mock_receiver)
    return sess, mock_receiver


def test_process_queue_calculates_xp(session):
    sess, mock_receiver = session
    mock_receiver.remove_from_top.side_effect = [
        "You gain 1000 experience points.",
        "Garbage line.",
        None
    ]
    logs = sess.process_queue()
    assert sess.total_xp == 1000
    assert len(logs) == 1


def test_xp_per_hour_calculation(session):
    sess, _ = session
    sess.total_xp = 10000
    sess.start_time = time.time() - 1800
    rate = sess.get_xp_per_hour()
    assert 19000 < rate < 21000


def test_reset_clears_state(session):
    sess, _ = session
    sess.total_xp = 50000
    sess.Group.AddMembers([Character("Foo")]) # Setup dirty state
    countBeforeReset = sess.Group.Count
    sess.reset()

    assert sess.total_xp == 0
    assert countBeforeReset == 1
    assert sess.Group.Count == 0  # Should be empty now
    assert (time.time() - sess.start_time) < 1.0


def test_group_data_flow(session):
    sess, mock_receiver = session

    # 1. Pre-fill with stale data
    sess.Group.AddMembers([Character("Foo")])
    
    # 2. Mock incoming game text
    mock_receiver.remove_from_top.side_effect = [
        "<10:00:00> Earthquack's group:",
        # Changed status to valid 'B'
        "[Orc  40] B Earthquack 100/100 (100%) 100/100 (100%) 100/100 (100%)",
        "[Elf  50] B Legolas    200/200 (100%) 200/200 (100%) 200/200 (100%)",
        None
    ]

    # 3. Process
    sess.process_queue()

    # 4. Verify
    group = sess.Group

    # This assertion failed before because StaleUser wasn't cleared
    # and new users weren't added. Now it should pass.
    assert group.Count == 2
    assert group.Members[0].Name == 'Earthquack'
    assert group.Members[1].Name == 'Legolas'

def test_UngroupedCharacterGainsNewFollower_NewFollowerAddedToLatestGroupData():
    receiver = InputReceiver()
    receiver.receive("FooBar follows you")

    session = GameSession(receiver)
    session.process_queue()

    assert session.Group.Count == 1

def test_LeaderGainsNewFollower_NewFollowerAddedToLatestGroupData():
    receiver = InputReceiver()
    groupCommandText = """Beautiful's group:

[ Class        Lvl] Status     Name                 Hits               Fat                Power            
[Sin            69]           Beautiful            500/ 500 (100%)    497/ 500 ( 99%)    592/ 707 ( 83%)   
[Skelton        50]           Skeletor             396/ 396 (100%)    396/ 396 (100%)    554/ 554 (100%) """

    receiver.receive(groupCommandText)
    session = GameSession(receiver)
    session.process_queue()    

    receiver.receive("FooBar follows you")
    session.process_queue()

    assert session.Group.Count == 3

def test_LeavingGroup_ClearsLatestGroupData():
    receiver = InputReceiver()
    groupCommandText = """Foo's group:

[ Class      Lv] Status   Name              Hits            Fat             Power         
[Necromance   9]         Foo              100/100 (100%)  100/100 (100%)  119/119 (100%)  

[Sin         74]         Beautiful        500/500 (100%)  383/500 ( 76%)  503/731 ( 68%)  """

    receiver.receive(groupCommandText)
    session = GameSession(receiver)
    session.process_queue()

    groupCountWhileMemberOfGroup = session.Group.Count

    receiver.receive("You disband from the group.")
    session.process_queue()

    assert groupCountWhileMemberOfGroup == 2
    assert session.Group.Count == 0

def test_nonGroupLeaderLeavesGroup_IsRemovedFromLatestGroupData():
    receiver = InputReceiver()
    groupText = """Foo's group:

[ Class      Lv] Status   Name              Hits            Fat             Power         
[Necromance   9]         Foo              100/100 (100%)  100/100 (100%)  119/119 (100%)  

[Sin         74]         Bar              500/500 (100%)  383/500 ( 76%)  503/731 ( 68%)  

[Hydro       60]         Baz              100/200 (100%)  200/400 ( 50%)  300/600 ( 50%)  """
    receiver.receive(groupText)
    session = GameSession(receiver)
    session.process_queue()
    initialGroupSize = session.Group.Count

    receiver.receive("Baz disbands from the group.")
    session.process_queue()

    assert initialGroupSize == 3
    assert session.Group.Count == 2
