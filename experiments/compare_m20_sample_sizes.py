"""Compare M20 offline landscapes across sample sizes (LOCAL_TEST_M20 9A.8).

Checks that the larger run extends the smaller one, then reports best-candidate
and Top-1 stability. Used to decide whether the EV landscape is stable enough
to interpret.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TOLERANCE = 1e-9


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def index_decisions(payload: dict) -> dict[tuple[int, int], dict]:
    out = {}
    for run in payload["per_run"]:
        for decision in run["decisions"]:
            out[(run["seed"], decision["iteration"])] = decision
    return out


def best_ids(decision: dict, samples: int) -> list[str]:
    means = {
        e["candidate_id"]: sum(v for v in e["outcomes"][:samples] if v is not None)
        / max(1, sum(1 for v in e["outcomes"][:samples] if v is not None))
        for e in decision["entries"]
    }
    best = min(means.values())
    return sorted(k for k, v in means.items() if abs(v - best) <= TOLERANCE)


def prefix_ok(smaller: dict, larger: dict, n_small: int) -> tuple[int, int]:
    good = bad = 0
    for key, decision in smaller.items():
        other = larger.get(key)
        if other is None:
            bad += 1
            continue
        a = {e["candidate_id"]: e["outcomes"] for e in decision["entries"]}
        b = {e["candidate_id"]: e["outcomes"] for e in other["entries"]}
        if set(a) != set(b):
            bad += 1
            continue
        if all(b[cid][:n_small] == a[cid] for cid in a):
            good += 1
        else:
            bad += 1
    return good, bad


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n32", type=Path, required=True)
    parser.add_argument("--n64", type=Path, required=True)
    parser.add_argument("--n128", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    n32 = load(args.n32)
    n64 = load(args.n64)
    d32 = index_decisions(n32)
    d64 = index_decisions(n64)

    result: dict = {"tolerance": TOLERANCE, "comparisons": {}}

    good, bad = prefix_ok(d32, d64, 32)
    result["comparisons"]["n32_to_n64"] = {
        "decisions_compared": len(d32),
        "prefix_consistent": good,
        "prefix_violations": bad,
    }

    # Best-candidate identity stability using each run's own full sample set.
    stable = changed = 0
    for key in d32:
        if best_ids(d32[key], 32) == best_ids(d64[key], 64):
            stable += 1
        else:
            changed += 1
    result["comparisons"]["n32_to_n64"]["best_candidate_stable"] = stable
    result["comparisons"]["n32_to_n64"]["best_candidate_changed"] = changed
    result["comparisons"]["n32_to_n64"]["best_candidate_stable_fraction"] = (
        stable / len(d32) if d32 else 0.0
    )

    if args.n128:
        n128 = load(args.n128)
        d128 = index_decisions(n128)
        good2, bad2 = prefix_ok(d64, d128, 64)
        stable2 = changed2 = 0
        for key in d64:
            if key not in d128:
                continue
            if best_ids(d64[key], 64) == best_ids(d128[key], 128):
                stable2 += 1
            else:
                changed2 += 1
        result["comparisons"]["n64_to_n128"] = {
            "decisions_compared": len(d64),
            "prefix_consistent": good2,
            "prefix_violations": bad2,
            "best_candidate_stable": stable2,
            "best_candidate_changed": changed2,
            "best_candidate_stable_fraction": (
                stable2 / len(d64) if d64 else 0.0
            ),
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())