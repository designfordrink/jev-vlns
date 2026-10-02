from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.search.destroy import apply_destroy, generate_destroy_candidates
from jev_vlns.search.repair import apply_repair, generate_repair_candidates
from jev_vlns.search.vlns import estimated_objective, projected_objective, random_vlns


def test_destroy_removes_top_containers_without_changing_move_count():
    state = make_seeded_state(42)
    candidate = generate_destroy_candidates(state)[0]
    partial = apply_destroy(state, candidate)
    assert len(partial.removed) == 1
    assert partial.state.moves == state.moves


def test_repair_restores_all_destroyed_containers():
    state = make_seeded_state(42)
    partial = apply_destroy(state, generate_destroy_candidates(state)[0])
    choices = generate_repair_candidates(partial)
    chosen = next(c for c in choices if c.container_id == partial.removed[0])
    restored = apply_repair(partial, [chosen])
    assert partial.removed[0] in {
        item for stack in restored.stacks for item in stack
    }


def test_estimated_objective_has_remaining_work_term():
    state = make_seeded_state(42)
    assert estimated_objective(state) == projected_objective(state)
    assert estimated_objective(state) >= state.moves


def test_random_vlns_is_reproducible():
    state = make_seeded_state(42)
    a = random_vlns(state, seed=9, iterations=20)
    b = random_vlns(state, seed=9, iterations=20)
    assert a.state == b.state
    assert a.evaluation == b.evaluation


def test_random_vlns_returns_a_complete_solution_when_greedy_can_finish():
    state = make_seeded_state(42)
    result = random_vlns(state, seed=9, iterations=20)
    assert result.state.is_complete
    assert result.evaluation.feasible
    assert result.best_projected_objective >= 0


def test_guided_vlns_random_selectors_is_reproducible():
    from jev_vlns.search.vlns import guided_vlns, make_random_vlns_selectors

    state = make_seeded_state(42)
    a = guided_vlns(state, *make_random_vlns_selectors(9), iterations=20)
    b = guided_vlns(state, *make_random_vlns_selectors(9), iterations=20)
    assert a.state == b.state
    assert a.evaluation == b.evaluation
