from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request

from algolab.application.datasets import generate_dataset
from algolab.application.execution import ExecutionRunner
from algolab.application.models import (
    BenchmarkResult,
    BenchmarkSuiteResult,
    DatasetResult,
    DatasetSpec,
    SortExperiment,
    SuiteSpec,
)
from algolab.domain.models import AlgorithmMetadata
from algolab.domain.registry import AlgorithmRegistry
from algolab.presentation.schemas import (
    BenchmarkRequest,
    DatasetRequest,
    ErrorResponse,
    SortRequest,
    SuiteRequest,
)

router = APIRouter(
    prefix="/api/v1",
    responses={
        404: {"model": ErrorResponse, "description": "Unknown algorithm ID"},
        413: {"model": ErrorResponse, "description": "Request body exceeds 1 MB"},
        422: {"model": ErrorResponse, "description": "Invalid input or experiment limit exceeded"},
        500: {
            "model": ErrorResponse,
            "description": "Internal failure or invalid algorithm output",
        },
        503: {"model": ErrorResponse, "description": "Execution capacity full or unavailable"},
    },
)


def get_runner(request: Request) -> ExecutionRunner:
    return cast(ExecutionRunner, request.app.state.runner)


def get_registry(request: Request) -> AlgorithmRegistry:
    return cast(AlgorithmRegistry, request.app.state.registry)


Runner = Annotated[ExecutionRunner, Depends(get_runner)]
Registry = Annotated[AlgorithmRegistry, Depends(get_registry)]


@router.get("/algorithms", tags=["Algorithms"])
def list_algorithms(registry: Registry) -> list[AlgorithmMetadata]:
    """List algorithm IDs, implementation-specific complexity, and input limits."""
    return registry.list_metadata()


@router.get(
    "/algorithms/{algorithm_id}", tags=["Algorithms"], responses={404: {"model": ErrorResponse}}
)
def get_algorithm(algorithm_id: str, registry: Registry) -> AlgorithmMetadata:
    return registry.get(algorithm_id).metadata


@router.post("/datasets", tags=["Datasets"])
def create_dataset(payload: DatasetRequest) -> DatasetResult:
    """Generate a reproducible dataset; reuse its values for each comparison."""
    return generate_dataset(DatasetSpec(**payload.model_dump()))


@router.post("/sort", tags=["Experiments"])
async def sort(payload: SortRequest, runner: Runner) -> SortExperiment:
    """Sort identical copies, count operations, and optionally return complete replay traces."""
    return await runner.sort(payload.values, payload.algorithm_ids, trace=payload.trace)


@router.post("/benchmarks", tags=["Benchmarks"])
async def benchmark(payload: BenchmarkRequest, runner: Runner) -> BenchmarkResult:
    """Measure sequential, repeated runs without counting or trace recording in the timer."""
    return await runner.benchmark(
        payload.values,
        payload.algorithm_ids,
        repeats=payload.repeats,
        warmups=payload.warmups,
        seed=payload.seed,
    )


@router.post("/benchmark-suites", tags=["Benchmarks"])
async def benchmark_suite(payload: SuiteRequest, runner: Runner) -> BenchmarkSuiteResult:
    """Compare algorithms over a bounded matrix of sizes and input distributions."""
    return await runner.suite(SuiteSpec(**payload.model_dump()))
