from jev_vlns.evaluation.benchmark import run_benchmark, run_matrix
from jev_vlns.search.oracle import OracleDestroySelector, OracleRepairSelector, best_repair_plan, destroy_landscape
from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.search.destroy import apply_destroy, generate_destroy_candidates


def test_benchmark_modes_are_reproducible():
    a = run_benchmark(seed=42, iterations=10, mode="jev-jev")
    b = run_benchmark(seed=42, iterations=10, mode="jev-jev")
    assert a == b


def test_benchmark_matrix_has_four_experiments():
    results = run_matrix(seed=42, iterations=10)
    assert [result.mode for result in results] == [
        "random-random",
        "jev-random",
        "random-jev",
        "jev-jev",
    ]
    assert all(result.feasible for result in results)


def test_jev_call_counts_match_enabled_side():
    rr = run_benchmark(seed=42, iterations=5, mode="random-random")
    jj = run_benchmark(seed=42, iterations=5, mode="jev-jev")
    assert rr.destroy_jev_calls == 0
    assert rr.repair_jev_calls == 0
    assert jj.destroy_jev_calls > 0
    assert jj.repair_jev_calls > 0


def test_invalid_mode_is_rejected():
    try:
        run_benchmark(mode="bad")
    except ValueError:
        pass
    else:
        raise AssertionError("expected invalid benchmark mode to fail")


def test_heuristic_system1_modes_are_reproducible():
    a = run_benchmark(seed=42, iterations=10, mode="heuristic-heuristic")
    b = run_benchmark(seed=42, iterations=10, mode="heuristic-heuristic")
    assert a == b
    assert a.feasible
    assert a.destroy_jev_calls > 0
    assert a.repair_jev_calls > 0


def test_heuristic_repair_is_selective():
    result = run_benchmark(seed=42, iterations=10, mode="random-heuristic")
    assert result.feasible
    assert result.repair_jev_calls > 0


def test_oracle_finds_a_legal_repair_plan():
    state = make_seeded_state(42)
    destroy = generate_destroy_candidates(state)[0]
    partial = apply_destroy(state, destroy)
    plan = best_repair_plan(partial)
    assert len(plan.choices) == len(partial.removed)
    assert plan.score >= 0


def test_oracle_landscape_scores_every_destroy_candidate():
    state = make_seeded_state(42)
    candidates = generate_destroy_candidates(state)
    landscape = destroy_landscape(state, candidates)
    assert len(landscape) == len(candidates)
    assert all(entry.candidate.id == candidate.id for entry, candidate in zip(landscape, candidates))


def test_oracle_modes_are_reproducible_and_feasible():
    for mode in ("oracle-random", "random-oracle", "oracle-oracle"):
        a = run_benchmark(seed=42, iterations=10, mode=mode)
        b = run_benchmark(seed=42, iterations=10, mode=mode)
        assert a == b
        assert a.feasible
