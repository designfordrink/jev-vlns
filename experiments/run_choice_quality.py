"""Run a reproducible multi-seed M11 choice-quality experiment.

This is an offline experiment: HeuristicJEV is a surrogate, not real JEV.
The generated JSON contains per-run replay-derived choice metrics and the
Markdown report summarizes them by selector mode.
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
from jev_vlns.evaluation.benchmark import _jev_state
from jev_vlns.evaluation.choice_quality import choice_metrics, summarize_choice_metrics
from jev_vlns.evaluation.replay import replay_document
from jev_vlns.jev.fake import HeuristicJevClient
from jev_vlns.search.oracle import OracleDestroySelector
from jev_vlns.search.vlns import guided_vlns, make_random_vlns_selectors
from jev_vlns.selectors.jev import JevDestroySelector, JevSelector


MODES = ("random-random", "heuristic-random", "oracle-random")


def run_one(mode: str, seed: int, iterations: int) -> dict:
    state = make_seeded_state(seed)
    random_destroy, random_repair = make_random_vlns_selectors(seed)

    if mode == "random-random":
        destroy_selector = random_destroy
    elif mode == "oracle-random":
        destroy_selector = OracleDestroySelector()
    else:
        destroy_selector = JevDestroySelector(
            JevSelector(
                HeuristicJevClient(),
                random_destroy.select,
                task="destroy",
                question="Choose the neighborhood to destroy.",
                state_serializer=_jev_state,
            )
        )

    result = guided_vlns(
        state,
        destroy_selector,
        random_repair,
        iterations=iterations,
        capture_trace=True,
    )
    document = replay_document(
        result,
        mode=mode,
        seed=seed,
        iterations=iterations,
    )
    document["choice_metrics"] = choice_metrics(document.get("trace", []))
    return document


def render_report(result: dict) -> str:
    lines = [
        "# M11 — JEV Choice vs Local Landscape",
        "",
        "Offline multi-seed experiment. heuristic-random uses the "
        "HeuristicJEV surrogate; it is NOT real JEV.",
        "",
        "| Mode | Runs | Decisions | Top-1 rate | Mean rank | Mean regret | Normalized regret |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for mode, row in result["summary"].items():
        decisions = sum(
            r["decisions"] for r in result["per_run"] if str(r["mode"]) == mode
        )
        lines.append(
            f"| {mode} | {row['runs']} | {decisions:.0f} | "
            f"{row['top1_rate']:.3f} | {row['mean_rank']:.2f} | "
            f"{row['mean_regret']:.3f} | {row['mean_normalized_regret']:.3f} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- Top-1 is the fraction of decisions where the selected Destroy "
        "candidate has the best downstream Oracle score.",
        "- Mean rank is 1 for the best local choice.",
        "- Normalized regret is 0 for the best choice and 1 for the worst "
        "available choice in that iteration.",
        "- These are choice-quality metrics, not end-to-end solver-quality "
        "metrics.",
        "- Oracle is an upper control for local choice quality.",
        "- Random is a baseline; candidate counts can vary, so its Top-1 rate "
        "is not expected to equal one fixed constant.",
        "",
        "The experiment uses fixed seeds and identical iteration budgets across "
        "modes. Oracle scores are diagnostic only and are not passed to the "
        "selector.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the M11 choice-quality matrix.")
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=MODES,
        default=list(MODES),
    )
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 4, 5])
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("experiments/runs/m11-choice-quality"),
        help="Output stem; writes .json and .md",
    )
    args = parser.parse_args()

    documents = [
        run_one(mode, seed, args.iterations)
        for mode in args.modes
        for seed in args.seeds
    ]
    summary = summarize_choice_metrics(documents)
    result = {
        "protocol": {
            "modes": args.modes,
            "seeds": args.seeds,
            "iterations": args.iterations,
            "offline": True,
            "selector_note": "heuristic-random uses HeuristicJEV surrogate; no live JEV API",
        },
        **summary,
    }

    stem = args.output.with_suffix("") if args.output.suffix else args.output
    stem.parent.mkdir(parents=True, exist_ok=True)
    json_path = stem.with_suffix(".json")
    md_path = stem.with_suffix(".md")
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    md_path.write_text(render_report(result), encoding="utf-8")

    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    print(render_report(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
