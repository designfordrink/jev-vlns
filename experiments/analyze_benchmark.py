"""Analyze raw JEV/VLNS benchmark results."""
from __future__ import annotations
import argparse
import json
import statistics
from pathlib import Path
from typing import Any

def load_results(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("expected JSON object with a results list")
    return payload

def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_mode: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_mode.setdefault(str(row["mode"]), []).append(row)
    summary = []
    for mode, mode_rows in by_mode.items():
        moves = [int(row["moves"]) for row in mode_rows]
        feasible = [bool(row["feasible"]) for row in mode_rows]
        summary.append({"mode": mode, "n": len(mode_rows), "feasible_rate": sum(feasible) / len(feasible),
                        "min": min(moves), "median": statistics.median(moves), "mean": statistics.mean(moves),
                        "max": max(moves), "stdev": statistics.stdev(moves) if len(moves) > 1 else 0.0})
    return summary

def deltas_vs_random_random(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_seed: dict[int, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_seed.setdefault(int(row["seed"]), {})[str(row["mode"])] = row
    output = []
    for seed, modes in sorted(by_seed.items()):
        baseline = modes.get("random-random")
        if baseline is None:
            continue
        baseline_moves = int(baseline["moves"])
        for mode, row in sorted(modes.items()):
            if mode == "random-random":
                continue
            output.append({"seed": seed, "mode": mode, "baseline_moves": baseline_moves,
                           "moves": int(row["moves"]), "delta_moves": int(row["moves"]) - baseline_moves})
    return output

def _fmt(value: float) -> str:
    return f"{value:.2f}"

def render_markdown(payload: dict[str, Any]) -> str:
    summary = summarize(payload["results"])
    deltas = deltas_vs_random_random(payload["results"])
    lines = [
        "# Benchmark analysis", "",
        f"Seeds: {payload.get('seeds', 'unknown')}",
        f"Iterations: {payload.get('iterations', 'unknown')}", "",
        "## Summary by mode", "",
        "| Mode | N | Feasible | Min | Median | Mean | Max | Stdev |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in summary:
        lines.append(
            f"| {item['mode']} | {item['n']} | {item['feasible_rate']:.0%} | {item['min']} | "
            f"{_fmt(item['median'])} | {_fmt(item['mean'])} | {item['max']} | {_fmt(item['stdev'])} |"
        )
    if deltas:
        lines += ["", "## Per-seed delta vs random-random", "",
                  "delta_moves = mode.moves - random-random.moves; negative means fewer final moves.", "",
                  "| Seed | Mode | Baseline | Moves | Delta |", "|---:|---|---:|---:|---:|"]
        for item in deltas:
            lines.append(f"| {item['seed']} | {item['mode']} | {item['baseline_moves']} | {item['moves']} | {item['delta_moves']:+d} |")
    lines += ["", "## Interpretation guardrails", "",
              "- moves is the primary solver-quality outcome.",
              "- projected_objective is a search-time estimate, not the final objective.",
              "- Per-seed deltas should be inspected before any aggregate claim.",
              "- Fake JEV and the heuristic System-1 surrogate are controls; they are not evidence about real JEV quality.",
              "- A real JEV comparison must keep instances, seeds, iteration/time budgets, and solver code fixed.", ""]
    return "\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a JEV/VLNS benchmark JSON artifact.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=None, help="Optional Markdown report path.")
    args = parser.parse_args()
    payload = load_results(args.input)
    report = render_markdown(payload)
    print(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"\nSaved: {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())