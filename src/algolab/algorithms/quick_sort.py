"""Iterative three-way quicksort with deterministic median-of-three pivots."""

from algolab.domain.models import AlgorithmMetadata, Complexity
from algolab.domain.operations import SortContext

metadata = AlgorithmMetadata(
    id="quick_sort",
    name="Quick Sort",
    description=(
        "Iterative three-way partitioning with median-of-three pivots; "
        "processes smaller partitions first to bound the pending stack."
    ),
    complexity=Complexity(
        "O(n)",
        "O(n log n)",
        "O(n^2)",
        "O(log n)",
        "All-equal input gives the linear best case; balanced distinct keys take O(n log n). "
        "The average assumes random input order, not adversarial input. Median-of-three "
        "does not guarantee O(n log n). Auxiliary space includes the explicit bound stack.",
    ),
    stable=False,
    in_place=True,
    max_size=10_000,
    workload="n_log_n",
)


def _pivot(context: SortContext, low: int, high: int) -> int:
    values = context.values
    middle = (low + high) // 2
    first, center, last = values[low], values[middle], values[high]
    if context.compare(first, center, (low, middle)) <= 0:
        if context.compare(center, last, (middle, high)) <= 0:
            return center
        if context.compare(first, last, (low, high)) <= 0:
            return last
        return first
    if context.compare(first, last, (low, high)) <= 0:
        return first
    if context.compare(center, last, (middle, high)) <= 0:
        return last
    return center


def _defer(context: SortContext, pending: list[int], low: int, high: int) -> None:
    if low < high:
        pending.append(low)
        pending.append(high)
        context.auxiliary_write(2)


def sort(context: SortContext) -> None:
    values = context.values
    low, high = 0, len(values) - 1
    pending: list[int] = []
    while True:
        while low < high:
            pivot = _pivot(context, low, high)
            lower = current = low
            upper = high
            while current <= upper:
                relation = context.compare(values[current], pivot, (current,))
                if relation < 0:
                    context.swap(lower, current)
                    lower += 1
                    current += 1
                elif relation > 0:
                    context.swap(current, upper)
                    upper -= 1
                else:
                    current += 1

            # Defer the larger partition; each nested smaller partition at least halves.
            if lower - low < high - upper:
                _defer(context, pending, upper + 1, high)
                high = lower - 1
            else:
                _defer(context, pending, low, lower - 1)
                low = upper + 1
        if not pending:
            return
        high = pending.pop()
        low = pending.pop()
