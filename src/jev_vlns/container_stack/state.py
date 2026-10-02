from dataclasses import dataclass
import random
from typing import Iterable


MAX_STACK_HEIGHT = 3
DEFAULT_STACK_COUNT = 5


@dataclass(frozen=True)
class Container:
    id: str
    destination: str
    priority: int = 1


@dataclass(frozen=True)
class ContainerStackState:
    """Immutable Container Stack board.

    Each stack has a destination label. A container can be delivered when it is
    on top of the stack whose destination matches the container destination.
    """

    stacks: tuple[tuple[str, ...], ...]
    containers: tuple[Container, ...]
    stack_destinations: tuple[str, ...]
    moves: int = 0
    delivered: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(self.stacks) != len(self.stack_destinations):
            raise ValueError("stacks and stack_destinations must have equal length")
        if any(len(stack) > MAX_STACK_HEIGHT for stack in self.stacks):
            raise ValueError("stack exceeds MAX_STACK_HEIGHT")
        ids = {container.id for container in self.containers}
        present = {item for stack in self.stacks for item in stack}
        if not present <= ids:
            raise ValueError("state contains an unknown container")
        if set(self.delivered) - ids:
            raise ValueError("delivered contains an unknown container")

    @property
    def delivered_count(self) -> int:
        return len(self.delivered)

    @property
    def remaining_count(self) -> int:
        return len(self.containers) - self.delivered_count

    @property
    def is_complete(self) -> bool:
        return self.remaining_count == 0

    def container(self, container_id: str) -> Container:
        for item in self.containers:
            if item.id == container_id:
                return item
        raise KeyError(container_id)

    def stack_height(self, index: int) -> int:
        return len(self.stacks[index])

    def with_stacks(
        self,
        stacks: tuple[tuple[str, ...], ...],
        *,
        moves: int | None = None,
        delivered: tuple[str, ...] | None = None,
    ) -> "ContainerStackState":
        return ContainerStackState(
            stacks=stacks,
            containers=self.containers,
            stack_destinations=self.stack_destinations,
            moves=self.moves if moves is None else moves,
            delivered=self.delivered if delivered is None else delivered,
        )


def make_seeded_state(
    seed: int,
    *,
    container_count: int = 10,
    stack_destinations: tuple[str, ...] = ("A", "B", "C", "D", "E"),
) -> ContainerStackState:
    """Create a deterministic, capacity-respecting initial state."""

    if container_count < 1:
        raise ValueError("container_count must be positive")
    if not stack_destinations:
        raise ValueError("at least one stack destination is required")
    capacity = len(stack_destinations) * MAX_STACK_HEIGHT
    if container_count > capacity:
        raise ValueError(f"container_count cannot exceed {capacity}")

    containers = tuple(
        Container(
            id=f"C{i + 1}",
            destination=stack_destinations[i % len(stack_destinations)],
            priority=(i % 3) + 1,
        )
        for i in range(container_count)
    )

    ids = [container.id for container in containers]
    rng = random.Random(seed)
    rng.shuffle(ids)

    stacks: list[list[str]] = [[] for _ in stack_destinations]
    for position, container_id in enumerate(ids):
        stacks[position % len(stacks)].append(container_id)

    return ContainerStackState(
        stacks=tuple(tuple(stack) for stack in stacks),
        containers=containers,
        stack_destinations=stack_destinations,
    )
