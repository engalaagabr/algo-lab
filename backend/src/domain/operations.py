from typing import Literal

from domain.errors import TraceLimitExceeded
from domain.models import Metrics, SortEvent


class SortContext:
    """Per-run mutable state; the caller owns the supplied working copy."""

    def __init__(
        self,
        values: list[int],
        *,
        count: bool = True,
        trace: bool = False,
        max_events: int = 20000,
    ) -> None:
        self.values = values
        self.metrics = Metrics()
        self.events: list[SortEvent] = []
        self.count = count
        self.trace = trace
        self.max_events = max_events

    def _emit(
        self,
        kind: Literal["compare", "swap", "write"],
        indices: tuple[int, ...],
        values: tuple[int, ...],
    ) -> None:
        if not self.trace:
            return
        if len(self.events) >= self.max_events:
            raise TraceLimitExceeded(f"Trace exceeds {self.max_events} events; reduce input size.")
        self.events.append(SortEvent(len(self.events), kind, indices, values))

    def compare(self, left: int, right: int, indices: tuple[int, ...] = ()) -> int:
        if self.count:
            self.metrics.comparisons += 1
        if self.trace:
            self._emit("compare", indices, (left, right))
        return (left > right) - (left < right)

    def swap(self, first: int, second: int) -> None:
        if first == second:
            return
        self.values[first], self.values[second] = self.values[second], self.values[first]
        if self.count:
            self.metrics.swaps += 1
            self.metrics.array_writes += 2
        if self.trace:
            self._emit("swap", (first, second), (self.values[first], self.values[second]))

    def write(self, index: int, value: int) -> None:
        self.values[index] = value
        if self.count:
            self.metrics.array_writes += 1
        if self.trace:
            self._emit("write", (index,), (value,))

    def auxiliary_write(self, count: int = 1) -> None:
        if self.count:
            self.metrics.auxiliary_writes += count
