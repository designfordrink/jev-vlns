"""Offline M20 expected-value landscape runner (no JEV, no API key).

LOCAL_TEST_M20 requires an offline gate that exercises the Expected-Value
evaluator over real M19-shaped decision states before any Live JEV spend:

    smoke   : seeds 1,     iterations 3,  N=32
    offline : seeds 1..5,  iterations 50, N=32 / 64 / 128

The evaluator itself is unchanged (jev_vlns.search.expected_value). This runner
only drives it. Decision states are taken from the solver's own trace
(``before`` + ``destroy_candidates``), so they are exactly the states the real
search visited -- no replay and no re-derivation of solver internals.

The runner never calls JEV, and EV results are never fed back into the search.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.search.expected_value import (
    expected_value_landscape,
    rank_landscape,
    state_key,
)
from jev_vlns.search.vlns import guided_vlns, make_random_vlns_selectors


def evaluate_state(state, candidates, run_seed: int, iteration: int, samples: int) -> dict:
    """Score every candidate for one frozen decision state."""
    before = state_key(state)
    landscape = expected_value_landscape(
        state,
        candidates,
        run_seed=run_seed,
        iteration=iteration,
        samples=samples,
    )
    after = state_key(state)
    if before != after:
        raise RuntimeError("state mutated during expected-value evaluation")

    ranking = rank_landscape(landscape)
    return {
        "state_key": landscape.state_key,
        "samples": landscape.samples,
        "entries": [
            {
                "candidate_id": entry.candidate.id,
                "position": index,
                "sample_count": len(entry.final_moves),
                "feasible_count": entry.feasible_count,
                "error_count": entry.error_count,
                "complete": entry.complete,
                "final_moves": list(entry.final_moves),
                "outcomes": list(entry.outcomes),
                "sample_seeds": list(entry.sample_seeds),
                "mean": entry.mean,
                "median": entry.median,
                "std": entry.std,
                "min": entry.minimum,
                "max": entry.maximum,
                "p10": entry.p10,
                "p90": entry.p90,
            }
            for index, entry in enumerate(landscape.entries)
        ],
        "ranking": ranking,
    }


def _candidate_lookup(candidates):
    return {candidate.id: candidate for candidate in candidates}


def run_one(seed: int, iterations: int, samples: int) -> dict:
    """Run the real solver with Random Destroy and score its decision states.

    Only the Destroy selector is wrapped: Random Destroy is the M18/M20 offline
    control, and it keeps the recorded decision states identical to the ones the
    search actually visited.
    """
    state = make_seeded_state(seed)
    random_destroy, random_repair = make_random_vlns_selectors(seed)

    captured: list[dict] = []

    class _RandomDestroyRecorder:
        def __init__(self, inner):
            self.inner = inner
            self.iteration = 0

        def select(self, current_state, candidates):
            ordered = list(candidates)
            choice = self.inner.select(current_state, ordered)
            captured.append(
                {
                    "iteration": self.iteration,
                    "state": current_state,
                    "candidates": ordered,
                    "selected_candidate": choice.id,
                }
            )
            self.iteration += 1
            return choice

    result = guided_vlns(
        state,
        _RandomDestroyRecorder(random_destroy),
        random_repair,
        iterations=iterations,
        capture_trace=True,
        destroy_min_stacks=2,
        destroy_max_stacks=2,
        destroy_include_non_adjacent=True,
    )

    decisions = []
    for frozen in captured:
        candidates = frozen["candidates"]
        if not candidates:
            continue
        record = evaluate_state(
            frozen["state"], candidates, seed, frozen["iteration"], samples
        )
        decisions.append(
            {
                "iteration": frozen["iteration"],
                "candidate_ids": [c.id for c in candidates],
                "selected_candidate": frozen["selected_candidate"],
                **record,
            }
        )

    return {
        "seed": seed,
        "iterations": result.iterations,
        "samples": samples,
        "destroy_min_stacks": 2,
        "destroy_max_stacks": 2,
        "destroy_include_non_adjacent": True,
        "decisions": decisions,
        "final": {
            "feasible": result.evaluation.feasible,
            "moves": int(result.evaluation.metrics["moves"]),
        },
    }


def summarize(documents: list[dict]) -> dict:
    decisions = [d for doc in documents for d in doc["decisions"]]
    if not decisions:
        raise RuntimeError("no decision states were evaluated")

    candidate_evals = 0
    requested = 0
    successful = 0
    failed = 0
    incomplete = 0
    for decision in decisions:
        for entry in decision["entries"]:
            candidate_evals += 1
            requested += decision["samples"]
            successful += entry["feasible_count"]
            failed += entry["error_count"]
            if not entry["complete"]:
                incomplete += 1

    return {
        "decision_states": len(decisions),
        "candidate_evaluations": candidate_evals,
        "requested_samples": requested,
        "successful_samples": successful,
        "failed_samples": failed,
        "incomplete_candidates": incomplete,
        "flat_landscapes": sum(d["ranking"]["flat"] for d in decisions),
        "mean_candidate_count": statistics.mean(
            len(d["entries"]) for d in decisions
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, choices=(32, 64, 128), required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 4, 5])
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.iterations < 0:
        parser.error("iterations must be >= 0")

    documents = [run_one(seed, args.iterations, args.samples) for seed in args.seeds]
    result = {
        "protocol": {
            "mode": "offline-random-destroy",
            "samples": args.samples,
            "seeds": args.seeds,
            "iterations": args.iterations,
            "destroy_min_stacks": 2,
            "destroy_max_stacks": 2,
            "destroy_include_non_adjacent": True,
            "repair": "random",
            "completion": "deterministic greedy",
            "jev_called": False,
            "objective": (
                "mean final executable moves after Random Repair + greedy completion"
            ),
        },
        "coverage": summarize(documents),
        "per_run": documents,
    }

    stem = args.output.with_suffix("") if args.output.suffix else args.output
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_suffix(".json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(result["coverage"], indent=2))
    print(f"Saved: {stem.with_suffix('.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
