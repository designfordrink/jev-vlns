"""Analyze one or more M10 replay JSON files as an M11 choice-quality experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jev_vlns.evaluation.choice_quality import summarize_choice_metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    docs = [json.loads(path.read_text(encoding="utf-8")) for path in args.files]
    result = summarize_choice_metrics(docs)

    lines = [
        "# M11 — JEV Choice vs Local Landscape",
        "",
        "| Mode | Runs | Top-1 rate | Mean rank | Mean regret | Normalized regret |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for mode, row in result["summary"].items():
        lines.append(
            f"| {mode} | {row['runs']} | {row['top1_rate']:.3f} | "
            f"{row['mean_rank']:.2f} | {row['mean_regret']:.3f} | "
            f"{row['mean_normalized_regret']:.3f} |"
        )

    lines += [
        "",
        "Interpretation: top-1 is the fraction of iterations where the selector "
        "picked a locally best Destroy candidate. Normalized regret is 0 for "
        "the best choice and 1 for the worst available choice in that iteration.",
        "",
        "This is a **choice-quality** measurement, not a solver-quality claim.",
    ]
    output = "\n".join(lines) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
