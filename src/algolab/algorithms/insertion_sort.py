"""Stable insertion sort using shifts."""

from algolab.domain.models import AlgorithmMetadata, Complexity
from algolab.domain.operations import SortContext

metadata: AlgorithmMetadata = AlgorithmMetadata(
    id="insertion_sort",
    name="Insertion Sort",
    description="Insert each value into the sorted prefix by shifting larger values right.",
    complexity=Complexity(
        best="O(n)",
        average="O(n^2)",
        worst="O(n^2)",
        auxiliary_space="O(1)",
        notes="An already ordered value needs one comparison and no writes.",
    ),
    stable=True,
    in_place=True,
    max_size=1000,
)


def sort(context: SortContext) -> None:
    """Shift only strictly larger values, preserving the order of equal values."""
    values = context.values
    for index in range(1, len(values)):
        key = values[index]
        position = index
        while position > 0:
            if context.compare(values[position - 1], key, (position - 1,)) <= 0:
                break
            context.write(position, values[position - 1])
            position -= 1
        if position != index:
            context.write(position, key)
