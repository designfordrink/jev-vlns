"""Run M20: Real JEV choice quality against the aligned Random-Repair EV landscape.

The JEV decision is made first. Only after the response is received do we
evaluate every legal Destroy candidate with the actual M19 downstream policy:
Random Repair + deterministic greedy completion.

This is a live experiment and requires a JEV API key.
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
from jev_vlns.evaluation.benchmark import (
    JEV_DESTROY_OBJECTIVE,
    JEV_DESTROY_QUESTION,
    _jev_destroy_candidate_context,
    _jev_state,
)
from jev_vlns.jev.client import JevClient
from jev_vlns.jev.config import JevConfig
from jev_vlns.search.vlns import guided_vlns, make_random_vlns_selectors
from jev_vlns.selectors.jev import JevDestroySelector, JevSelector


def run_one(seed: int, iterations: int, samples: int, config: JevConfig) -> dict:
    state = make_seeded_state(seed)
    random_destroy, random_repair = make_random_vlns_selectors(seed)
    client = JevClient(config)
    selector = JevDestroySelector(
        JevSelector(
            client,
            random_destroy.select,
            task="destroy",
            question=JEV_DESTROY_QUESTION,
            objective=JEV_DESTROY_OBJECTIVE,
            min_confidence=config.min_confidence,
            state_serializer=_jev_state,
            candidate_serializer=_jev_destroy_candidate_context,
        )
    )
    selector.m20_run_seed = seed

    result = guided_vlns(
        state,
        selector,
        random_repair,
        iterations=iterations,
        capture_trace=True,
        destroy_min_stacks=2,
        destroy_max_stacks=2,
        destroy_include_non_adjacent=True,
        expected_value_samples=samples,
    )

    decisions = []
    for trace in result.trace:
        ev = trace.get("expected_value_landscape")
        if not ev:
            continue
        ranking = ev["ranking"]
        selected = trace["selected_destroy"]
        decisions.append(
            {
                "iteration": trace["iteration"],
                "state_key": ev["state_key"],
                "selected_candidate": selected,
                "selected_mean_ev": next(
                    e["mean"] for e in ev["entries"]
                    if e["candidate_id"] == selected
                ),
                "best_mean_ev": ranking["best_mean"],
                "worst_mean_ev": ranking["worst_mean"],
                "selected_rank": ranking["ranks"][selected],
                "selected_regret": ranking["regret"][selected],
                "selected_normalized_regret": ranking["normalized_regret"][selected],
                "top1": selected in ranking["tied_best"],
                "flat": ranking["flat"],
                "candidate_count": len(ev["entries"]),
                "samples": ev["samples"],
            }
        )

    return {
        "mode": "real-jev-random",
        "seed": seed,
        "iterations": result.iterations,
        "samples": samples,
        "destroy_min_stacks": 2,
        "destroy_max_stacks": 2,
        "destroy_include_non_adjacent": True,
        "decisions": decisions,
        "jev_stats": {
            "calls": client.stats.calls,
            "successes": client.stats.successes,
            "failures": client.stats.failures,
            "fallbacks": selector.selector.stats.fallbacks,
            "low_confidence": selector.selector.stats.low_confidence,
            "invalid_choice": selector.selector.stats.invalid_choice,
            "average_latency_ms": client.stats.average_latency_ms,
            "input_tokens": client.stats.total_input_tokens,
            "output_tokens": client.stats.total_output_tokens,
            "cost_usd": client.stats.total_cost_usd,
        },
        "final": {
            "feasible": result.evaluation.feasible,
            "moves": int(result.evaluation.metrics["moves"]),
            "projected_objective": result.best_projected_objective,
        },
    }


def summarize(documents: list[dict]) -> dict:
    decisions = [d for doc in documents for d in doc["decisions"]]
    if not decisions:
        raise RuntimeError("M20 produced no decision-level EV records")
    regrets = [d["selected_regret"] for d in decisions]
    normalized = [d["selected_normalized_regret"] for d in decisions]
    ranks = [d["selected_rank"] for d in decisions]
    return {
        "decisions": len(decisions),
        "top1_rate": sum(d["top1"] for d in decisions) / len(decisions),
        "mean_rank": statistics.mean(ranks),
        "median_rank": statistics.median(ranks),
        "mean_regret": statistics.mean(regrets),
        "median_regret": statistics.median(regrets),
        "mean_normalized_regret": statistics.mean(normalized),
        "median_normalized_regret": statistics.median(normalized),
        "flat_landscapes": sum(d["flat"] for d in decisions),
        "mean_candidate_count": statistics.mean(d["candidate_count"] for d in decisions),
    }


def render(result: dict) -> str:
    s = result["summary"]
    totals = result["jev_totals"]
    lines = [
        "# M20 — Real JEV Choice Quality vs Random-Repair Expected Value",
        "",
        "| Decisions | Top-1 | Mean rank | Median rank | Mean regret | Mean normalized regret | Flat landscapes |",
        "|---:|---:|---:|---:|---:|---:|---:|",
        f"| {s['decisions']} | {s['top1_rate']:.3f} | {s['mean_rank']:.2f} | "
        f"{s['median_rank']:.2f} | {s['mean_regret']:.3f} | "
        f"{s['mean_normalized_regret']:.3f} | {s['flat_landscapes']} |",
        "",
        "## Protocol",
        "",
        "- JEV chooses first; EV evaluation happens only after the JEV response.",
        "- Every legal K=2 non-adjacent Destroy candidate is evaluated.",
        f"- Random Repair samples per candidate: {result['protocol']['samples']}.",
        "- Greedy completion is deterministic.",
        "- Common random-number seeds are shared across candidates at each decision.",
        "- EV is never included in the JEV request.",
        "- Primary objective is expected final executable move count.",
        "",
        "## JEV telemetry",
        "",
        f"- Calls: {totals['calls']}",
        f"- Successful calls: {totals['successes']}",
        f"- Fallbacks: {totals['fallbacks']}",
        f"- Cost USD: {totals['cost_usd']:.6f}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, choices=(32, 64, 128), default=64)
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 4, 5])
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--destroy-min-stacks", type=int, default=2)
    parser.add_argument("--destroy-max-stacks", type=int, default=2)
    parser.add_argument("--destroy-include-non-adjacent", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--output", type=Path, default=Path("experiments/runs/m20-real-jev-ev"))
    args = parser.parse_args()

    if args.destroy_min_stacks != 2 or args.destroy_max_stacks != 2:
        parser.error("M20 requires fixed K=2 Destroy neighborhoods")
    if not args.destroy_include_non_adjacent:
        parser.error("M20 requires non-adjacent Destroy neighborhoods")

    config = JevConfig.from_environment()
    if not config.api_key:
        parser.error("No JEV API key configured")

    documents = [
        run_one(seed, args.iterations, args.samples, config)
        for seed in args.seeds
    ]
    result = {
        "protocol": {
            "mode": "real-jev-random",
            "samples": args.samples,
            "seeds": args.seeds,
            "iterations": args.iterations,
            "destroy_min_stacks": 2,
            "destroy_max_stacks": 2,
            "destroy_include_non_adjacent": True,
            "objective": "mean final executable moves after Random Repair + greedy completion",
            "ev_hidden_from_jev": True,
        },
        "summary": summarize(documents),
        "per_run": documents,
        "jev_totals": {
            key: sum(d["jev_stats"][key] for d in documents)
            for key in ("calls", "successes", "failures", "fallbacks", "low_confidence", "invalid_choice", "input_tokens", "output_tokens", "cost_usd")
        },
    }

    stem = args.output.with_suffix("") if args.output.suffix else args.output
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_suffix(".json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    stem.with_suffix(".md").write_text(render(result), encoding="utf-8")
    print(render(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
