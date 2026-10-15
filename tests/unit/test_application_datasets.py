from dataclasses import replace

import pytest

from algolab.application.datasets import generate_dataset
from algolab.application.models import DatasetSpec
from algolab.application.validation import DISTRIBUTIONS, MAX_SEED
from algolab.domain.errors import DomainError


@pytest.mark.parametrize("distribution", DISTRIBUTIONS)
def test_seed_reproduces_every_distribution(distribution: str) -> None:
    spec = DatasetSpec(size=100, minimum=-30, maximum=25, distribution=distribution, seed=2026)
    first = generate_dataset(spec)
    assert generate_dataset(spec) == first
    assert len(first.values) == 100
    assert all(type(value) is int and -30 <= value <= 25 for value in first.values)


def test_returned_seed_reproduces_an_unseeded_request() -> None:
    spec = DatasetSpec(size=40, minimum=-5, maximum=9)
    generated = generate_dataset(spec)
    assert 0 <= generated.seed <= MAX_SEED
    assert generate_dataset(replace(spec, seed=generated.seed)) == generated


@pytest.mark.parametrize("distribution", DISTRIBUTIONS)
def test_empty_and_single_value_range(distribution: str) -> None:
    spec = DatasetSpec(size=0, minimum=-3, maximum=-3, distribution=distribution, seed=0)
    assert generate_dataset(spec).values == []
    assert generate_dataset(replace(spec, size=4)).values == [-3] * 4


def test_ordered_and_few_unique_distributions_have_documented_shapes() -> None:
    spec = DatasetSpec(size=100, minimum=-100, maximum=100, seed=8)
    source = generate_dataset(spec).values
    assert generate_dataset(replace(spec, distribution="sorted")).values == sorted(source)
    assert generate_dataset(replace(spec, distribution="reversed")).values == sorted(
        source, reverse=True
    )
    nearly = generate_dataset(replace(spec, distribution="nearly_sorted")).values
    assert sorted(nearly) == sorted(source)
    assert sum(a != b for a, b in zip(nearly, sorted(source), strict=True)) <= 10
    assert len(set(generate_dataset(replace(spec, distribution="few_unique")).values)) <= 5


@pytest.mark.parametrize(
    "overrides",
    [
        {"size": True},
        {"size": 3.0},
        {"size": -1},
        {"size": 10001},
        {"minimum": False},
        {"maximum": 2.5},
        {"minimum": -1000000001},
        {"maximum": 1000000001},
        {"minimum": 10, "maximum": 0},
        {"seed": True},
        {"seed": 4.0},
        {"seed": -1},
        {"seed": MAX_SEED + 1},
        {"distribution": "unknown"},
        {"distribution": 4},
    ],
)
def test_dataset_settings_fail_at_domain_boundary(overrides: dict[str, object]) -> None:
    with pytest.raises(DomainError):
        generate_dataset(replace(DatasetSpec(), **overrides))  # type: ignore[arg-type]


def test_few_unique_handles_huge_ranges_without_allocating_the_range() -> None:
    result = generate_dataset(
        DatasetSpec(size=20, minimum=-(10**9), maximum=10**9, distribution="few_unique", seed=9)
    )
    assert len(result.values) == 20
    assert len(set(result.values)) <= 5
