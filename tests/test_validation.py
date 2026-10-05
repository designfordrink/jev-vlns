from jev_vlns.container_stack.actions import legal_actions
from jev_vlns.container_stack.state import make_seeded_state
from jev_vlns.search.validation import (
    assert_state_conservation,
    validate_complete_plan,
)


def test_complete_plan_replay_is_independently_validated():
    state = make_seeded_state(42)

    # Greedily execute the same legal-action policy used by the environment.
    actions = []
    current = state
    for _ in range(1000):
        if current.is_complete:
            break
        candidates = legal_actions(current)
        assert candidates, "seeded state should be solvable by legal actions"
        action = candidates[0]
        actions.append(action)
        from jev_vlns.container_stack.actions import apply_legal_action
        current = apply_legal_action(current, action)

    result = validate_complete_plan(state, actions)

    assert result.valid
    assert result.final_state.is_complete
    assert result.actions_applied == len(actions)
    assert result.final_state.moves == len(actions)


def test_invalid_action_is_rejected_instead_of_trusted_by_id():
    state = make_seeded_state(42)
    action = legal_actions(state)[0]

    # Keep the ID but alter the payload. The validator must inspect legality,
    # not trust the identifier.
    from jev_vlns.core.action import Action
    tampered = Action(
        id=action.id,
        kind=action.kind,
        payload={**action.payload, "container_id": "C999"},
    )

    result = validate_complete_plan(state, [tampered])

    assert not result.valid
    assert "illegal" in result.error


def test_conservation_rejects_duplicate_container():
    state = make_seeded_state(42)
    from dataclasses import replace

    bad_stack = list(state.stacks[0])
    bad_stack.append(bad_stack[-1])
    bad = replace(
        state,
        stacks=(tuple(bad_stack),) + state.stacks[1:],
    )

    try:
        assert_state_conservation(bad)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate container was not rejected")
