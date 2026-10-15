from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

IntegerValue = Annotated[int, Field(strict=True, ge=-1_000_000_000, le=1_000_000_000)]
Seed = Annotated[int, Field(strict=True, ge=0, le=4_294_967_295)]
Size = Annotated[int, Field(strict=True, ge=0, le=10000)]
AlgorithmId = Annotated[str, Field(strict=True, min_length=1, max_length=64)]
Distribution = Literal["random", "sorted", "reversed", "nearly_sorted", "few_unique"]


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DatasetRequest(RequestModel):
    size: Size = 50
    minimum: IntegerValue = 1
    maximum: IntegerValue = 100
    distribution: Distribution = "random"
    seed: Seed | None = None

    @model_validator(mode="after")
    def ordered_range(self) -> Self:
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self


class SortRequest(RequestModel):
    values: Annotated[list[IntegerValue], Field(max_length=10000)]
    algorithm_ids: Annotated[list[AlgorithmId], Field(min_length=1, max_length=10)]
    trace: StrictBool = False

    @model_validator(mode="after")
    def unique_algorithms(self) -> Self:
        if len(set(self.algorithm_ids)) != len(self.algorithm_ids):
            raise ValueError("algorithm_ids must be unique")
        return self


class BenchmarkRequest(RequestModel):
    values: Annotated[list[IntegerValue], Field(max_length=10000)]
    algorithm_ids: Annotated[list[AlgorithmId], Field(min_length=1, max_length=10)]
    repeats: Annotated[int, Field(strict=True, ge=1, le=15)] = 5
    warmups: Annotated[int, Field(strict=True, ge=0, le=3)] = 1
    seed: Seed | None = None

    @model_validator(mode="after")
    def unique_algorithms(self) -> Self:
        if len(set(self.algorithm_ids)) != len(self.algorithm_ids):
            raise ValueError("algorithm_ids must be unique")
        return self


class SuiteRequest(RequestModel):
    algorithm_ids: Annotated[list[AlgorithmId], Field(min_length=1, max_length=10)]
    sizes: Annotated[list[Size], Field(min_length=1, max_length=12)]
    distributions: Annotated[list[Distribution], Field(min_length=1, max_length=5)]
    minimum: IntegerValue = 1
    maximum: IntegerValue = 100
    seed: Seed | None = None
    repeats: Annotated[int, Field(strict=True, ge=1, le=15)] = 5
    warmups: Annotated[int, Field(strict=True, ge=0, le=3)] = 1

    @model_validator(mode="after")
    def consistent_suite(self) -> Self:
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        if len(self.sizes) * len(self.distributions) > 12:
            raise ValueError("A suite supports at most 12 size/distribution combinations")
        for name, values in (
            ("algorithm_ids", self.algorithm_ids),
            ("sizes", self.sizes),
            ("distributions", self.distributions),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must be unique")
        return self


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
