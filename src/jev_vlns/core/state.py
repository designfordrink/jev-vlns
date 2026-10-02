from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class State:
    """Immutable base state.

    Environment-specific state should extend or compose this type. The core
    search layer must treat state as read-only.
    """

    data: Any = None
