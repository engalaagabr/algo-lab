from algolab.algorithms import build_registry
from algolab.application.services import ExperimentService
from algolab.infrastructure.clock import PerformanceClock


def build_service() -> ExperimentService:
    return ExperimentService(build_registry(), PerformanceClock())
