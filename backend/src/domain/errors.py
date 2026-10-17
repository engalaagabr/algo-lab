class DomainError(Exception):
    """An expected, safe-to-expose experiment failure."""

    code = "invalid_experiment"


class UnknownAlgorithm(DomainError):
    code = "unknown_algorithm"


class LimitExceeded(DomainError):
    code = "limit_exceeded"


class TraceLimitExceeded(LimitExceeded):
    code = "trace_limit_exceeded"


class InvalidResult(DomainError):
    code = "invalid_algorithm_result"
