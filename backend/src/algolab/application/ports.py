from typing import Protocol


class Clock(Protocol):
    """Monotonic, high-resolution elapsed-time source, expressed in nanoseconds."""

    def now_ns(self) -> int: ...
