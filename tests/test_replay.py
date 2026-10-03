from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.evaluation.replay import replay_document, render_replay_html
from jev_vlns.search.vlns import guided_vlns, make_random_vlns_selectors

def test_replay_capture_does_not_change_solver_result():
    state = make_seeded_state(42)
    a = guided_vlns(state, *make_random_vlns_selectors(9), iterations=10)
    b = guided_vlns(state, *make_random_vlns_selectors(9), iterations=10, capture_trace=True)
    assert a.state == b.state
    assert a.evaluation == b.evaluation
    assert a.best_projected_objective == b.best_projected_objective
    assert len(b.trace) == 10

def test_replay_document_has_step_level_decision_evidence():
    state = make_seeded_state(42)
    result = guided_vlns(state, *make_random_vlns_selectors(9), iterations=3, capture_trace=True)
    document = replay_document(result, mode="random-random", seed=42, iterations=3)
    assert document["schema_version"] == 1
    assert len(document["trace"]) == 3
    step = document["trace"][0]
    assert step["before"]["stacks"]
    assert step["destroy_candidates"]
    assert step["selected_destroy"]
    assert "destroy_scores" in step
    assert "selected_repairs" in step
    assert "accepted" in step

def test_replay_html_is_self_contained():
    state = make_seeded_state(42)
    result = guided_vlns(state, *make_random_vlns_selectors(9), iterations=1, capture_trace=True)
    html = render_replay_html(replay_document(result, mode="random-random", seed=42, iterations=1))
    assert "<html" in html
    assert "Iteration 0" in html
    assert "Destroy candidates" in html
