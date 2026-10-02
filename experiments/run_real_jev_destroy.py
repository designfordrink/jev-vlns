"""Run the real-JEV Destroy + Random Repair experiment.

Requires a JEV/TypeSafe API key in the environment. This script intentionally
does not fall back to a fake client when the key is missing.

Example:
    python experiments/run_real_jev_destroy.py --seeds 1 2 3 4 5 --iterations 50
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jev_vlns.evaluation.benchmark import run_real_jev_destroy_benchmark


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[42])
    parser.add_argument("--iterations", type=int, default=25)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    rows = []
    for seed in args.seeds:
        result = run_real_jev_destroy_benchmark(
            seed=seed,
            iterations=args.iterations,
        )
        row = result.as_dict()
        rows.append(row)
        print(
            f"real-jev-random seed={seed} moves={row['moves']} "
            f"JEV_calls={row['destroy_jev_calls']} "
            f"fallbacks={row['destroy_jev_fallbacks']} "
            f"avg_latency_ms={row['destroy_jev_average_latency_ms']:.1f} "
            f"D-regret={row['mean_destroy_regret']:.2f}"
        )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                {
                    "mode": "real-jev-random",
                    "seeds": args.seeds,
                    "iterations": args.iterations,
                    "results": rows,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"Saved: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
