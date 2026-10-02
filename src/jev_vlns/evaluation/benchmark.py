from dataclasses import dataclass, asdict
from typing import Any

from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.jev.client import JevClient
from jev_vlns.jev.config import JevConfig
from jev_vlns.jev.fake import FakeJevClient, HeuristicJevClient
from jev_vlns.selectors.jev import JevDestroySelector, JevRepairSelector, JevSelector
from jev_vlns.search.oracle import OracleDestroySelector, OracleRepairSelector
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
    mean_destroy_candidates: float
    mean_repair_candidates: float
    mean_destroy_regret: float
    mean_repair_regret: float
    destroy_jev_fallbacks: int = 0
    destroy_jev_average_latency_ms: float = 0.0
    destroy_jev_input_tokens: int = 0
    destroy_jev_output_tokens: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _jev_state(state: Any) -> dict[str, Any]:
    if hasattr(state, "stacks"):
        containers = {
            container.id: {
                "destination": container.destination,
                "priority": container.priority,
            }
            for container in state.containers
        }
        return {
            "stacks": state.stacks,
            "destinations": state.stack_destinations,
            "containers": containers,
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
    if mode not in {
        "random-random", "jev-random", "random-jev", "jev-jev",
        "heuristic-random", "random-heuristic", "heuristic-heuristic",
        "oracle-random", "random-oracle", "oracle-oracle",
    }:
        raise ValueError(f"unknown benchmark mode: {mode}")

    state = make_seeded_state(seed)

    random_destroy, random_repair = make_random_vlns_selectors(seed)

    destroy_client = HeuristicJevClient() if mode.startswith("heuristic-") or mode == "heuristic-heuristic" else FakeJevClient(strategy="last")
    repair_client = HeuristicJevClient() if mode.endswith("-heuristic") or mode == "heuristic-heuristic" else FakeJevClient(strategy="last")

    if mode in {"oracle-random", "oracle-oracle"}:
        destroy_selector = OracleDestroySelector()
    elif mode in {"jev-random", "jev-jev", "heuristic-random", "heuristic-heuristic"}:
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

    if mode in {"oracle-oracle", "random-oracle"}:
        repair_selector = OracleRepairSelector()
    elif mode in {"random-jev", "jev-jev", "random-heuristic", "heuristic-heuristic"}:
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
        mean_destroy_candidates=result.mean_destroy_candidates,
        mean_repair_candidates=result.mean_repair_candidates,
        mean_destroy_regret=result.mean_destroy_regret,
        mean_repair_regret=result.mean_repair_regret,
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
        "oracle-random",
        "random-oracle",
        "oracle-oracle",
    )
    return [
        run_benchmark(seed=seed, iterations=iterations, mode=mode)
        for mode in modes
    ]


def run_real_jev_destroy_benchmark(
    *,
    seed: int = 42,
    iterations: int = 25,
    config: JevConfig | None = None,
) -> BenchmarkResult:
    """Run the M9 experiment: real JEV Destroy + Random Repair.

    This function intentionally requires a configured JEV API key. It never
    silently converts a missing key into a baseline result.
    """
    config = config or JevConfig.from_environment()
    if not config.api_key:
        raise RuntimeError(
            "M9 requires JEV_API_KEY, TYPESAFE_API_KEY, or OPENROUTER_API_KEY"
        )

    state = make_seeded_state(seed)
    random_destroy, random_repair = make_random_vlns_selectors(seed)
    client = JevClient(config)
    selector = JevDestroySelector(
        JevSelector(
            client,
            random_destroy.select,
            task="destroy",
            question=(
                "Choose which legal neighborhood to destroy before repair. "
                "Prefer the neighborhood that is most likely to reduce the "
                "future number of total container moves. Choose exactly one "
                "candidate from the provided criteria."
            ),
            objective="minimize total moves after deterministic greedy repair",
            min_confidence=config.min_confidence,
            state_serializer=_jev_state,
        )
    )

    result = guided_vlns(
        state,
        selector,
        random_repair,
        iterations=iterations,
    )
    return BenchmarkResult(
        mode="real-jev-random",
        seed=seed,
        iterations=result.iterations,
        feasible=result.evaluation.feasible,
        moves=int(result.evaluation.metrics["moves"]),
        projected_objective=result.best_projected_objective,
        destroy_jev_calls=client.stats.calls,
        repair_jev_calls=0,
        mean_destroy_candidates=result.mean_destroy_candidates,
        mean_repair_candidates=result.mean_repair_candidates,
        mean_destroy_regret=result.mean_destroy_regret,
        mean_repair_regret=result.mean_repair_regret,
        destroy_jev_fallbacks=selector.selector.stats.fallbacks,
        destroy_jev_average_latency_ms=client.stats.average_latency_ms,
        destroy_jev_input_tokens=client.stats.total_input_tokens,
        destroy_jev_output_tokens=client.stats.total_output_tokens,
    )