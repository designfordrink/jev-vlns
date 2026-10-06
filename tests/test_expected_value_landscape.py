import math

from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.search.destroy import generate_destroy_candidates
from jev_vlns.search.expected_value import (
    CandidateEV,
    expected_value_landscape,
    rank_landscape,
)


def test_m20_is_reproducible_and_does_not_mutate_state():
    state = make_seeded_state(1)
    before = state
    candidates = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )
    a = expected_value_landscape(state, candidates[:3], run_seed=1, iteration=0, samples=32)
    b = expected_value_landscape(state, candidates[:3], run_seed=1, iteration=0, samples=32)
    assert state == before
    assert a == b


def test_m20_is_invariant_to_candidate_evaluation_order():
    state = make_seeded_state(2)
    candidates = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )[:4]
    forward = expected_value_landscape(state, candidates, run_seed=2, iteration=3, samples=32)
    reverse = expected_value_landscape(
        state, list(reversed(candidates)), run_seed=2, iteration=3, samples=32
    )
    by_id = {e.candidate.id: e for e in reverse.entries}
    for entry in forward.entries:
        assert entry == by_id[entry.candidate.id]


def test_m20_candidate_isolation_matches_standalone_evaluation():
    state = make_seeded_state(3)
    candidates = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )[:3]
    all_entries = expected_value_landscape(
        state, candidates, run_seed=3, iteration=4, samples=32
    )
    one_entry = expected_value_landscape(
        state, [candidates[1]], run_seed=3, iteration=4, samples=32
    )
    assert all_entries.entries[1] == one_entry.entries[0]


def test_m20_objective_is_mean_of_executable_final_moves():
    state = make_seeded_state(4)
    candidate = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )[0]
    landscape = expected_value_landscape(
        state, [candidate], run_seed=4, iteration=5, samples=32
    )
    entry = landscape.entries[0]
    assert entry.complete
    assert all(isinstance(value, int) and value >= 0 for value in entry.final_moves)
    assert entry.mean == sum(entry.final_moves) / len(entry.final_moves)


def test_m20_prefix_consistency_across_sample_sizes():
    state = make_seeded_state(5)
    candidates = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )[:2]
    n32 = expected_value_landscape(state, candidates, run_seed=5, iteration=6, samples=32)
    n64 = expected_value_landscape(state, candidates, run_seed=5, iteration=6, samples=64)
    n128 = expected_value_landscape(state, candidates, run_seed=5, iteration=6, samples=128)
    for i in range(2):
        # The index-aligned stream is the authoritative prefix check: it keeps
        # failed samples in place, so it holds even where final_moves (successes
        # only) would shift positions.
        assert n64.entries[i].outcomes[:32] == n32.entries[i].outcomes
        assert n128.entries[i].outcomes[:64] == n64.entries[i].outcomes
        assert n32.entries[i].sample_seeds == n64.entries[i].sample_seeds[:32]
        assert len(n64.entries[i].outcomes) == 64


def test_m20_outcomes_stream_stays_aligned_with_seeds():
    """A failed sample must not shift later outcomes in the stored stream."""
    state = make_seeded_state(11)
    candidates = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )
    landscape = expected_value_landscape(
        state, candidates, run_seed=11, iteration=0, samples=64
    )
    for entry in landscape.entries:
        assert len(entry.outcomes) == 64
        assert len(entry.sample_seeds) == 64
        assert entry.feasible_count == sum(v is not None for v in entry.outcomes)
        assert entry.error_count == sum(v is None for v in entry.outcomes)
        assert entry.final_moves == tuple(
            v for v in entry.outcomes if v is not None
        )


def test_m20_ranking_handles_flat_landscape():
    state = make_seeded_state(6)
    candidates = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )[:2]
    base = expected_value_landscape(state, candidates[:1], run_seed=6, iteration=7, samples=32)
    first = base.entries[0]
    tied = CandidateEV(
        candidate=candidates[1],
        sample_seeds=first.sample_seeds,
        final_moves=first.final_moves,
        mean=first.mean,
        median=first.median,
        std=first.std,
        minimum=first.minimum,
        maximum=first.maximum,
        p10=first.p10,
        p90=first.p90,
        feasible_count=first.feasible_count,
        error_count=first.error_count,
    )
    landscape = type(base)(
        state_key=base.state_key,
        samples=base.samples,
        entries=(first, tied),
    )
    ranked = rank_landscape(landscape)
    assert ranked["flat"]
    assert ranked["tied_best"] == sorted([candidates[0].id, candidates[1].id])
    assert all(value == 0.0 for value in ranked["normalized_regret"].values())


def test_m20_rejects_invalid_sample_count():
    state = make_seeded_state(7)
    candidate = generate_destroy_candidates(
        state, min_stacks=2, max_stacks=2, include_non_adjacent=True
    )[0]
    try:
        expected_value_landscape(state, [candidate], run_seed=7, iteration=0, samples=16)
    except ValueError as exc:
        assert "32, 64, or 128" in str(exc)
    else:
        raise AssertionError("expected invalid sample count to fail")
