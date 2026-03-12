from typing import Iterable
import pytest

from Wingman.core.parsing.tokenstream import TokenStream

def test_Peeking():
    ts = TokenStream(['a', 'b', 'c'])

    assert ts.peek() == 'a'
    assert ts.consume() == 'a'
    assert ts.peek() == 'b'

def test_PeekingN():
    ts = TokenStream(['a', 'b', 'c'])

    assert ts.peek_n(0) == 'a'
    assert ts.peek_n(1) == 'b'
    assert ts.peek_n(2) == 'c'
    assert ts.peek_n(3) is None

def test_Consuming():
    ts = TokenStream(['a', 'b', 'c'])

    assert ts.consume() == 'a'
    assert ts.consume() == 'b'
    assert ts.consume() == 'c'
    assert ts.consume() is None

def test_ConsumingIf():
    ts = TokenStream(['a', 'b', 'c'])

    assert ts.consume_if({'a', 'x'}) == 'a'
    assert ts.consume_if({'a', 'x'}) is None
    assert ts.consume_if({'b', 'x'}) == 'b'
    assert ts.consume_if({'c', 'x'}) == 'c'
    assert ts.consume_if({'d', 'x'}) is None

@pytest.mark.parametrize('tokens, expected', [(['a', 'b' , 'c'], False),
                                              ([], True)],
                                ids=['Non-empty iterable',
                                     'Empty iterable'])
def test_Empty(tokens: Iterable[str], expected: bool):
    ts = TokenStream(tokens)

    assert ts.isEmpty() == expected

def test_Remaining():
    expected = ['b', 'c']
    ts = TokenStream(['a', 'b', 'c'])

    ts.consume()

    assert ts.remaining() == expected