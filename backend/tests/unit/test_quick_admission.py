from dataclasses import replace

import pytest

from algorithms import build_registry
from application.services import ExperimentService
from domain.errors import LimitExceeded
from domain.models import Algorithm
from domain.registry import AlgorithmRegistry


class UnusedClock:
    def now_ns(self):
        raise AssertionError("Rejected experiments must not start timing")


def test_adversarial_quicksort_work_is_rejected_before_execution():
    def forbidden_sort(context):
        raise AssertionError("Rejected experiments must not run the algorithm")

    metadata = build_registry().get("quick_sort").metadata
    assert metadata.workload == "quadratic"
    registry = AlgorithmRegistry([Algorithm(replace(metadata), forbidden_sort)])
    service = ExperimentService(registry, UnusedClock())
    values = list(range(0, 2000, 2)) + list(range(1, 2000, 2))
    with pytest.raises(LimitExceeded, match="work budget"):
        service.benchmark(values, ["quick_sort"], repeats=15, warmups=3, seed=1)
