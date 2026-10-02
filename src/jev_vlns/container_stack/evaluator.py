from jev_vlns.core.evaluator import Evaluation

from .state import ContainerStackState


def evaluate(state: ContainerStackState) -> Evaluation:
    """Evaluate feasibility and the MVP objective: total moves."""

    feasible = state.is_complete
    blocked_containers = sum(max(0, len(stack) - 1) for stack in state.stacks)
    max_height = max((len(stack) for stack in state.stacks), default=0)
    total_items = sum(len(stack) for stack in state.stacks)

    metrics = {
        "moves": state.moves,
        "delivered_count": state.delivered_count,
        "remaining_count": state.remaining_count,
        "blocked_containers": blocked_containers,
        "max_stack_height": max_height,
        "average_stack_height": (
            total_items / len(state.stacks) if state.stacks else 0.0
        ),
    }
    return Evaluation(
        feasible=feasible,
        objective=float(state.moves),
        metrics=metrics,
    )
