from .state import ContainerStackState


def render_text(state: ContainerStackState) -> str:
    """Render a compact deterministic text representation for debugging/replay."""

    lines = [f"moves={state.moves} delivered={state.delivered_count}/{len(state.containers)}"]
    for index, (destination, stack) in enumerate(
        zip(state.stack_destinations, state.stacks)
    ):
        contents = " ".join(stack) if stack else "·"
        lines.append(f"[{index}] target={destination} | {contents}")
    return "\n".join(lines)
