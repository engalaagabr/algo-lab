"""Bottom-up binary max-heap sort with early-stopping sift-down."""

from domain.models import AlgorithmMetadata, Complexity
from domain.operations import SortContext

metadata = AlgorithmMetadata(
    id="heap_sort",
    name="Heap Sort",
    description="Build a binary max heap, then repeatedly move its maximum to the array end.",
    complexity=Complexity(
        "O(n)",
        "O(n log n)",
        "O(n log n)",
        "O(1)",
        "The linear best case permits equal keys and early-stopping sift-down. "
        "With distinct keys, the best case is O(n log n).",
    ),
    stable=False,
    in_place=True,
    max_size=10_000,
    workload="n_log_n",
)


def _sift_down(context: SortContext, root: int, stop: int) -> None:
    values = context.values
    while 2 * root + 1 < stop:
        child = 2 * root + 1
        right = child + 1
        if right < stop and context.compare(values[right], values[child], (right, child)) > 0:
            child = right
        if context.compare(values[root], values[child], (root, child)) >= 0:
            return
        context.swap(root, child)
        root = child


def sort(context: SortContext) -> None:
    size = len(context.values)
    for root in range(size // 2 - 1, -1, -1):
        _sift_down(context, root, size)
    for stop in range(size - 1, 0, -1):
        context.swap(0, stop)
        _sift_down(context, 0, stop)
