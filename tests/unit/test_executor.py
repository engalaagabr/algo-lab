import asyncio
from concurrent.futures import Future
from concurrent.futures.process import BrokenProcessPool

import pytest

from algolab.application.execution import ExecutionBusy, ExecutionUnavailable
from algolab.infrastructure import executor


class ControlledPool:
    def __init__(self):
        self.futures = []
        self.closed = False

    def submit(self, function):
        future = Future()
        future.set_running_or_notify_cancel()
        self.futures.append(future)
        return future

    def shutdown(self, *, wait, cancel_futures):
        self.closed = True


def test_running_job_keeps_capacity_when_its_await_is_cancelled(monkeypatch):
    pool = ControlledPool()
    monkeypatch.setattr(executor, "ProcessPoolExecutor", lambda **kwargs: pool)

    async def scenario():
        runner = executor.ProcessExecutionRunner(max_pending=1)
        task = asyncio.create_task(runner._submit(lambda: 42))
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        with pytest.raises(ExecutionBusy):
            await runner._submit(lambda: 99)
        assert not pool.futures[0].cancelled()
        pool.futures[0].set_result(42)
        await asyncio.sleep(0)
        next_task = asyncio.create_task(runner._submit(lambda: 99))
        await asyncio.sleep(0)
        pool.futures[1].set_result(99)
        assert await next_task == 99
        await runner.close()
        assert pool.closed
        with pytest.raises(ExecutionUnavailable):
            await runner._submit(lambda: 1)

    asyncio.run(scenario())


def test_worker_failure_is_translated_and_capacity_released(monkeypatch):
    pool = ControlledPool()
    monkeypatch.setattr(executor, "ProcessPoolExecutor", lambda **kwargs: pool)

    async def scenario():
        runner = executor.ProcessExecutionRunner(max_pending=1)
        task = asyncio.create_task(runner._submit(lambda: 1))
        await asyncio.sleep(0)
        pool.futures[0].set_exception(BrokenProcessPool("worker exited"))
        with pytest.raises(ExecutionUnavailable):
            await task
        assert runner._pending == 0
        await runner.close()

    asyncio.run(scenario())


def test_submission_failure_does_not_consume_capacity(monkeypatch):
    pool = ControlledPool()

    def unavailable(function):
        raise RuntimeError("closed")

    pool.submit = unavailable
    monkeypatch.setattr(executor, "ProcessPoolExecutor", lambda **kwargs: pool)

    async def scenario():
        runner = executor.ProcessExecutionRunner(max_pending=1)
        with pytest.raises(ExecutionUnavailable):
            await runner._submit(lambda: 1)
        assert runner._pending == 0
        await runner.close()

    asyncio.run(scenario())
