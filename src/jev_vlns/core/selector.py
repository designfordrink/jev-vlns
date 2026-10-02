from typing import Protocol, Sequence

from .action import Action
from .state import State


class Selector(Protocol):
    """Choose one candidate; never mutate state or execute the action."""

    def select(self, state: State, candidates: Sequence[Action]) -> Action:
        ...
