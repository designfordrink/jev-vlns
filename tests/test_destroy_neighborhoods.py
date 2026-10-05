from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.search.destroy import apply_destroy, generate_destroy_candidates


def test_variable_destroy_includes_non_adjacent_pairs():
    state = make_seeded_state(42)
    candidates = generate_destroy_candidates(state, max_stacks=2)
    ids = {candidate.id for candidate in candidates}
    non_empty = [i for i, stack in enumerate(state.stacks) if stack]
    assert len(non_empty) >= 3
    assert f"stacks:{non_empty[0]},{non_empty[2]}" in ids


def test_variable_destroy_has_all_sizes_up_to_k():
    state = make_seeded_state(42)
    candidates = generate_destroy_candidates(state, max_stacks=3)
    sizes = {len(candidate.stack_indices) for candidate in candidates}
    assert sizes == {1, 2, 3}


def test_destroy_candidate_order_is_deterministic():
    state = make_seeded_state(42)
    a = generate_destroy_candidates(state, max_stacks=3)
    b = generate_destroy_candidates(state, max_stacks=3)
    assert a == b


def test_adjacent_only_mode_preserves_contiguous_neighborhoods():
    state = make_seeded_state(42)
    candidates = generate_destroy_candidates(
        state, max_stacks=2, include_non_adjacent=False
    )
    for candidate in candidates:
        if len(candidate.stack_indices) == 2:
            left, right = candidate.stack_indices
            assert right == left + 1


def test_destroy_rejects_invalid_neighborhood_bounds():
    state = make_seeded_state(42)
    try:
        generate_destroy_candidates(state, min_stacks=3, max_stacks=2)
    except ValueError as exc:
        assert "max_stacks" in str(exc)
    else:
        raise AssertionError("expected invalid neighborhood bounds to fail")


def test_destroy_of_larger_neighborhood_preserves_move_count_and_removes_exact_tops():
    state = make_seeded_state(42)
    candidate = generate_destroy_candidates(state, max_stacks=3)[-1]
    partial = apply_destroy(state, candidate)
    assert len(partial.removed) == len(candidate.stack_indices)
    assert partial.state.moves == state.moves
    for index, removed_id in zip(candidate.stack_indices, partial.removed):
        assert removed_id not in partial.state.stacks[index]
