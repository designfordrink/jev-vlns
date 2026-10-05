from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.search.execution import assert_executable_plan, greedy_plan


def test_greedy_plan_is_executable_from_initial_state():
    initial = make_seeded_state(42)
    plan = greedy_plan(initial)

    assert plan.final_state.is_complete
    assert plan.moves == plan.final_state.moves
    assert_executable_plan(initial, plan) == plan.final_state


def test_executable_plan_detects_tampered_final_state():
    from dataclasses import replace

    initial = make_seeded_state(42)
    plan = greedy_plan(initial)
    tampered = replace(plan, final_state=initial)

    try:
        assert_executable_plan(initial, tampered)
    except ValueError as exc:
        assert "final state" in str(exc)
    else:
        raise AssertionError("tampered final state was accepted")
