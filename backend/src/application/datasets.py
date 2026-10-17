from random import Random, SystemRandom

from application.models import DatasetResult, DatasetSpec
from application.validation import (
    MAX_DATASET_SIZE,
    MAX_SEED,
    require_integer,
    validate_distribution,
    validate_range,
    validate_seed,
)


def concrete_seed(seed: int | None) -> int:
    validate_seed(seed)
    return SystemRandom().randrange(MAX_SEED + 1) if seed is None else seed


def generate_dataset(spec: DatasetSpec) -> DatasetResult:
    """Create reproducible integers; the returned seed also reproduces unseeded requests."""
    require_integer(spec.size, "size", 0, MAX_DATASET_SIZE)
    validate_range(spec.minimum, spec.maximum)
    validate_distribution(spec.distribution)
    seed = concrete_seed(spec.seed)
    rng = Random(seed)
    if spec.distribution == "few_unique":
        # At most five unique values; range endpoints are inclusive.
        unique_count = min(5, spec.maximum - spec.minimum + 1)
        choices = rng.sample(range(spec.minimum, spec.maximum + 1), unique_count)
        values = [rng.choice(choices) for _ in range(spec.size)]
    else:
        values = [rng.randint(spec.minimum, spec.maximum) for _ in range(spec.size)]
        if spec.distribution in ("sorted", "nearly_sorted"):
            values.sort()
        elif spec.distribution == "reversed":
            values.sort(reverse=True)
        if spec.distribution == "nearly_sorted" and spec.size > 1:
            # A sorted sample with a small number of random transpositions.
            for _ in range(max(1, spec.size // 20)):
                first, second = rng.sample(range(spec.size), 2)
                values[first], values[second] = values[second], values[first]
    return DatasetResult(values, seed, spec.size, spec.minimum, spec.maximum, spec.distribution)
