from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.search.vlns import random_vlns


def test_neighborhood_size_changes_candidate_space_without_changing_protocol():
    state = make_seeded_state(42)
    k1 = random_vlns(state, seed=7, iterations=5, destroy_max_stacks=1)
    k3 = random_vlns(state, seed=7, iterations=5, destroy_max_stacks=3)
    assert k1.evaluation.feasible
    assert k3.evaluation.feasible
    assert k1.iterations == k3.iterations == 5
    assert k1.mean_destroy_candidates > 0
    assert k3.mean_destroy_candidates >= k1.mean_destroy_candidates


def test_neighborhood_size_comparison_is_reproducible():
    state = make_seeded_state(42)
    kwargs = dict(seed=7, iterations=10, destroy_min_stacks=1,
                  destroy_max_stacks=3, destroy_include_non_adjacent=True)
    a = random_vlns(state, **kwargs)
    b = random_vlns(state, **kwargs)
    assert a.state == b.state
    assert a.evaluation == b.evaluation
    assert a.iterations == b.iterations
    assert a.mean_destroy_candidates == b.mean_destroy_candidates


def test_zero_iteration_budget_is_reported_as_zero():
    state = make_seeded_state(42)
    result = random_vlns(state, seed=7, iterations=0, destroy_max_stacks=3)
    assert result.iterations == 0


def test_m18_comparison_script_produces_complete_rows():
    """The documented M18 command must run and emit every required field.

    The script is imported here because the suite previously exercised the
    library only, which is how the ``evaluation.moves`` attribute error
    reached a green CI run.
    """
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "compare_neighborhood_sizes",
        root / "experiments" / "compare_neighborhood_sizes.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    payload = module.run([1, 2], 5, 3, False)

    assert len(payload["results"]) == 6  # 2 seeds x K=1,2,3
    required = (
        "seed", "k", "iterations", "requested_iterations",
        "moves", "projected_objective", "feasible", "mean_destroy_candidates",
    )
    for row in payload["results"]:
        assert all(field in row for field in required)
        assert row["iterations"] == row["requested_iterations"] == 5
        assert isinstance(row["moves"], int)
    assert len(payload["paired_deltas"]) == 4  # 2 seeds x K=2,3
    assert module.render(payload)
