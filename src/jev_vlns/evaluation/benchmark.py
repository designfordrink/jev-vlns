from dataclasses import dataclass, asdict
import json
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
    destroy_jev_cost_usd: float = 0.0

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


def _jev_destroy_candidate_context(state: Any, candidate: Any) -> str:
    """Serialize only the state-derived context relevant to one Destroy choice."""
    containers = {container.id: container for container in state.containers}
    affected_stacks = []
    for index in candidate.stack_indices:
        stack = state.stacks[index]
        top_id = stack[-1]
        exposed_id = stack[-2] if len(stack) >= 2 else None
        top = containers[top_id]
        exposed = containers[exposed_id] if exposed_id is not None else None
        affected_stacks.append(
            {
                "index": index,
                "destination": state.stack_destinations[index],
                "height_before": len(stack),
                "top": {
                    "id": top.id,
                    "destination": top.destination,
                    "priority": top.priority,
                },
                "exposed_after_destroy": (
                    {
                        "id": exposed.id,
                        "destination": exposed.destination,
                        "priority": exposed.priority,
                    }
                    if exposed is not None
                    else None
                ),
            }
        )
    return json.dumps(
        {
            "operation": "destroy_top",
            "affected_stacks": affected_stacks,
        },
        sort_keys=True,
    )


JEV_DESTROY_QUESTION = (
    "Choose exactly one legal destroy neighborhood.\n\n"
    "Goal: select the neighborhood most likely to reduce the final number "
    "of container moves after the removed containers are repaired and the "
    "arrangement is completed.\n\n"
    "How to reason:\n"
    "- A container is delivered when it is on top of the stack whose "
    "destination matches the container's destination.\n"
    "- Destroy removes the top container from each affected stack.\n"
    "- Removing a top container exposes the container immediately below it.\n"
    "- The removed containers are placed back during the repair phase on "
    "legal non-full stacks.\n"
    "- After repair, the solver may greedily complete the arrangement using "
    "the deterministic legal-action policy.\n"
    "- Consider stack destinations, container destinations, stack heights, "
    "priorities, and the containers affected by each candidate.\n"
    "- Prefer candidates that are likely to expose useful containers, reduce "
    "blocking, and create a promising arrangement for repair and completion.\n\n"
    "Do not invent actions outside the provided candidates. Choose exactly "
    "one candidate ID from the provided choices. Do not use future "
    "evaluations, Oracle scores, candidate rankings, or regret information."
)

JEV_DESTROY_OBJECTIVE = (
    "Minimize final total container moves after Random Repair and "
    "deterministic greedy completion."
)


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
        destroy_jev_cost_usd=client.stats.total_cost_usd,
    )