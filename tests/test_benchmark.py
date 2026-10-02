from jev_vlns.evaluation.benchmark import run_benchmark, run_matrix


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
