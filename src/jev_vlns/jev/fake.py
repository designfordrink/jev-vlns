from collections.abc import Callable, Mapping
from typing import Any

from .types import DecisionQuestion, DecisionResult, JevClientProtocol


class FakeJevClient(JevClientProtocol):
    """Deterministic JEV substitute for tests, CI and offline experiments."""

    def __init__(
        self,
        strategy: str = "first",
        scripted_choices: list[str] | None = None,
        confidence: float = 1.0,
    ):
        self.strategy = strategy
        self.scripted_choices = list(scripted_choices or [])
        self.confidence = confidence
        self.calls = 0

    def decide(
        self,
        state: Mapping[str, Any],
        question: DecisionQuestion,
    ) -> DecisionResult:
        self.calls += 1
        ids = list(question.candidates)
        if not ids:
            raise ValueError("FakeJevClient received no candidates")

        if self.strategy == "first":
            choice = ids[0]
        elif self.strategy == "last":
            choice = ids[-1]
        elif self.strategy == "scripted":
            if not self.scripted_choices:
                raise ValueError("No scripted JEV choices remaining")
            choice = self.scripted_choices.pop(0)
        else:
            raise ValueError(f"Unknown fake strategy: {self.strategy}")

        if choice not in question.candidates:
            raise ValueError(f"FakeJevClient selected unknown candidate: {choice}")

        return DecisionResult(choice=choice, confidence=self.confidence)
