"""Offline choice-quality metrics for M20 (LOCAL_TEST_M20 sections 12-13).

The offline runs use Random Destroy, so the "selected" candidate is the one the
Random control actually picked in the solver trace. This quantifies how a
uniform-random selector scores against the aligned Random-Repair EV landscape --
the reference against which the live JEV result is judged.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

TOLERANCE = 1e-9


def candidate_means(decision: dict) -> dict[str, float]:
    means = {}
    for entry in decision["entries"]:
        values = [v for v in entry["outcomes"] if v is not None]
        if values:
            means[entry["candidate_id"]] = sum(values) / len(values)
    return means


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))

    ranks: list[int] = []
    regrets: list[float] = []
    normalized: list[float] = []
    top1 = 0
    flat = 0
    decisions = 0

    for run in payload["per_run"]:
        for decision in run["decisions"]:
            means = candidate_means(decision)
            if not means:
                continue
            decisions += 1
            best = min(means.values())
            worst = max(means.values())
            denominator = worst - best
            if denominator <= TOLERANCE:
                flat += 1

            ordered = sorted(means.values())
            for candidate_id, value in means.items():
                rank = 1 + sum(1 for other in ordered if other < value - TOLERANCE)
                means[candidate_id] = value
                if candidate_id == decision.get("selected_candidate"):
                    ranks.append(rank)
                    regrets.append(value - best)
                    normalized.append(
                        0.0 if denominator <= TOLERANCE else (value - best) / denominator
                    )
                    if abs(value - best) <= TOLERANCE:
                        top1 += 1

    result = {
        "decisions": decisions,
        "top1": top1,
        "top1_rate": top1 / decisions if decisions else 0.0,
        "mean_rank": statistics.mean(ranks) if ranks else 0.0,
        "median_rank": statistics.median(ranks) if ranks else 0.0,
        "mean_regret": statistics.mean(regrets) if regrets else 0.0,
        "median_regret": statistics.median(regrets) if regrets else 0.0,
        "mean_normalized_regret": statistics.mean(normalized) if normalized else 0.0,
        "median_normalized_regret": (
            statistics.median(normalized) if normalized else 0.0
        ),
        "flat_landscapes": flat,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())