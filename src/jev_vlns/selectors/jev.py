from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeVar

from jev_vlns.jev.types import JevClientProtocol

T = TypeVar("T")
Fallback = Callable[[Any, Sequence[T]], T]
StateSerializer = Callable[[Any], Mapping[str, Any]]


class JevSelector:
    """Select only from locally generated candidates using JEV."""

    def __init__(
        self,
        client: JevClientProtocol,
        fallback: Fallback[T],
        *,
        task: str,
        question: str,
        objective: str | None = None,
        min_confidence: float = 0.0,
        state_serializer: StateSerializer | None = None,
    ):
        self.client = client
        self.fallback = fallback
        self.task = task
        self.question = question
        self.objective = objective
        self.min_confidence = min_confidence
        self.state_serializer = state_serializer or _default_state_serializer

    def select(self, state: Any, candidates: Sequence[T]) -> T:
        if not candidates:
            raise ValueError("cannot select from an empty candidate list")

        candidate_map: dict[str, str] = {}
        for candidate in candidates:
            candidate_id = _candidate_id(candidate)
            if candidate_id in candidate_map:
                raise ValueError(f"duplicate candidate id: {candidate_id}")
            candidate_map[candidate_id] = _candidate_description(candidate)

        state_data = self.state_serializer(state)
        from jev_vlns.jev.types import DecisionQuestion
        question = DecisionQuestion(
            task=self.task,
            question=self.question,
            candidates=candidate_map,
            state=state_data,
            objective=self.objective,
        )

        try:
            result = self.client.decide(state_data, question)
            if result.choice not in candidate_map:
                raise ValueError(f"JEV selected unknown candidate: {result.choice}")
            if result.confidence is not None and result.confidence < self.min_confidence:
                raise ValueError(
                    f"JEV confidence {result.confidence:.3f} is below "
                    f"minimum {self.min_confidence:.3f}"
                )
            return next(c for c in candidates if _candidate_id(c) == result.choice)
        except Exception:
            return self.fallback(state, candidates)


def _candidate_id(candidate: Any) -> str:
    value = getattr(candidate, "id", None)
    if not isinstance(value, str) or not value:
        raise ValueError("candidate must expose a non-empty string 'id'")
    return value


def _candidate_description(candidate: Any) -> str:
    value = getattr(candidate, "description", None)
    return value if isinstance(value, str) and value else repr(candidate)


def _default_state_serializer(state: Any) -> Mapping[str, Any]:
    if isinstance(state, Mapping):
        return dict(state)
    if hasattr(state, "__dict__"):
        return {
            key: value for key, value in vars(state).items() if _is_json_like(value)
        }
    return {"state": repr(state)}


def _is_json_like(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, (list, tuple)):
        return all(_is_json_like(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(k, str) and _is_json_like(v) for k, v in value.items())
    return False
