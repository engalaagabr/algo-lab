import asyncio
import multiprocessing
from collections.abc import Callable
from concurrent.futures import Future, ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from functools import partial
from typing import TypeVar

from application.execution import ExecutionBusy, ExecutionUnavailable
from application.models import (
    BenchmarkResult,
    BenchmarkSuiteResult,
    SortExperiment,
    SuiteSpec,
)
from infrastructure.worker import run_benchmark_job, run_sort_job, run_suite_job

T = TypeVar("T")


class ProcessExecutionRunner:
    """One worker isolates CPU work and serializes experiments within this API process."""

    def __init__(self, max_pending: int = 4) -> None:
        if max_pending < 1:
            raise ValueError("max_pending must be positive")
        self._pool = ProcessPoolExecutor(
            max_workers=1, mp_context=multiprocessing.get_context("spawn")
        )
        self._max_pending = max_pending
        self._pending = 0
        self._closed = False

    async def _submit(self, function: Callable[[], T]) -> T:
        if self._closed:
            raise ExecutionUnavailable("Execution worker is unavailable.")
        if self._pending >= self._max_pending:
            raise ExecutionBusy("Execution capacity is full; retry shortly.")
        self._pending += 1
        loop = asyncio.get_running_loop()
        try:
            future = self._pool.submit(function)
        except (BrokenProcessPool, RuntimeError):
            self._pending -= 1
            raise ExecutionUnavailable("Execution worker is unavailable.") from None

        def finished(_: Future[T]) -> None:
            # A cancelled HTTP await does not release a still-running CPU job's slot.
            loop.call_soon_threadsafe(self._release)

        future.add_done_callback(finished)
        try:
            return await asyncio.wrap_future(future)
        except BrokenProcessPool:
            raise ExecutionUnavailable("Execution worker stopped unexpectedly.") from None

    def _release(self) -> None:
        self._pending -= 1

    async def sort(
        self, values: list[int], algorithm_ids: list[str], *, trace: bool = False
    ) -> SortExperiment:
        return await self._submit(partial(run_sort_job, values, algorithm_ids, trace))

    async def benchmark(
        self,
        values: list[int],
        algorithm_ids: list[str],
        *,
        repeats: int = 5,
        warmups: int = 1,
        seed: int | None = None,
    ) -> BenchmarkResult:
        return await self._submit(
            partial(run_benchmark_job, values, algorithm_ids, repeats, warmups, seed)
        )

    async def suite(self, spec: SuiteSpec) -> BenchmarkSuiteResult:
        return await self._submit(partial(run_suite_job, spec))

    async def close(self) -> None:
        self._closed = True
        await asyncio.to_thread(self._pool.shutdown, wait=True, cancel_futures=True)
