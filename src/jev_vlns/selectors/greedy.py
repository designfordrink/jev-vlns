from collections.abc import Sequence

from jev_vlns.container_stack.actions import apply_legal_action
from jev_vlns.container_stack.state import ContainerStackState
from jev_vlns.core.action import Action


class GreedySelector:
    """Container Stack baseline.

    Prefer immediate delivery. Otherwise move a container toward its own
    destination stack when possible, then prefer shorter destination stacks.
    """

    def select(
        self, state: ContainerStackState, candidates: Sequence[Action]
    ) -> Action:
        if not candidates:
            raise ValueError("cannot select from an empty candidate list")

        ranked = sorted(
            candidates,
            key=lambda action: (
                0 if action.kind == "deliver" else 1,
                self._move_score(state, action),
                action.id,
            ),
        )
        return ranked[0]

    @staticmethod
    def _move_score(state: ContainerStackState, action: Action) -> tuple:
        if action.kind == "deliver":
            return (0, 0, 0, 0)

        destination = int(action.payload["destination"])
        source = int(action.payload["source"])
        container_id = str(action.payload["container_id"])
        container = state.container(container_id)
        targets_own_destination = (
            state.stack_destinations[destination] == container.destination
        )
        projected = len(state.stacks[destination]) + 1

        return (
            0 if targets_own_destination else 1,
            projected,
            len(state.stacks[source]),
            destination,
        )
