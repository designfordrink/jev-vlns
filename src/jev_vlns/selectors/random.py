import random
from collections.abc import Sequence

from jev_vlns.core.action import Action
from jev_vlns.core.state import State


class RandomSelector:
    """Select a legal candidate uniformly using a private seeded RNG."""

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def select(self, state: State, candidates: Sequence[Action]) -> Action:
        if not candidates:
            raise ValueError("cannot select from an empty candidate list")
        return self._rng.choice(list(candidates))
