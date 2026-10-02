from dataclasses import dataclass, asdict
from typing import Any

from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.jev.fake import FakeJevClient, HeuristicJevClient
from jev_vlns.selectors.jev import JevDestroySelector, JevRepairSelector, JevSelector
from jev_vlns.search.vlns import guided_vlns, make_random_vlns_selectors


@dataclass(frozen=True)
class BenchmarkResult:
    mode: str
    seed: int
    iterations: int
    feasible: bool
    moves: int
    projected_objective: float
    destroy_jev_calls: int
    repair_jev_calls: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _jev_state(state: Any) -> dict[str, Any]:
    if hasattr(state, "stacks"):
        return {
            "stacks": state.stacks,
            "destinations": state.stack_destinations,
            "moves": state.moves,
            "delivered": state.delivered,
        }
    return {"state": repr(state)}


def run_benchmark(
    *,
    seed: int = 42,
    iterations: int = 25,
    mode: str = "random-random",
) -> BenchmarkResult:
    """Run one controlled JEV/VLNS configuration.

    FakeJevClient and HeuristicJevClient make the experiment offline and reproducible.
    The heuristic client is a deterministic System-1 surrogate, not real JEV;
    replacing them with the real JEV client does not change the solver.
    """
    if mode not in {"random-random", "jev-random", "random-jev", "jev-jev", "heuristic-random", "random-heuristic", "heuristic-heuristic"}:
        raise ValueError(f"unknown benchmark mode: {mode}")

    state = make_seeded_state(seed)

    random_destroy, random_repair = make_random_vlns_selectors(seed)

    destroy_client = HeuristicJevClient() if mode.startswith("heuristic-") or mode == "heuristic-heuristic" else FakeJevClient(strategy="last")
    repair_client = HeuristicJevClient() if mode.endswith("-heuristic") or mode == "heuristic-heuristic" else FakeJevClient(strategy="last")

    if mode in {"jev-random", "jev-jev", "heuristic-random", "heuristic-heuristic"}:
        destroy_selector = JevDestroySelector(
            JevSelector(
                destroy_client,
                random_destroy.select,
                task="destroy",
                question="Choose the neighborhood to destroy.",
                state_serializer=_jev_state,
            )
        )
    else:
        destroy_selector = random_destroy

    if mode in {"random-jev", "jev-jev", "random-heuristic", "heuristic-heuristic"}:
        repair_selector = JevRepairSelector(
            JevSelector(
                repair_client,
                lambda state, candidates: random_repair.select_for_container(
                    state, candidates, candidates[0].container_id
                ),
                task="repair",
                question="Choose where to place this removed container.",
                state_serializer=_jev_state,
            )
        )
    else:
        repair_selector = random_repair

    result = guided_vlns(
        state,
        destroy_selector,
        repair_selector,
        iterations=iterations,
    )

    return BenchmarkResult(
        mode=mode,
        seed=seed,
        iterations=result.iterations,
        feasible=result.evaluation.feasible,
        moves=int(result.evaluation.metrics["moves"]),
        projected_objective=result.best_projected_objective,
        destroy_jev_calls=destroy_client.calls,
        repair_jev_calls=repair_client.calls,
    )


def run_matrix(
    *,
    seed: int = 42,
    iterations: int = 25,
) -> list[BenchmarkResult]:
    """Run the four controlled Destroy/Repair combinations."""
    return [
        run_benchmark(seed=seed, iterations=iterations, mode=mode)
        for mode in ("random-random", "jev-random", "random-jev", "jev-jev")
    ]


def run_extended_matrix(
    *,
    seed: int = 42,
    iterations: int = 25,
) -> list[BenchmarkResult]:
    """Run the original controls plus deterministic heuristic System-1 modes."""
    modes = (
        "random-random",
        "jev-random",
        "random-jev",
        "jev-jev",
        "heuristic-random",
        "random-heuristic",
        "heuristic-heuristic",
    )
    return [
        run_benchmark(seed=seed, iterations=iterations, mode=mode)
        for mode in modes
    ]
