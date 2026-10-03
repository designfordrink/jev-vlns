"""Generate a deterministic replay artifact for one JEV/VLNS run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.evaluation.replay import replay_document, write_replay_html, write_replay_json
from jev_vlns.evaluation.benchmark import _jev_state
from jev_vlns.jev.fake import FakeJevClient, HeuristicJevClient
from jev_vlns.search.oracle import OracleDestroySelector
from jev_vlns.search.vlns import guided_vlns, make_random_vlns_selectors
from jev_vlns.selectors.jev import JevDestroySelector, JevSelector


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a JEV/VLNS replay.")
    parser.add_argument("--mode", choices=("random-random", "heuristic-random", "oracle-random"),
                        default="random-random")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--iterations", type=int, default=25)
    parser.add_argument("--output", type=Path, default=Path("experiments/runs/replay"))
    args = parser.parse_args()

    state = make_seeded_state(args.seed)
    random_destroy, random_repair = make_random_vlns_selectors(args.seed)

    if args.mode == "random-random":
        destroy_selector = random_destroy
    elif args.mode == "oracle-random":
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
        iterations=args.iterations,
        capture_trace=True,
    )
    document = replay_document(result, mode=args.mode, seed=args.seed, iterations=args.iterations)
    stem = args.output
    if stem.suffix:
        stem = stem.with_suffix("")
    write_replay_json(document, str(stem) + ".json")
    write_replay_html(document, str(stem) + ".html")
    print(f"JSON: {stem}.json")
    print(f"HTML: {stem}.html")
    print(f"Final moves: {document['final']['moves']}")
    print(f"Feasible: {document['final']['feasible']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
