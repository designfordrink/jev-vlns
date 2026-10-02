from collections.abc import Mapping
from typing import Any, Callable

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


class HeuristicJevClient(JevClientProtocol):
    """Deterministic System-1 surrogate for the benchmark.

    It uses only the serialized state and candidate descriptions. It is not a
    model of the real JEV service; it exists to test whether a non-random,
    candidate-first System-1 can improve the search pipeline.
    """

    def __init__(self, confidence: float = 1.0):
        self.confidence = confidence
        self.calls = 0

    def decide(
        self,
        state: Mapping[str, Any],
        question: DecisionQuestion,
    ) -> DecisionResult:
        self.calls += 1
        candidates = list(question.candidates.items())
        if not candidates:
            raise ValueError("HeuristicJevClient received no candidates")

        if question.task == "repair":
            stacks = state.get("stacks", ())
            def repair_score(item):
                candidate_id, _ = item
                try:
                    stack_index = int(candidate_id.rsplit(":", 1)[1])
                    height = len(stacks[stack_index])
                except (ValueError, IndexError, TypeError):
                    return (10**9, candidate_id)
                return (height, stack_index, candidate_id)
            choice = min(candidates, key=repair_score)[0]
        else:
            # Prefer a two-stack neighborhood, then deterministic ID order.
            # This deliberately does not inspect environment internals.
            choice = min(
                candidates,
                key=lambda item: (0 if item[0].startswith("stacks:") else 1, item[0]),
            )[0]

        return DecisionResult(choice=choice, confidence=self.confidence)
