"""Run M21: controlled JEV state-representation diagnostics."""

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
from jev_vlns.evaluation.benchmark import JEV_DESTROY_OBJECTIVE, JEV_DESTROY_QUESTION
from jev_vlns.evaluation.context_variants import context_variant_names, serializers_for_variant
from jev_vlns.jev.client import JevClient
from jev_vlns.jev.config import JevConfig
from jev_vlns.search.vlns import guided_vlns, make_random_vlns_selectors
from jev_vlns.selectors.jev import JevDestroySelector, JevSelector


def run_one(variant, seed, iterations, samples, config):
    state_serializer, candidate_serializer = serializers_for_variant(variant)
    state = make_seeded_state(seed)
    random_destroy, random_repair = make_random_vlns_selectors(seed)
    client = JevClient(config)
    selector = JevDestroySelector(JevSelector(
        client,
        random_destroy.select,
        task="destroy",
        question=JEV_DESTROY_QUESTION,
        objective=JEV_DESTROY_OBJECTIVE,
        min_confidence=config.min_confidence,
        state_serializer=state_serializer,
        candidate_serializer=candidate_serializer,
    ))
    selector.m20_run_seed = seed
    result = guided_vlns(
        state, selector, random_repair,
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
        decisions.append({
            "iteration": trace["iteration"],
            "selected_candidate": selected,
            "selected_rank": ranking["ranks"][selected],
            "selected_regret": ranking["regret"][selected],
            "selected_normalized_regret": ranking["normalized_regret"][selected],
            "top1": selected in ranking["tied_best"],
            "flat": ranking["flat"],
            "candidate_count": len(ev["entries"]),
        })
    return {
        "variant": variant,
        "seed": seed,
        "iterations": result.iterations,
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


def summarize(runs):
    decisions = [d for run in runs for d in run["decisions"]]
    if not decisions:
        raise RuntimeError("M21 produced no decision records")
    return {
        "decisions": len(decisions),
        "top1_rate": sum(d["top1"] for d in decisions) / len(decisions),
        "mean_rank": statistics.mean(d["selected_rank"] for d in decisions),
        "median_rank": statistics.median(d["selected_rank"] for d in decisions),
        "mean_regret": statistics.mean(d["selected_regret"] for d in decisions),
        "mean_normalized_regret": statistics.mean(d["selected_normalized_regret"] for d in decisions),
        "flat_landscapes": sum(d["flat"] for d in decisions),
    }


def render(result):
    lines = [
        "# M21 — JEV State Representation / Context Diagnostics",
        "",
        "| Variant | Decisions | Top-1 | Mean rank | Median rank | Mean regret | Normalized regret | Fallbacks | Cost USD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant, data in result["variants"].items():
        s = data["summary"]
        t = data["telemetry"]
        lines.append(
            f"| {variant} | {s['decisions']} | {s['top1_rate']:.3f} | "
            f"{s['mean_rank']:.2f} | {s['median_rank']:.2f} | "
            f"{s['mean_regret']:.3f} | {s['mean_normalized_regret']:.3f} | "
            f"{t['fallbacks']} | {t['cost_usd']:.6f} |"
        )
    lines += [
        "",
        "## Frozen protocol",
        "",
        "- Only JEV state/candidate serialization changes.",
        "- Same model, question, objective, K=2 candidate set, fallback and confidence threshold.",
        "- Same Random Repair + greedy completion.",
        "- Same M20 EV evaluator and N=64 sample schedule.",
        "- EV/Oracle information is never sent to JEV.",
        "- No prompt tuning.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, choices=(32, 64, 128), default=64)
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 4, 5])
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--output", type=Path, default=Path("experiments/runs/m21-context-diagnostics"))
    args = parser.parse_args()

    config = JevConfig.from_environment()
    if not config.api_key:
        parser.error("No JEV API key configured")

    variants = {}
    for variant in context_variant_names():
        runs = [run_one(variant, seed, args.iterations, args.samples, config) for seed in args.seeds]
        variants[variant] = {
            "summary": summarize(runs),
            "telemetry": {
                key: sum(r["jev_stats"][key] for r in runs)
                for key in ("calls", "successes", "failures", "fallbacks",
                            "low_confidence", "invalid_choice",
                            "input_tokens", "output_tokens", "cost_usd")
            },
            "per_run": runs,
        }

    result = {
        "protocol": {
            "name": "M21-state-representation",
            "variants": list(context_variant_names()),
            "seeds": args.seeds,
            "iterations": args.iterations,
            "samples": args.samples,
            "destroy_min_stacks": 2,
            "destroy_max_stacks": 2,
            "destroy_include_non_adjacent": True,
            "objective": "mean final executable moves after Random Repair + greedy completion",
            "ev_hidden_from_jev": True,
            "prompt_unchanged": True,
        },
        "variants": variants,
    }
    stem = args.output.with_suffix("") if args.output.suffix else args.output
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_suffix(".json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    stem.with_suffix(".md").write_text(render(result), encoding="utf-8")
    print(render(result), end="")


if __name__ == "__main__":
    main()
