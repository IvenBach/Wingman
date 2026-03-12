from collections import deque
from typing import Iterable

class TokenStream:

    def __init__(self, tokens: Iterable[str]) -> None:
        self._tokens = deque(tokens)

    def peek(self) -> str | None:
        '''Return the next token without consuming it.'''
        return self._tokens[0] if self._tokens else None

    def peek_n(self, n: int) -> str | None:
        '''Return the nth token without consuming it.'''
        return self._tokens[n] if len(self._tokens) > n else None

    def consume(self) -> str | None:
        '''Consume and return the next token.'''
        return self._tokens.popleft() if self._tokens else None

    def consume_if(self, valid_tokens: Iterable[str]) -> str | None:
        '''Consume token if it belongs to the iterable predicate.'''
        token = self.peek()

        if token is None:
            return None

        if token in valid_tokens:
            return self.consume()

        return None

    def isEmpty(self) -> bool:
        '''Check if there are no more tokens.'''
        return not self._tokens

    def remaining(self) -> list[str]:
        '''Return a list of remaining tokens without consuming them.'''
        return list(self._tokens)
