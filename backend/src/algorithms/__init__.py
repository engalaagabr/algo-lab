"""Concrete sorting algorithms wired through the domain registry."""

from domain.models import Algorithm
from domain.registry import AlgorithmRegistry

from . import (
    binary_insertion_sort,
    bubble_sort,
    cocktail_sort,
    frequency_sort,
    heap_sort,
    insertion_sort,
    odd_even_sort,
    quick_sort,
    selection_sort,
    shell_sort,
)

__all__ = ["build_registry"]


def build_registry() -> AlgorithmRegistry:
    """Build a fresh registry with the ten supported algorithms in display order."""
    return AlgorithmRegistry(
        [
            Algorithm(selection_sort.metadata, selection_sort.sort),
            Algorithm(bubble_sort.metadata, bubble_sort.sort),
            Algorithm(odd_even_sort.metadata, odd_even_sort.sort),
            Algorithm(cocktail_sort.metadata, cocktail_sort.sort),
            Algorithm(insertion_sort.metadata, insertion_sort.sort),
            Algorithm(binary_insertion_sort.metadata, binary_insertion_sort.sort),
            Algorithm(frequency_sort.metadata, frequency_sort.sort),
            Algorithm(shell_sort.metadata, shell_sort.sort),
            Algorithm(heap_sort.metadata, heap_sort.sort),
            Algorithm(quick_sort.metadata, quick_sort.sort),
        ]
    )
