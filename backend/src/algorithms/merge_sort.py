"""Stable top-down merge sort with an instrumented auxiliary buffer."""

from domain.models import AlgorithmMetadata, Complexity
from domain.operations import SortContext

metadata = AlgorithmMetadata(
    id="merge_sort",
    name="Merge Sort",
    description=(
        "Recursively split the array, then stably merge each pair of sorted halves "
        "using an auxiliary buffer."
    ),
    complexity=Complexity(
        "O(n log n)",
        "O(n log n)",
        "O(n log n)",
        "O(n)",
        "Stable; each merge writes its range to a reusable auxiliary buffer and back.",
    ),
    stable=True,
    in_place=False,
    max_size=10_000,
    workload="n_log_n",
)


def sort(context: SortContext) -> None:
    values = context.values
    size = len(values)
    if size < 2:
        return

    buffer = [0] * size
    context.auxiliary_write(size)

    def merge(low: int, middle: int, high: int) -> None:
        left = low
        right = middle
        target = low

        while left < middle and right < high:
            if context.compare(values[left], values[right], (left, right)) <= 0:
                buffer[target] = values[left]
                left += 1
            else:
                buffer[target] = values[right]
                right += 1
            target += 1
            context.auxiliary_write()

        while left < middle:
            buffer[target] = values[left]
            left += 1
            target += 1
            context.auxiliary_write()

        while right < high:
            buffer[target] = values[right]
            right += 1
            target += 1
            context.auxiliary_write()

        for index in range(low, high):
            context.write(index, buffer[index])

    def split_and_merge(low: int, high: int) -> None:
        if high - low < 2:
            return
        middle = (low + high) // 2
        split_and_merge(low, middle)
        split_and_merge(middle, high)
        merge(low, middle, high)

    split_and_merge(0, size)
