import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping

from .config import JevConfig
from .types import DecisionQuestion, DecisionResult


class JevClientError(RuntimeError):
    """Raised when the remote JEV service cannot produce a valid decision."""


@dataclass
class JevClientStats:
    calls: int = 0
    successes: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0

    @property
    def average_latency_ms(self) -> float:
        return self.total_latency_ms / self.calls if self.calls else 0.0

    @property
    def average_cost_usd(self) -> float:
        return self.total_cost_usd / self.successes if self.successes else 0.0


class JevClient:
    """HTTP adapter for TypeSafe's /v1/systemone choice endpoint."""

    def __init__(self, config: JevConfig):
        self.config = config
        self.stats = JevClientStats()

    def decide(
        self,
        state: Mapping[str, Any],
        question: DecisionQuestion,
    ) -> DecisionResult:
        self.stats.calls += 1
        started = time.perf_counter()
        try:
            result = self._decide(state, question, started)
        except Exception:
            self.stats.failures += 1
            raise
        self.stats.successes += 1
        return result

    def _decide(
        self,
        state: Mapping[str, Any],
        question: DecisionQuestion,
        started: float,
    ) -> DecisionResult:
        if not self.config.api_key:
            raise JevClientError("JEV API key is not configured")

        criteria = dict(question.candidates)
        payload = {
            "model": self.config.model,
            "state": dict(state),
            "questions": {
                "choice": {
                    "type": "choice",
                    "instructions": question.question,
                    "criteria": criteria,
                }
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

        try:
            with urllib.request.urlopen(
                request, timeout=self.config.timeout_seconds
            ) as response:
                raw = response.read().decode("utf-8")
                status = getattr(response, "status", 200)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise JevClientError(f"JEV request failed: {exc}") from exc

        latency_ms = (time.perf_counter() - started) * 1000
        if status >= 400:
            raise JevClientError(f"JEV returned HTTP {status}")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise JevClientError("JEV returned invalid JSON") from exc

        try:
            answer = data["answers"]["choice"]
            choice = answer["choice"]
        except (KeyError, TypeError) as exc:
            raise JevClientError("JEV response has no answers.choice.choice") from exc

        if not isinstance(choice, str):
            raise JevClientError("JEV choice is not a string")

        confidence = answer.get("confidence")
        if confidence is not None:
            try:
                confidence = float(confidence)
            except (TypeError, ValueError) as exc:
                raise JevClientError("JEV confidence is not numeric") from exc

        usage = data.get("usage") or {}
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        cost = usage.get("cost")
        cost_usd = 0.0 if cost is None else float(cost)
        self.stats.total_input_tokens += input_tokens
        self.stats.total_output_tokens += output_tokens
        self.stats.total_cost_usd += cost_usd

        return DecisionResult(
            choice=choice,
            confidence=confidence,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            raw=data,
        )
