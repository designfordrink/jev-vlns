import json
import time
import urllib.error
import urllib.request
from typing import Any, Mapping

from .config import JevConfig
from .types import DecisionQuestion, DecisionResult


class JevClientError(RuntimeError):
    """Raised when the remote JEV service cannot produce a valid decision."""


class JevClient:
    """Minimal HTTP adapter for a JEV-compatible /v1/systemone endpoint."""

    def __init__(self, config: JevConfig):
        self.config = config

    def decide(
        self,
        state: Mapping[str, Any],
        question: DecisionQuestion,
    ) -> DecisionResult:
        if not self.config.api_key:
            raise JevClientError("JEV API key is not configured")

        payload = {
            "model": self.config.model,
            "state": dict(state),
            "questions": {
                "task": question.task,
                "question": question.question,
                "objective": question.objective,
                "candidates": dict(question.candidates),
                "state": dict(question.state),
            },
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.config.base_url}/v1/systemone",
            data=body,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        started = time.perf_counter()
        try:
            with urllib.request.urlopen(
                request, timeout=self.config.timeout_seconds
            ) as response:
                raw = response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise JevClientError(f"JEV request failed: {exc}") from exc

        latency_ms = (time.perf_counter() - started) * 1000
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise JevClientError("JEV returned invalid JSON") from exc

        choice = data.get("choice") or data.get("selected")
        if not isinstance(choice, str):
            raise JevClientError("JEV response has no string choice")

        confidence = data.get("confidence")
        if confidence is not None:
            try:
                confidence = float(confidence)
            except (TypeError, ValueError) as exc:
                raise JevClientError("JEV confidence is not numeric") from exc

        return DecisionResult(
            choice=choice,
            confidence=confidence,
            latency_ms=latency_ms,
            cost_usd=_optional_float(data.get("cost_usd")),
            raw=data,
        )


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
