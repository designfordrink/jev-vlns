"""Run M13: paired real-JEV vs Random end-to-end search.

The treatment is real JEV Destroy + Random Repair. The control is
Random Destroy + Random Repair. Each seed is run independently with the
same iteration budget; results are paired by seed.

Requires a configured JEV API key for the treatment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jev_vlns.evaluation.benchmark import run_benchmark, run_real_jev_destroy_benchmark


def summarize(rows: list[dict]) -> dict:
    deltas = [row["real_jev_moves"] - row["random_moves"] for row in rows]
    wins = sum(delta < 0 for delta in deltas)
    ties = sum(delta == 0 for delta in deltas)
    return {
        "runs": len(rows),
        "mean_random_moves": mean(row["random_moves"] for row in rows),
        "mean_real_jev_moves": mean(row["real_jev_moves"] for row in rows),
        "mean_delta_moves": mean(deltas),
        "median_delta_moves": median(deltas),
        "min_delta_moves": min(deltas),
        "max_delta_moves": max(deltas),
        "real_jev_wins": wins,
        "ties": ties,
        "losses": sum(delta > 0 for delta in deltas),
        "real_jev_win_rate": wins / len(rows) if rows else 0.0,
        "mean_fallbacks": mean(row["fallbacks"] for row in rows),
        "total_calls": sum(row["jev_calls"] for row in rows),
        "total_fallbacks": sum(row["fallbacks"] for row in rows),
        "total_successes": sum(row.get("successes", 0) for row in rows),
        "all_feasible": all(
            row.get("random_feasible", True) and row.get("real_jev_feasible", True)
            for row in rows
        ),
        "mean_latency_ms": mean(row.get("average_latency_ms", 0.0) for row in rows),
        "total_input_tokens": sum(row.get("input_tokens", 0) for row in rows),
        "total_output_tokens": sum(row.get("output_tokens", 0) for row in rows),
        "total_cost_usd": sum(row["cost_usd"] for row in rows),
    }


def render_markdown(
    rows: list[dict],
    summary: dict,
    *,
    seeds: list[int],
    iterations: int,
    destroy_min_stacks: int = 2,
    destroy_max_stacks: int = 2,
    destroy_include_non_adjacent: bool = True,
) -> str:
    lines = [
        "# M13 — Real JEV End-to-End Validation",
        "",
        "Paired comparison of real JEV Destroy + Random Repair against Random Destroy + Random Repair.",
        "",
        f"- seeds: {seeds}",
        f"- iterations: {iterations}",
        f"- destroy neighborhood: K={destroy_min_stacks}..{destroy_max_stacks}, non-adjacent={destroy_include_non_adjacent}",
        "",
        "## Paired results",
        "",
        "| Seed | Random moves | Real JEV moves | Delta (JEV-Random) | Fallbacks | Calls | Cost USD |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['seed']} | {row['random_moves']} | {row['real_jev_moves']} | "
            f"{row['real_jev_moves'] - row['random_moves']} | {row['fallbacks']} | "
            f"{row['jev_calls']} | {row['cost_usd']:.6f} |"
        )
    lines += [
        "",
        "## Aggregate",
        "",
        f"- Random mean moves: **{summary['mean_random_moves']:.3f}**",
        f"- Real JEV mean moves: **{summary['mean_real_jev_moves']:.3f}**",
        f"- Mean paired delta (JEV − Random): **{summary['mean_delta_moves']:.3f}**",
        f"- Median paired delta: **{summary['median_delta_moves']:.3f}**",
        f"- Min / max paired delta: **{summary.get('min_delta_moves', 0):+d} / "
        f"{summary.get('max_delta_moves', 0):+d}**",
        f"- Real JEV wins / ties / losses: **{summary['real_jev_wins']} / "
        f"{summary['ties']} / {summary.get('losses', 0)}** of {summary['runs']} "
        f"({summary['real_jev_win_rate']:.1%} wins)",
        f"- All runs feasible: **{summary.get('all_feasible', True)}**",
        f"- Total JEV calls: **{summary['total_calls']}**, successes "
        f"**{summary.get('total_successes', 0)}**, fallbacks "
        f"**{summary.get('total_fallbacks', 0)}**",
        f"- Mean latency: **{summary.get('mean_latency_ms', 0.0):.1f} ms**",
        f"- Tokens in/out: **{summary.get('total_input_tokens', 0)}** / "
        f"**{summary.get('total_output_tokens', 0)}**",
        f"- Total API cost: **$ {summary['total_cost_usd']:.6f}**",
        "",
        "## Paired deltas",
        "",
        "delta = JEV moves − Random moves; negative favours Real JEV.",
        "",
        "| Comparison | Wins | Ties | Losses | Mean Δ | Median Δ |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Real JEV vs Random (K=2) | {summary['real_jev_wins']} | "
        f"{summary['ties']} | {summary.get('losses', 0)} | "
        f"{summary['mean_delta_moves']:+.3f} | {summary['median_delta_moves']:+.3f} |",
        "",
        "## Interpretation rule",
        "",
        "Negative delta means real JEV used fewer final moves and therefore won that paired seed.",
        "This experiment tests end-to-end search quality under the fixed Random Repair protocol.",
        "It does not establish that JEV is universally better, nor does it replace M12 local choice-quality measurements.",
        "Fallbacks are reported separately and must be considered when interpreting the result.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 4, 5])
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--destroy-min-stacks", type=int, default=2)
    parser.add_argument("--destroy-max-stacks", type=int, default=2)
    parser.add_argument("--destroy-include-non-adjacent", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    if args.destroy_min_stacks != 2 or args.destroy_max_stacks != 2:
        parser.error("M19 requires fixed K=2 Destroy neighborhoods")

    rows = []
    for seed in args.seeds:
        random_result = run_benchmark(
            seed=seed,
            iterations=args.iterations,
            mode="random-random",
        ).as_dict()
        real_result = run_real_jev_destroy_benchmark(
            seed=seed,
            iterations=args.iterations,
            destroy_min_stacks=args.destroy_min_stacks,
            destroy_max_stacks=args.destroy_max_stacks,
            destroy_include_non_adjacent=args.destroy_include_non_adjacent,
        ).as_dict()

        row = {
            "seed": seed,
            "random_moves": random_result["moves"],
            "real_jev_moves": real_result["moves"],
            "random_feasible": random_result["feasible"],
            "real_jev_feasible": real_result["feasible"],
            "fallbacks": real_result["destroy_jev_fallbacks"],
            "jev_calls": real_result["destroy_jev_calls"],
            "successes": real_result["destroy_jev_calls"]
            - real_result["destroy_jev_fallbacks"],
            "average_latency_ms": real_result["destroy_jev_average_latency_ms"],
            "input_tokens": real_result["destroy_jev_input_tokens"],
            "output_tokens": real_result["destroy_jev_output_tokens"],
            "cost_usd": real_result["destroy_jev_cost_usd"],
        }
        rows.append(row)
        print(
            f"seed={seed} random={row['random_moves']} "
            f"real_jev={row['real_jev_moves']} "
            f"delta={row['real_jev_moves'] - row['random_moves']} "
            f"fallbacks={row['fallbacks']} "
            f"cost_usd={row['cost_usd']:.6f}"
        )

    summary = summarize(rows)
    payload = {
        "experiment": "M13",
        "seeds": args.seeds,
        "iterations": args.iterations,
        "destroy_min_stacks": args.destroy_min_stacks,
        "destroy_max_stacks": args.destroy_max_stacks,
        "destroy_include_non_adjacent": args.destroy_include_non_adjacent,
        "results": rows,
        "summary": summary,
    }

    if args.output:
        json_path = args.output.with_suffix(".json")
        md_path = args.output.with_suffix(".md")
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(
            render_markdown(
                rows, summary,
                seeds=args.seeds,
                iterations=args.iterations,
                destroy_min_stacks=args.destroy_min_stacks,
                destroy_max_stacks=args.destroy_max_stacks,
                destroy_include_non_adjacent=args.destroy_include_non_adjacent,
            ),
            encoding="utf-8",
        )
        print(f"Saved: {json_path}")
        print(f"Saved: {md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
