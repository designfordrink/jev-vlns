"""Run M12: real JEV Destroy choice quality vs the M11 local landscape.

Requires a configured JEV API key. The protocol is intentionally identical to
M11: fixed seeds, fixed iteration budget, Random Repair, and Oracle scores used
only after each decision for offline diagnostics.

Example:
    python experiments/run_real_jev_choice_quality.py --seeds 1 2 3 4 5 --iterations 50
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

from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.evaluation.benchmark import (
    JEV_DESTROY_OBJECTIVE,
    JEV_DESTROY_QUESTION,
    _jev_destroy_candidate_context,
    _jev_state,
)
from jev_vlns.evaluation.choice_quality import choice_metrics, summarize_choice_metrics
from jev_vlns.evaluation.replay import replay_document
from jev_vlns.jev.client import JevClient
from jev_vlns.jev.config import JevConfig
from jev_vlns.search.vlns import guided_vlns, make_random_vlns_selectors
from jev_vlns.selectors.jev import JevDestroySelector, JevSelector


def run_one(seed: int, iterations: int, config: JevConfig) -> dict:
    if not config.api_key:
        raise RuntimeError(
            "M12 requires JEV_API_KEY, TYPESAFE_API_KEY, or OPENROUTER_API_KEY"
        )

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

    result = guided_vlns(
        state,
        selector,
        random_repair,
        iterations=iterations,
        capture_trace=True,
    )
    document = replay_document(
        result,
        mode="real-jev-random",
        seed=seed,
        iterations=iterations,
    )
    document["choice_metrics"] = choice_metrics(document.get("trace", []))
    document["jev_stats"] = {
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
    }
    return document


def render_report(result: dict) -> str:
    lines = [
        "# M12 — Real JEV Choice Quality",
        "",
        "Live JEV Destroy selector with Random Repair, evaluated with the same "
        "local Oracle landscape used by M11.",
        "",
        "| Mode | Runs | Decisions | Top-1 rate | Mean rank | Mean regret | Normalized regret | JEV calls | Fallbacks | Cost USD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode, row in result["summary"].items():
        runs = [r for r in result["per_run"] if str(r["mode"]) == mode]
        decisions = sum(r.get("decisions", 0.0) for r in runs)
        calls = sum(r.get("jev_stats", {}).get("calls", 0) for r in runs)
        fallbacks = sum(r.get("jev_stats", {}).get("fallbacks", 0) for r in runs)
        cost = sum(r.get("jev_stats", {}).get("cost_usd", 0.0) for r in runs)
        lines.append(
            f"| {mode} | {row['runs']} | {decisions:.0f} | "
            f"{row['top1_rate']:.3f} | {row['mean_rank']:.2f} | "
            f"{row['mean_regret']:.3f} | {row['mean_normalized_regret']:.3f} | "
            f"{calls} | {fallbacks} | {cost:.6f} |"
        )

    lines += [
        "",
        "## Method",
        "",
        "- Same seeds and iteration budget as M11.",
        "- Random Repair is fixed; only Destroy selection is live JEV.",
        "- Legal candidates are generated locally before JEV is called.",
        "- Oracle downstream scores are computed only after the decision and are "
        "never sent to JEV.",
        "- JEV may only select one of the locally generated candidate IDs.",
        "- Fallbacks are reported separately and must not be described as "
        "successful JEV decisions.",
        "",
        "## Interpretation",
        "",
        "Compare this result with the M11 random-random, heuristic-random and "
        "oracle-random controls. M12 measures local choice quality; it does "
        "not by itself establish better end-to-end VLNS performance.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the M12 real-JEV choice-quality experiment.")
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 4, 5])
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--destroy-min-stacks", type=int, default=2)
    parser.add_argument("--destroy-max-stacks", type=int, default=2)
    parser.add_argument("--destroy-include-non-adjacent", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("experiments/runs/m12-real-jev-choice-quality"),
        help="Output stem; writes .json and .md",
    )
    args = parser.parse_args()

    if args.destroy_min_stacks != 2 or args.destroy_max_stacks != 2:
        parser.error("M19 requires fixed K=2 Destroy neighborhoods")

    config = JevConfig.from_environment()
    if not config.api_key:
        parser.error(
            "No JEV API key configured. Set JEV_API_KEY, TYPESAFE_API_KEY, "
            "or OPENROUTER_API_KEY."
        )

    documents = [
        run_one(seed, args.iterations, config)
        for seed in args.seeds
    ]
    summary = summarize_choice_metrics(documents)
    result = {
        "protocol": {
            "mode": "real-jev-random",
            "seeds": args.seeds,
            "iterations": args.iterations,
            "offline": False,
            "model": config.model,
            "base_url": config.base_url,
            "oracle_diagnostic_only": True,
            "repair_selector": "random",
        },
        **summary,
    }

    # Aggregate live-JEV telemetry without exposing credentials.
    result["jev_totals"] = {
        "calls": sum(d["jev_stats"]["calls"] for d in documents),
        "successes": sum(d["jev_stats"]["successes"] for d in documents),
        "failures": sum(d["jev_stats"]["failures"] for d in documents),
        "fallbacks": sum(d["jev_stats"]["fallbacks"] for d in documents),
        "low_confidence": sum(d["jev_stats"]["low_confidence"] for d in documents),
        "invalid_choice": sum(d["jev_stats"]["invalid_choice"] for d in documents),
        "input_tokens": sum(d["jev_stats"]["input_tokens"] for d in documents),
        "output_tokens": sum(d["jev_stats"]["output_tokens"] for d in documents),
        "cost_usd": sum(d["jev_stats"]["cost_usd"] for d in documents),
    }

    stem = args.output.with_suffix("") if args.output.suffix else args.output
    stem.parent.mkdir(parents=True, exist_ok=True)
    json_path = stem.with_suffix(".json")
    md_path = stem.with_suffix(".md")
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_report(result), encoding="utf-8")

    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    print(render_report(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
