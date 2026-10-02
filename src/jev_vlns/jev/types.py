from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class DecisionQuestion:
    """A typed decision request sent to a JEV-compatible client."""

    task: str
    question: str
    candidates: Mapping[str, str]
    state: Mapping[str, Any] = field(default_factory=dict)
    objective: str | None = None


@dataclass(frozen=True)
class DecisionResult:
    """Normalized JEV decision returned to the selector layer."""

    choice: str
    confidence: float | None = None
    latency_ms: float | None = None
    cost_usd: float | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


class JevClientProtocol:
    """Small runtime interface implemented by real and fake JEV clients."""

    def decide(
        self,
        state: Mapping[str, Any],
        question: DecisionQuestion,
    ) -> DecisionResult:
        raise NotImplementedError
