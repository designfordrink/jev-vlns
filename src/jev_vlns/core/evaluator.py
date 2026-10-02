from dataclasses import dataclass, field
from typing import Any, Protocol

from .action import Action
from .state import State


@dataclass(frozen=True)
class Evaluation:
    """Feasibility and objective result for a state."""

    feasible: bool
    objective: float
    metrics: dict[str, Any] = field(default_factory=dict)


class Executor(Protocol):
    """Apply a legal action deterministically and return a new state."""

    def apply(self, state: State, action: Action) -> State:
        ...


class Evaluator(Protocol):
    """Validate and score a state independently of the selector."""

    def evaluate(self, state: State) -> Evaluation:
        ...
