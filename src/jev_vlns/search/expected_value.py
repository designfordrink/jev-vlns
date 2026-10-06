"""Expected-value downstream landscape under the actual Random Repair policy.

M20 measures the objective that a Destroy choice actually faces in M19:
expected final executable move count after one Destroy, Random Repair, and
deterministic greedy completion.

The evaluator is deliberately independent of JEV. It never changes the
solver's live state and uses common random numbers across candidates.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random
from statistics import mean, median, stdev
from collections.abc import Sequence

from jev_vlns.container_stack.state import ContainerStackState
from .destroy import DestroyCandidate, apply_destroy
from .repair import apply_repair, generate_repair_candidates
from .vlns import _finish_greedily, _repair_randomly


M20_PROTOCOL_VERSION = "m20-ev-v1"


@dataclass(frozen=True)
class CandidateEV:
    candidate: DestroyCandidate
    sample_seeds: tuple[int, ...]
    final_moves: tuple[int, ...]
    mean: float
    median: float
    std: float
    minimum: int
    maximum: int
    p10: float
    p90: float
    feasible_count: int
    error_count: int
    # Index-aligned stream: one entry per requested sample, in sample-index
    # order, with None where the sample failed. ``final_moves`` is the filtered
    # (successes-only) view and therefore not aligned with ``sample_seeds``.
    outcomes: tuple[int | None, ...] = ()

    @property
    def complete(self) -> bool:
        return self.error_count == 0 and self.feasible_count == len(self.final_moves)


@dataclass(frozen=True)
class LandscapeResult:
    state_key: str
    samples: int
    entries: tuple[CandidateEV, ...]


def state_key(state: ContainerStackState) -> str:
    """Return a deterministic identity for a frozen decision state."""
    payload = repr(
        (
            state.stacks,
            state.stack_destinations,
            tuple(
                (c.id, c.destination, c.priority)
                for c in state.containers
            ),
            state.moves,
            state.delivered,
        )
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sample_seed(
    run_seed: int,
    iteration: int,
    frozen_state_key: str,
    sample_index: int,
) -> int:
    """Derive the protocol seed; candidate ID is intentionally excluded."""
    raw = (
        f"{M20_PROTOCOL_VERSION}|{run_seed}|{iteration}|"
        f"{frozen_state_key}|{sample_index}"
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big", signed=False)


def _percentile(values: Sequence[int], fraction: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * fraction
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    weight = position - low
    return ordered[low] + (ordered[high] - ordered[low]) * weight


def _evaluate_candidate(
    state: ContainerStackState,
    candidate: DestroyCandidate,
    sample_seeds: Sequence[int],
) -> CandidateEV:
    """Evaluate one candidate without mutating the supplied state."""
    partial = apply_destroy(state, candidate)
    repairs = generate_repair_candidates(partial)
    outcomes: list[int] = []
    stream: list[int | None] = []
    errors = 0

    for seed in sample_seeds:
        try:
            choices = _repair_randomly(
                partial,
                partial.removed,
                repairs,
                random.Random(seed),
            )
            if not choices:
                raise ValueError("Random Repair produced no legal complete repair")
            repaired = apply_repair(partial, choices)
            finished = _finish_greedily(repaired)
            if not finished.is_complete:
                raise ValueError("greedy completion did not finish")
            moves = int(finished.moves)
            outcomes.append(moves)
            stream.append(moves)
        except Exception:
            errors += 1
            stream.append(None)

    return CandidateEV(
        candidate=candidate,
        sample_seeds=tuple(sample_seeds),
        final_moves=tuple(outcomes),
        mean=mean(outcomes) if outcomes else float("inf"),
        median=median(outcomes) if outcomes else float("inf"),
        std=stdev(outcomes) if len(outcomes) >= 2 else 0.0,
        minimum=min(outcomes) if outcomes else 0,
        maximum=max(outcomes) if outcomes else 0,
        p10=_percentile(outcomes, 0.10),
        p90=_percentile(outcomes, 0.90),
        feasible_count=len(outcomes),
        error_count=errors,
        outcomes=tuple(stream),
    )


def expected_value_landscape(
    state: ContainerStackState,
    candidates: Sequence[DestroyCandidate],
    *,
    run_seed: int,
    iteration: int,
    samples: int = 64,
) -> LandscapeResult:
    """Evaluate every candidate under the same Random Repair sample schedule."""
    if samples not in {32, 64, 128}:
        raise ValueError("M20 samples must be one of 32, 64, or 128")
    if not candidates:
        raise ValueError("cannot evaluate an empty candidate set")

    frozen_key = state_key(state)
    seeds = tuple(
        sample_seed(run_seed, iteration, frozen_key, index)
        for index in range(samples)
    )
    entries = tuple(
        _evaluate_candidate(state, candidate, seeds)
        for candidate in candidates
    )
    return LandscapeResult(
        state_key=frozen_key,
        samples=samples,
        entries=entries,
    )


def rank_landscape(
    landscape: LandscapeResult,
    *,
    tolerance: float = 1e-9,
) -> dict[str, object]:
    """Return aligned best-candidate, rank and regret diagnostics.

    Random Repair can hand the deterministic greedy completion a configuration
    it cannot finish, so a candidate may have fewer valid samples than
    requested. Such candidates are ranked on the samples that did complete,
    and their counts are reported alongside the ranking so failures stay
    visible instead of being silently dropped.

    A candidate with no valid sample is unrankable and raises, because its
    expected value is undefined rather than merely noisy.
    """
    unrankable = [
        entry.candidate.id
        for entry in landscape.entries
        if entry.feasible_count == 0
    ]
    if unrankable:
        raise ValueError(
            "cannot rank a landscape with candidates that have no valid "
            f"samples: {sorted(unrankable)}"
        )

    valid = [entry for entry in landscape.entries if entry.feasible_count > 0]

    values = [entry.mean for entry in valid]
    best = min(values)
    worst = max(values)
    denominator = worst - best

    tied_best = {
        entry.candidate.id
        for entry in valid
        if abs(entry.mean - best) <= tolerance
    }
    ordered = sorted(valid, key=lambda entry: entry.mean)

    ranks: dict[str, int] = {}
    rank = 1
    previous: float | None = None
    for position, entry in enumerate(ordered, start=1):
        if previous is not None and abs(entry.mean - previous) > tolerance:
            rank = position
        ranks[entry.candidate.id] = rank
        previous = entry.mean

    return {
        "best_mean": best,
        "worst_mean": worst,
        "tied_best": sorted(tied_best),
        "flat": denominator <= tolerance,
        "ranks": ranks,
        "regret": {
            entry.candidate.id: entry.mean - best
            for entry in valid
        },
        "normalized_regret": {
            entry.candidate.id: (
                0.0 if denominator <= tolerance
                else (entry.mean - best) / denominator
            )
            for entry in valid
        },
        "ordered_candidate_ids": [entry.candidate.id for entry in ordered],
        "sample_counts": {
            entry.candidate.id: entry.feasible_count
            for entry in landscape.entries
        },
        "error_counts": {
            entry.candidate.id: entry.error_count
            for entry in landscape.entries
        },
        "total_errors": sum(entry.error_count for entry in landscape.entries),
    }
