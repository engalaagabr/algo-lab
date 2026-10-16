from dataclasses import dataclass, field

from algolab.domain.models import SortEvent


@dataclass(frozen=True, slots=True)
class DatasetSpec:
    size: int = 50
    minimum: int = 1
    maximum: int = 100
    distribution: str = "random"
    seed: int | None = None


@dataclass(frozen=True, slots=True)
class DatasetResult:
    values: list[int]
    seed: int
    size: int
    minimum: int
    maximum: int
    distribution: str


@dataclass(frozen=True, slots=True)
class OperationMetrics:
    comparisons: int
    swaps: int
    array_writes: int
    auxiliary_writes: int
    writes: int


@dataclass(frozen=True, slots=True)
class SortResult:
    algorithm_id: str
    output_values: list[int]
    metrics: OperationMetrics
    events: list[SortEvent] | None


@dataclass(frozen=True, slots=True)
class SortExperiment:
    input_values: list[int]
    results: list[SortResult]


@dataclass(frozen=True, slots=True)
class AlgorithmBenchmark:
    algorithm_id: str
    output_values: list[int]
    metrics: OperationMetrics
    samples_ns: list[int]
    median_ns: float
    min_ns: int
    max_ns: int
    spread_ns: int


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    input_values: list[int]
    seed: int
    repeats: int
    warmups: int
    results: list[AlgorithmBenchmark]
    fastest_algorithm_ids: list[str]
    noise_warning: bool


@dataclass(frozen=True, slots=True)
class SuiteSpec:
    algorithm_ids: list[str]
    sizes: list[int]
    distributions: list[str]
    minimum: int = 1
    maximum: int = 100
    seed: int | None = None
    repeats: int = 5
    warmups: int = 1


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    dataset: DatasetResult
    benchmark: BenchmarkResult


@dataclass(frozen=True, slots=True)
class BenchmarkSuiteResult:
    seed: int
    cases: list[BenchmarkCase] = field(default_factory=list)
