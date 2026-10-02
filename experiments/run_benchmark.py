"""Run the controlled JEV/VLNS benchmark matrix.

Examples:
    python experiments/run_benchmark.py
    python experiments/run_benchmark.py --seeds 1 2 3 4 5 --iterations 50
    python experiments/run_benchmark.py --output experiments/runs/baseline.json
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

from jev_vlns.evaluation.benchmark import run_matrix


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the JEV/VLNS benchmark matrix.")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42],
                        help="Instance/search seeds to run (default: 42).")
    parser.add_argument("--iterations", type=int, default=25,
                        help="VLNS iteration budget per run (default: 25).")
    parser.add_argument("--output", type=Path, default=None,
                        help="Optional JSON output path.")
    args = parser.parse_args()

    if args.iterations < 0:
        parser.error("--iterations must be >= 0")

    rows = []
    for seed in args.seeds:
        rows.extend(result.as_dict() for result in run_matrix(seed=seed, iterations=args.iterations))

    print("mode           seed  feasible  moves  projected  destroy_jev  repair_jev")
    print("-" * 76)
    for row in rows:
        print(f"{row["mode"]:<14} {row["seed"]:>4}  {str(row["feasible"]):<8}  {row["moves"]:>5}  {row["projected_objective"]:>9.1f}  {row["destroy_jev_calls"]:>11}  {row["repair_jev_calls"]:>9}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"iterations": args.iterations, "seeds": args.seeds, "results": rows}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nSaved: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
