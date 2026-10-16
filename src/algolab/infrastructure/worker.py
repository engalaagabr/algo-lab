"""Picklable process-pool entry points and their per-job service composition."""

from algolab.algorithms import build_registry
from algolab.application.models import (
    BenchmarkResult,
    BenchmarkSuiteResult,
    SortExperiment,
    SuiteSpec,
)
from algolab.application.services import ExperimentService
from algolab.infrastructure.clock import PerformanceClock


def _build_service() -> ExperimentService:
    """Create worker-local dependencies inside the spawned process."""
    return ExperimentService(build_registry(), PerformanceClock())


def run_sort_job(values: list[int], algorithm_ids: list[str], trace: bool) -> SortExperiment:
    return _build_service().sort(values, algorithm_ids, trace=trace)


def run_benchmark_job(
    values: list[int],
    algorithm_ids: list[str],
    repeats: int,
    warmups: int,
    seed: int | None,
) -> BenchmarkResult:
    return _build_service().benchmark(
        values, algorithm_ids, repeats=repeats, warmups=warmups, seed=seed
    )


def run_suite_job(spec: SuiteSpec) -> BenchmarkSuiteResult:
    return _build_service().suite(spec)
