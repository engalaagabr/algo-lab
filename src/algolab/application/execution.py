"""Async execution boundary, independent of any transport or worker implementation."""

from typing import Protocol

from algolab.application.models import (
    BenchmarkResult,
    BenchmarkSuiteResult,
    SortExperiment,
    SuiteSpec,
)


class ExecutionBusy(Exception):
    pass


class ExecutionUnavailable(Exception):
    pass


class ExecutionRunner(Protocol):
    async def sort(
        self, values: list[int], algorithm_ids: list[str], *, trace: bool = False
    ) -> SortExperiment: ...

    async def benchmark(
        self,
        values: list[int],
        algorithm_ids: list[str],
        *,
        repeats: int = 5,
        warmups: int = 1,
        seed: int | None = None,
    ) -> BenchmarkResult: ...

    async def suite(self, spec: SuiteSpec) -> BenchmarkSuiteResult: ...
