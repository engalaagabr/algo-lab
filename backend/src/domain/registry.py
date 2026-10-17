from collections.abc import Iterable

from domain.errors import UnknownAlgorithm
from domain.models import Algorithm, AlgorithmMetadata


class AlgorithmRegistry:
    def __init__(self, algorithms: Iterable[Algorithm]) -> None:
        self._algorithms: dict[str, Algorithm] = {}
        for algorithm in algorithms:
            identifier = algorithm.metadata.id
            if identifier in self._algorithms:
                raise ValueError(f"Duplicate algorithm ID: {identifier}")
            self._algorithms[identifier] = algorithm

    def get(self, identifier: str) -> Algorithm:
        try:
            return self._algorithms[identifier]
        except KeyError:
            raise UnknownAlgorithm(f"Unknown algorithm: {identifier}") from None

    def list_metadata(self) -> list[AlgorithmMetadata]:
        return [algorithm.metadata for algorithm in self._algorithms.values()]
