from time import perf_counter_ns


class PerformanceClock:
    def now_ns(self) -> int:
        return perf_counter_ns()
