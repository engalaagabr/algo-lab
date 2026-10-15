from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from algolab.domain.operations import SortContext


@dataclass(frozen=True, slots=True)
class Complexity:
    best: str
    average: str
    worst: str
    auxiliary_space: str
    notes: str = ""


@dataclass(frozen=True, slots=True)
class AlgorithmMetadata:
    id: str
    name: str
    description: str
    complexity: Complexity
    stable: bool
    in_place: bool
    comparison_based: bool = True
    max_size: int = 1000
    max_value_range: int | None = None


@dataclass(frozen=True, slots=True)
class Algorithm:
    metadata: AlgorithmMetadata
    sort: Callable[[SortContext], None]


@dataclass(slots=True)
class Metrics:
    comparisons: int = 0
    swaps: int = 0
    array_writes: int = 0
    auxiliary_writes: int = 0

    @property
    def writes(self) -> int:
        return self.array_writes + self.auxiliary_writes


@dataclass(frozen=True, slots=True)
class SortEvent:
    sequence: int
    kind: Literal["compare", "swap", "write"]
    indices: tuple[int, ...]
    values: tuple[int, ...]
