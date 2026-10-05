from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.search.vlns import random_vlns


def test_neighborhood_size_changes_candidate_space_without_changing_protocol():
    state = make_seeded_state(42)
    k1 = random_vlns(state, seed=7, iterations=5, destroy_max_stacks=1)
    k3 = random_vlns(state, seed=7, iterations=5, destroy_max_stacks=3)
    assert k1.evaluation.feasible
    assert k3.evaluation.feasible
    assert k1.iterations == k3.iterations == 5


def test_neighborhood_size_comparison_is_reproducible():
    state = make_seeded_state(42)
    kwargs = dict(seed=7, iterations=10, destroy_min_stacks=1,
                  destroy_max_stacks=3, destroy_include_non_adjacent=True)
    a = random_vlns(state, **kwargs)
    b = random_vlns(state, **kwargs)
    assert a.state == b.state
    assert a.evaluation == b.evaluation
