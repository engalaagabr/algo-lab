from domain.errors import DomainError, LimitExceeded

MAX_DATASET_SIZE = 10_000
MAX_INTEGER_MAGNITUDE = 1_000_000_000
MAX_SEED = 2**32 - 1
MAX_ALGORITHMS = 10
MAX_TRACE_SIZE = 128
MAX_TRACE_EVENTS = 20_000
MAX_SUITE_CASES = 12
# Conservative admission units, not a runtime estimate or algorithm complexity claim.
MAX_WORK_UNITS = 50_000_000
DISTRIBUTIONS = ("random", "sorted", "reversed", "nearly_sorted", "few_unique")


def require_integer(value: int, name: str, lower: int, upper: int) -> None:
    # bool is an int subclass, but is not a valid dataset value or setting.
    if type(value) is not int:
        raise DomainError(f"{name} must be an integer.")
    if not lower <= value <= upper:
        raise LimitExceeded(f"{name} must be between {lower} and {upper}.")


def validate_seed(seed: int | None) -> None:
    if seed is not None:
        require_integer(seed, "seed", 0, MAX_SEED)


def validate_values(values: list[int]) -> None:
    if not isinstance(values, list):
        raise DomainError("values must be a list of integers.")
    require_integer(len(values), "dataset size", 0, MAX_DATASET_SIZE)
    for value in values:
        require_integer(value, "dataset value", -MAX_INTEGER_MAGNITUDE, MAX_INTEGER_MAGNITUDE)


def validate_distribution(distribution: str) -> None:
    if not isinstance(distribution, str) or distribution not in DISTRIBUTIONS:
        raise DomainError(f"distribution must be one of: {', '.join(DISTRIBUTIONS)}.")


def validate_range(minimum: int, maximum: int) -> None:
    require_integer(minimum, "minimum", -MAX_INTEGER_MAGNITUDE, MAX_INTEGER_MAGNITUDE)
    require_integer(maximum, "maximum", -MAX_INTEGER_MAGNITUDE, MAX_INTEGER_MAGNITUDE)
    if minimum > maximum:
        raise DomainError("minimum must be less than or equal to maximum.")


def validate_repetitions(repeats: int, warmups: int) -> None:
    require_integer(repeats, "repeats", 1, 15)
    require_integer(warmups, "warmups", 0, 3)


def check_work_budget(units: int) -> None:
    if units > MAX_WORK_UNITS:
        raise LimitExceeded(
            "Experiment exceeds the work budget; reduce array sizes, algorithms, "
            "repetitions, or suite cases."
        )
