from typing import Protocol, Sequence

from .action import Action
from .state import State


class CandidateGenerator(Protocol):
    """Generate legal candidate actions for a state."""

    def generate(self, state: State) -> Sequence[Action]:
        ...
