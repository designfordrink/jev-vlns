"""Independent replay validation for executable Container Stack plans."""

from dataclasses import dataclass
from collections.abc import Sequence

from jev_vlns.container_stack.actions import apply_legal_action, legal_actions
from jev_vlns.container_stack.state import ContainerStackState
from jev_vlns.core.action import Action


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    final_state: ContainerStackState
    actions_applied: int
    error: str | None = None


def replay_actions(
    initial_state: ContainerStackState,
    actions: Sequence[Action],
) -> ValidationResult:
    """Replay an executable action sequence from the initial state.

    This validator deliberately uses the public legal-action boundary instead
    of trusting action IDs or solver bookkeeping.
    """
    state = initial_state
    for index, action in enumerate(actions):
        try:
            state = apply_legal_action(state, action)
        except (TypeError, ValueError, KeyError) as exc:
            return ValidationResult(
                valid=False,
                final_state=state,
                actions_applied=index,
                error=f"action {index} ({action.id!r}) is illegal: {exc}",
            )

    return ValidationResult(
        valid=True,
        final_state=state,
        actions_applied=len(actions),
    )


def validate_complete_plan(
    initial_state: ContainerStackState,
    actions: Sequence[Action],
) -> ValidationResult:
    """Replay a plan and require a complete final state."""
    result = replay_actions(initial_state, actions)
    if not result.valid:
        return result
    if not result.final_state.is_complete:
        return ValidationResult(
            valid=False,
            final_state=result.final_state,
            actions_applied=result.actions_applied,
            error="plan replayed legally but did not reach a complete state",
        )
    return result


def assert_state_conservation(state: ContainerStackState) -> None:
    """Check that the state contains no duplicate or unknown containers."""
    known = {container.id for container in state.containers}
    present = [item for stack in state.stacks for item in stack]
    if len(present) != len(set(present)):
        raise ValueError("state contains duplicate containers")
    if not set(present) <= known:
        raise ValueError("state contains an unknown container")
    if not set(state.delivered) <= known:
        raise ValueError("delivered contains an unknown container")
    if set(present) & set(state.delivered):
        raise ValueError("a container is both present and delivered")


def legal_action_ids(state: ContainerStackState) -> tuple[str, ...]:
    """Return the complete legal-action boundary for diagnostics."""
    return tuple(action.id for action in legal_actions(state))
