from fastapi.testclient import TestClient

from main import create_app


def test_real_process_worker_runs_all_experiment_endpoints_and_preserves_errors():
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200
        identifiers = [item["id"] for item in client.get("/api/v1/algorithms").json()]
        values = [5, -1, 3, 3, 0]
        response = client.post(
            "/api/v1/sort",
            json={"values": values, "algorithm_ids": identifiers, "trace": True},
        )
        assert response.status_code == 200, response.text
        assert len(response.json()["results"]) == 10
        assert all(
            result["output_values"] == sorted(values) for result in response.json()["results"]
        )
        response = client.post(
            "/api/v1/benchmarks",
            json={"values": values, "algorithm_ids": identifiers, "repeats": 2, "seed": 7},
        )
        assert response.status_code == 200, response.text
        assert all(len(result["samples_ns"]) == 2 for result in response.json()["results"])
        response = client.post(
            "/api/v1/benchmark-suites",
            json={
                "algorithm_ids": ["heap_sort", "quick_sort"],
                "sizes": [0, 16],
                "distributions": ["random", "reversed"],
                "repeats": 2,
                "seed": 42,
            },
        )
        assert response.status_code == 200, response.text
        assert len(response.json()["cases"]) == 4
        unknown = client.post("/api/v1/sort", json={"values": [], "algorithm_ids": ["missing"]})
        assert unknown.status_code == 404
        assert unknown.json()["error"]["code"] == "unknown_algorithm"
        limited = client.post(
            "/api/v1/sort",
            json={"values": list(range(129)), "algorithm_ids": identifiers, "trace": True},
        )
        assert limited.status_code == 422
        assert client.get("/health").json()["status"] == "ok"
