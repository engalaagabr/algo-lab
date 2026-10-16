from collections.abc import Iterator
from dataclasses import asdict
from typing import Any

import pytest
from fastapi.testclient import TestClient

from algolab.algorithms import build_registry
from algolab.application.execution import ExecutionBusy, ExecutionUnavailable
from algolab.application.models import (
    BenchmarkResult,
    BenchmarkSuiteResult,
    SortExperiment,
    SuiteSpec,
)
from algolab.application.services import ExperimentService
from algolab.domain.errors import InvalidResult
from algolab.main import create_app

ALGORITHM_IDS = {
    "selection_sort",
    "bubble_sort",
    "odd_even_sort",
    "cocktail_sort",
    "insertion_sort",
    "binary_insertion_sort",
    "frequency_sort",
    "shell_sort",
    "heap_sort",
    "quick_sort",
}
DISTRIBUTIONS = ["random", "sorted", "reversed", "nearly_sorted", "few_unique"]


class FakeClock:
    def __init__(self) -> None:
        self.ticks = 0

    def now_ns(self) -> int:
        self.ticks += 100
        return self.ticks


class LocalRunner:
    """Exercise actual use cases over HTTP without starting a worker process."""

    def __init__(self, failure: Exception | None = None) -> None:
        self.service = ExperimentService(build_registry(), FakeClock())
        self.failure = failure
        self.calls = 0

    def _before(self) -> None:
        self.calls += 1
        if self.failure is not None:
            raise self.failure

    async def sort(
        self, values: list[int], algorithm_ids: list[str], *, trace: bool = False
    ) -> SortExperiment:
        self._before()
        return self.service.sort(values, algorithm_ids, trace=trace)

    async def benchmark(
        self,
        values: list[int],
        algorithm_ids: list[str],
        *,
        repeats: int = 5,
        warmups: int = 1,
        seed: int | None = None,
    ) -> BenchmarkResult:
        self._before()
        return self.service.benchmark(
            values, algorithm_ids, repeats=repeats, warmups=warmups, seed=seed
        )

    async def suite(self, spec: SuiteSpec) -> BenchmarkSuiteResult:
        self._before()
        return self.service.suite(spec)


@pytest.fixture
def runner() -> LocalRunner:
    return LocalRunner()


@pytest.fixture
def client(runner: LocalRunner) -> Iterator[TestClient]:
    with TestClient(create_app(runner)) as test_client:
        yield test_client


def assert_error(response: Any, status: int, code: str | None = None) -> None:
    assert response.status_code == status, response.text
    assert set(response.json()) == {"error"}
    detail = response.json()["error"]
    assert isinstance(detail["code"], str)
    assert isinstance(detail["message"], str) and detail["message"]
    if code is not None:
        assert detail["code"] == code


def test_health_is_independent_of_execution_worker() -> None:
    runner = LocalRunner(ExecutionUnavailable("Unavailable"))
    with TestClient(create_app(runner)) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "AlgoLab"
    assert response.json()["version"]
    assert runner.calls == 0


def test_catalog_contains_exactly_the_ten_agreed_algorithms(client: TestClient) -> None:
    response = client.get("/api/v1/algorithms")
    assert response.status_code == 200
    catalog = response.json()
    assert len(catalog) == 10
    assert {algorithm["id"] for algorithm in catalog} == ALGORITHM_IDS
    for algorithm in catalog:
        assert set(algorithm["complexity"]) >= {"best", "average", "worst", "auxiliary_space"}
        assert algorithm["max_size"] > 0
        detail = client.get(f"/api/v1/algorithms/{algorithm['id']}")
        assert detail.status_code == 200
        assert detail.json() == algorithm
    assert_error(client.get("/api/v1/algorithms/missing"), 404, "unknown_algorithm")


@pytest.mark.parametrize("distribution", DISTRIBUTIONS)
def test_generated_datasets_are_reproducible_over_http(
    client: TestClient,
    distribution: str,
) -> None:
    payload = {"size": 20, "minimum": -20, "maximum": 30, "distribution": distribution}
    response = client.post("/api/v1/datasets", json=payload)
    assert response.status_code == 200, response.text
    dataset = response.json()
    assert 0 <= dataset["seed"] <= 2**32 - 1
    assert len(dataset["values"]) == 20
    repeated = client.post("/api/v1/datasets", json={**payload, "seed": dataset["seed"]})
    assert repeated.json() == dataset
    assert all(-20 <= value <= 30 for value in dataset["values"])


@pytest.mark.parametrize("algorithm_id", sorted(ALGORITHM_IDS))
def test_each_algorithm_returns_replayable_trace_and_serialized_metrics(
    client: TestClient,
    algorithm_id: str,
) -> None:
    values = [4, -2, 1, 4, 0, -2]
    response = client.post(
        "/api/v1/sort",
        json={
            "values": values,
            "algorithm_ids": [algorithm_id],
            "trace": True,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["input_values"] == values
    result = payload["results"][0]
    assert result["algorithm_id"] == algorithm_id
    assert result["output_values"] == sorted(values)
    metrics = result["metrics"]
    assert metrics["writes"] == metrics["array_writes"] + metrics["auxiliary_writes"]
    assert all(type(value) is int and value >= 0 for value in metrics.values())
    reconstructed = values.copy()
    assert isinstance(result["events"], list)
    for sequence, event in enumerate(result["events"]):
        assert event["sequence"] == sequence
        assert isinstance(event["indices"], list)
        if event["kind"] in ("swap", "write"):
            for index, value in zip(event["indices"], event["values"], strict=True):
                reconstructed[index] = value
    assert reconstructed == result["output_values"]


def test_all_algorithms_receive_same_input_in_one_request(client: TestClient) -> None:
    values = [5, -1, 5, 0]
    response = client.post(
        "/api/v1/sort",
        json={
            "values": values,
            "algorithm_ids": sorted(ALGORITHM_IDS),
        },
    )
    assert response.status_code == 200
    assert response.json()["input_values"] == values
    assert len(response.json()["results"]) == 10
    assert all(result["output_values"] == sorted(values) for result in response.json()["results"])
    assert all(result["events"] is None for result in response.json()["results"])


@pytest.mark.parametrize("values", [[], [0], [-3, -3]])
def test_empty_singleton_and_duplicate_data_are_accepted(
    client: TestClient,
    values: list[int],
) -> None:
    response = client.post(
        "/api/v1/sort",
        json={
            "values": values,
            "algorithm_ids": ["frequency_sort", "quick_sort"],
            "trace": True,
        },
    )
    assert response.status_code == 200
    assert all(row["output_values"] == sorted(values) for row in response.json()["results"])


@pytest.mark.parametrize("endpoint", ["sort", "benchmarks"])
def test_unknown_algorithm_and_duplicate_ids_are_rejected(
    client: TestClient,
    endpoint: str,
) -> None:
    unknown = client.post(f"/api/v1/{endpoint}", json={"values": [2, 1], "algorithm_ids": ["bad"]})
    assert_error(unknown, 404, "unknown_algorithm")
    duplicate = client.post(
        f"/api/v1/{endpoint}",
        json={
            "values": [2, 1],
            "algorithm_ids": ["quick_sort", "quick_sort"],
        },
    )
    assert_error(duplicate, 422, "validation_error")


@pytest.mark.parametrize("invalid", [True, False, 1.0, "1", None, [], {}])
@pytest.mark.parametrize("endpoint", ["sort", "benchmarks"])
def test_integer_array_values_are_not_coerced(
    client: TestClient,
    runner: LocalRunner,
    endpoint: str,
    invalid: object,
) -> None:
    response = client.post(
        f"/api/v1/{endpoint}",
        json={
            "values": [invalid],
            "algorithm_ids": ["quick_sort"],
        },
    )
    assert_error(response, 422, "validation_error")
    assert runner.calls == 0


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("datasets", {"size": True}),
        ("datasets", {"size": 2.0}),
        ("datasets", {"size": "2"}),
        ("datasets", {"minimum": False}),
        ("datasets", {"maximum": 3.5}),
        ("datasets", {"seed": "4"}),
        ("datasets", {"seed": True}),
        ("sort", {"values": [], "algorithm_ids": ["quick_sort"], "trace": 1}),
        ("sort", {"values": [], "algorithm_ids": ["quick_sort"], "trace": "false"}),
        ("sort", {"values": [], "algorithm_ids": [4]}),
        ("benchmarks", {"values": [], "algorithm_ids": ["quick_sort"], "repeats": "2"}),
        ("benchmarks", {"values": [], "algorithm_ids": ["quick_sort"], "warmups": False}),
        (
            "benchmark-suites",
            {"algorithm_ids": ["quick_sort"], "sizes": [1.0], "distributions": ["random"]},
        ),
    ],
)
def test_settings_are_strictly_typed(
    client: TestClient,
    runner: LocalRunner,
    endpoint: str,
    payload: dict[str, object],
) -> None:
    assert_error(client.post(f"/api/v1/{endpoint}", json=payload), 422, "validation_error")
    assert runner.calls == 0


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("datasets", {}),
        ("sort", {"values": [], "algorithm_ids": ["quick_sort"]}),
        ("benchmarks", {"values": [], "algorithm_ids": ["quick_sort"]}),
        (
            "benchmark-suites",
            {"algorithm_ids": ["quick_sort"], "sizes": [1], "distributions": ["random"]},
        ),
    ],
)
def test_unknown_request_fields_are_rejected(
    client: TestClient,
    endpoint: str,
    payload: dict[str, object],
) -> None:
    assert_error(
        client.post(f"/api/v1/{endpoint}", json={**payload, "typo": 1}), 422, "validation_error"
    )


def test_malformed_json_and_missing_body_have_consistent_errors(client: TestClient) -> None:
    response = client.post(
        "/api/v1/sort", content='{"values": ', headers={"Content-Type": "application/json"}
    )
    assert_error(response, 422, "validation_error")
    assert_error(client.post("/api/v1/sort"), 422, "validation_error")


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("datasets", {"size": -1}),
        ("datasets", {"size": 10001}),
        ("datasets", {"minimum": 5, "maximum": 4}),
        ("datasets", {"minimum": -(10**9) - 1}),
        ("datasets", {"maximum": 10**9 + 1}),
        ("datasets", {"seed": -1}),
        ("datasets", {"seed": 2**32}),
        ("datasets", {"distribution": "unsupported"}),
        ("sort", {"values": [], "algorithm_ids": []}),
        ("sort", {"values": [10**9 + 1], "algorithm_ids": ["quick_sort"]}),
        ("sort", {"values": [0] * 10001, "algorithm_ids": ["quick_sort"]}),
        ("sort", {"values": [0] * 1001, "algorithm_ids": ["bubble_sort"]}),
        ("sort", {"values": [-(10**9), 10**9], "algorithm_ids": ["frequency_sort"]}),
        ("sort", {"values": [0] * 129, "algorithm_ids": ["quick_sort"], "trace": True}),
        ("benchmarks", {"values": [], "algorithm_ids": ["quick_sort"], "repeats": 0}),
        ("benchmarks", {"values": [], "algorithm_ids": ["quick_sort"], "repeats": 16}),
        ("benchmarks", {"values": [], "algorithm_ids": ["quick_sort"], "warmups": 4}),
        (
            "benchmark-suites",
            {"algorithm_ids": ["quick_sort"], "sizes": [1, 2, 3], "distributions": DISTRIBUTIONS},
        ),
        (
            "benchmark-suites",
            {"algorithm_ids": ["quick_sort"], "sizes": [1, 1], "distributions": ["random"]},
        ),
        (
            "benchmark-suites",
            {"algorithm_ids": ["quick_sort"], "sizes": [1], "distributions": ["random", "random"]},
        ),
    ],
)
def test_documented_limits_are_enforced_over_http(
    client: TestClient,
    endpoint: str,
    payload: dict[str, object],
) -> None:
    assert_error(client.post(f"/api/v1/{endpoint}", json=payload), 422)


def test_frequency_limit_uses_span_rather_than_value_magnitude(client: TestClient) -> None:
    response = client.post(
        "/api/v1/sort",
        json={
            "values": [-(10**9) + 1, -(10**9)],
            "algorithm_ids": ["frequency_sort"],
        },
    )
    assert response.status_code == 200
    assert response.json()["results"][0]["output_values"] == [-(10**9), -(10**9) + 1]


def test_trace_size_boundary_allows_128_elements(client: TestClient) -> None:
    response = client.post(
        "/api/v1/sort",
        json={
            "values": [0] * 128,
            "algorithm_ids": ["bubble_sort"],
            "trace": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["results"][0]["output_values"] == [0] * 128
    assert isinstance(response.json()["results"][0]["events"], list)


def test_benchmark_json_keeps_timing_separate_from_trace_and_metrics(client: TestClient) -> None:
    values = [4, -2, 1, 4, 0, -2]
    ids = ["bubble_sort", "frequency_sort"]
    traced = client.post(
        "/api/v1/sort",
        json={
            "values": values,
            "algorithm_ids": ids,
            "trace": True,
        },
    ).json()
    response = client.post(
        "/api/v1/benchmarks",
        json={
            "values": values,
            "algorithm_ids": ids,
            "repeats": 3,
            "warmups": 2,
            "seed": 6,
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["input_values"] == values
    assert result["seed"] == 6
    assert result["repeats"] == 3
    assert result["warmups"] == 2
    for row, trace_row in zip(result["results"], traced["results"], strict=True):
        assert row["output_values"] == sorted(values)
        assert row["metrics"] == trace_row["metrics"]
        assert "events" not in row
        assert row["samples_ns"] == [100, 100, 100]
        assert row["median_ns"] == row["min_ns"] == row["max_ns"] == 100
        assert row["spread_ns"] == 0
    assert result["fastest_algorithm_ids"] == ids
    assert result["noise_warning"] is True


def test_suite_matrix_is_reproducible_and_cases_use_identical_data(client: TestClient) -> None:
    payload = {
        "algorithm_ids": ["quick_sort", "heap_sort"],
        "sizes": [0, 8],
        "distributions": ["random", "reversed"],
        "minimum": -10,
        "maximum": 10,
        "repeats": 2,
        "warmups": 0,
    }
    response = client.post("/api/v1/benchmark-suites", json=payload)
    assert response.status_code == 200, response.text
    suite = response.json()
    repeated = client.post("/api/v1/benchmark-suites", json={**payload, "seed": suite["seed"]})
    assert repeated.json() == suite
    assert len(suite["cases"]) == 4
    assert [case["dataset"]["size"] for case in suite["cases"]] == [0, 0, 8, 8]
    for case in suite["cases"]:
        dataset, benchmark = case["dataset"], case["benchmark"]
        assert benchmark["input_values"] == dataset["values"]
        assert benchmark["seed"] == dataset["seed"]
        assert all(
            row["output_values"] == sorted(dataset["values"]) for row in benchmark["results"]
        )


def test_suite_http_response_matches_application_contract(client: TestClient) -> None:
    spec = SuiteSpec(["quick_sort"], [2], ["few_unique"], seed=11, repeats=1, warmups=0)
    response = client.post("/api/v1/benchmark-suites", json=asdict(spec))
    expected = ExperimentService(build_registry(), FakeClock()).suite(spec)
    assert response.status_code == 200
    assert response.json() == asdict(expected)


def test_openapi_exposes_typed_responses_and_request_validation(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "AlgoLab API"
    response_types = {
        "/api/v1/datasets": "DatasetResult",
        "/api/v1/sort": "SortExperiment",
        "/api/v1/benchmarks": "BenchmarkResult",
        "/api/v1/benchmark-suites": "BenchmarkSuiteResult",
    }
    for path, name in response_types.items():
        operation = schema["paths"][path]["post"]
        success = operation["responses"]["200"]["content"]["application/json"]["schema"]
        assert success["$ref"].endswith("/" + name)
        for status in ("404", "413", "422", "500", "503"):
            error = operation["responses"][status]["content"]["application/json"]["schema"]
            assert error["$ref"].endswith("/ErrorResponse")
    schemas = schema["components"]["schemas"]
    assert "writes" in schemas["OperationMetrics"]["properties"]
    assert "samples_ns" in schemas["AlgorithmBenchmark"]["properties"]
    assert schemas["SortRequest"]["additionalProperties"] is False
    assert client.get("/docs").status_code == 200


@pytest.mark.parametrize(
    "failure,code",
    [
        (ExecutionBusy("Busy"), "execution_busy"),
        (ExecutionUnavailable("Unavailable"), "execution_unavailable"),
    ],
)
@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("sort", {"values": [], "algorithm_ids": ["quick_sort"]}),
        ("benchmarks", {"values": [], "algorithm_ids": ["quick_sort"]}),
        (
            "benchmark-suites",
            {"algorithm_ids": ["quick_sort"], "sizes": [0], "distributions": ["random"]},
        ),
    ],
)
def test_execution_capacity_failures_have_retryable_http_errors(
    failure: Exception,
    code: str,
    endpoint: str,
    payload: dict[str, object],
) -> None:
    with TestClient(create_app(LocalRunner(failure))) as client:
        response = client.post(f"/api/v1/{endpoint}", json=payload)
        assert_error(response, 503, code)
        assert response.headers["Retry-After"] == "1"
        assert client.get("/health").status_code == 200


def test_oversized_body_is_rejected_before_json_parsing_or_execution(
    client: TestClient,
    runner: LocalRunner,
) -> None:
    response = client.post(
        "/api/v1/sort", content=b" " * 1_000_001, headers={"Content-Type": "application/json"}
    )
    assert_error(response, 413, "request_too_large")
    assert runner.calls == 0


@pytest.mark.parametrize(
    "failure,code",
    [
        (InvalidResult("Internal algorithm detail"), "invalid_algorithm_result"),
        (RuntimeError("Internal algorithm detail"), "internal_error"),
    ],
)
def test_server_failures_do_not_expose_internal_error_details(
    failure: Exception,
    code: str,
) -> None:
    with TestClient(create_app(LocalRunner(failure)), raise_server_exceptions=False) as client:
        response = client.post(
            "/api/v1/sort",
            json={
                "values": [2, 1],
                "algorithm_ids": ["quick_sort"],
            },
        )
    assert_error(response, 500, code)
    assert "Internal algorithm detail" not in response.text


def test_suite_aggregate_cost_limit_is_visible_as_http_error(client: TestClient) -> None:
    response = client.post(
        "/api/v1/benchmark-suites",
        json={
            "algorithm_ids": ["bubble_sort", "insertion_sort"],
            "sizes": [1000],
            "distributions": DISTRIBUTIONS,
            "repeats": 5,
            "warmups": 1,
            "seed": 7,
        },
    )
    assert_error(response, 422, "limit_exceeded")
