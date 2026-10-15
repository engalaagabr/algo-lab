"""Shell sort using n // 2, n // 4, ..., 1 gaps."""

from algolab.domain.models import AlgorithmMetadata, Complexity
from algolab.domain.operations import SortContext

metadata = AlgorithmMetadata(
    id="shell_sort",
    name="Shell Sort",
    description="Gapped insertion sort using the original halving gap sequence.",
    complexity=Complexity(
        "O(n log n)",
        "Unknown (halving gaps)",
        "O(n^2)",
        "O(1)",
        "Uses n // 2, n // 4, ..., 1 gaps. No average-case bound is claimed for this variant.",
    ),
    stable=False,
    in_place=True,
)


def sort(context: SortContext) -> None:
    values = context.values
    gap = len(values) // 2
    while gap > 0:
        for index in range(gap, len(values)):
            key = values[index]
            position = index
            while position >= gap:
                previous = position - gap
                if context.compare(values[previous], key, (previous,)) <= 0:
                    break
                context.write(position, values[previous])
                position = previous
            if position != index:
                context.write(position, key)
        gap //= 2
