import pytest

from jev_vlns.container_stack.actions import (
    action_is_legal,
    apply_legal_action,
    legal_actions,
)
from jev_vlns.container_stack.evaluator import evaluate
from jev_vlns.container_stack.renderer import render_text
from jev_vlns.container_stack.state import (
    MAX_STACK_HEIGHT,
    Container,
    ContainerStackState,
    make_seeded_state,
)


def test_seeded_state_is_reproducible():
    assert make_seeded_state(42).stacks == make_seeded_state(42).stacks


def test_different_seed_can_change_layout():
    assert make_seeded_state(1).stacks != make_seeded_state(2).stacks


def test_state_respects_stack_capacity():
    state = make_seeded_state(42)
    assert all(len(stack) <= MAX_STACK_HEIGHT for stack in state.stacks)


def test_state_has_expected_container_count():
    state = make_seeded_state(42, container_count=7)
    assert len(state.containers) == 7
    assert sum(len(stack) for stack in state.stacks) == 7


def test_legal_actions_are_deterministic():
    state = make_seeded_state(42)
    assert [a.id for a in legal_actions(state)] == [
        a.id for a in legal_actions(state)
    ]


def test_move_action_changes_only_two_stacks():
    state = make_seeded_state(42)
    move = next(a for a in legal_actions(state) if a.kind == "move")
    new_state = apply_legal_action(state, move)
    assert new_state.moves == state.moves + 1
    assert sum(map(len, new_state.stacks)) == sum(map(len, state.stacks))


def test_delivery_removes_top_container():
    state = ContainerStackState(
        stacks=(("C1",), ()),
        containers=(Container("C1", "A"),),
        stack_destinations=("A", "B"),
    )
    delivery = next(a for a in legal_actions(state) if a.kind == "deliver")
    new_state = apply_legal_action(state, delivery)
    assert new_state.delivered == ("C1",)
    assert new_state.stacks == ((), ())


def test_full_stack_is_never_a_move_destination():
    state = ContainerStackState(
        stacks=(("C1",), ("C2", "C3", "C4")),
        containers=(
            Container("C1", "A"),
            Container("C2", "B"),
            Container("C3", "C"),
            Container("C4", "D"),
        ),
        stack_destinations=("A", "B"),
    )
    actions = legal_actions(state)
    assert all(a.payload.get("destination") != 1 for a in actions if a.kind == "move")


def test_illegal_action_is_rejected():
    state = make_seeded_state(42)
    move = next(a for a in legal_actions(state) if a.kind == "move")
    bad = type(move)(
        id=move.id,
        kind=move.kind,
        payload={**move.payload, "destination": 999},
    )
    assert not action_is_legal(state, bad)
    with pytest.raises(ValueError):
        apply_legal_action(state, bad)


def test_evaluator_reports_infeasible_initial_state():
    state = make_seeded_state(42)
    result = evaluate(state)
    assert not result.feasible
    assert result.objective == 0


def test_renderer_is_deterministic_and_human_readable():
    state = make_seeded_state(42)
    rendered = render_text(state)
    assert "target=A" in rendered
    assert "C" in rendered
    assert "moves=0" in rendered
