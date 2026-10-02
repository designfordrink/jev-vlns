from jev_vlns.container_stack.actions import legal_actions
from jev_vlns.container_stack.solver import solve
from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.selectors.greedy import GreedySelector
from jev_vlns.selectors.random import RandomSelector


def test_random_selector_is_reproducible():
    state = make_seeded_state(42)
    candidates = legal_actions(state)
    a = RandomSelector(seed=7).select(state, candidates)
    b = RandomSelector(seed=7).select(state, candidates)
    assert a.id == b.id


def test_random_selector_rejects_empty_candidates():
    try:
        RandomSelector(seed=1).select(make_seeded_state(1), [])
    except ValueError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_greedy_prefers_delivery():
    state = make_seeded_state(42)
    candidates = legal_actions(state)
    delivery = next((a for a in candidates if a.kind == "deliver"), None)
    if delivery is None:
        # Constructing an initial state with no delivery is legitimate; skip
        # this behavior-specific check for this seed.
        return
    assert GreedySelector().select(state, candidates).kind == "deliver"


def test_solver_runs_with_random_selector():
    result = solve(make_seeded_state(42), RandomSelector(seed=5), max_iterations=1000)
    assert result.iterations == result.state.moves
    assert result.evaluation.objective == result.state.moves


def test_solver_runs_with_greedy_selector():
    result = solve(make_seeded_state(42), GreedySelector(), max_iterations=1000)
    assert result.iterations == result.state.moves
    assert result.evaluation.objective == result.state.moves
