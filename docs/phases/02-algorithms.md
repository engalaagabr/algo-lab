# Phase 02 — instrumented sorting algorithms

## Delivered

- Ten independent modules: Selection, Bubble, Odd-Even, Cocktail, Insertion, Binary
  Insertion, Frequency (ascending Counting Sort), Shell, Heap, and Quick.
- `algolab.algorithms.build_registry()` wires each implementation to immutable metadata,
  preserving stable snake_case identifiers and exposing its exact variant and limits.
- Common `SortContext` operations drive key comparisons, mutations, logical auxiliary
  writes, and complete replayable traces. Raw execution uses the same implementation.
- Frequency supports negative integers and bounds its inclusive integer span at 100,000.
- Quick uses median-of-three three-way partitioning and an explicit smaller-first stack;
  Heap uses an iterative heap; neither depends on Python recursion depth.
- Conservative element limits are 1,000 for quadratic/gap-sensitive algorithms and
  10,000 for Heap, Quick, and Frequency.

## Architecture boundary

Concrete algorithms depend on domain contracts only. They mutate the caller-owned working
copy, return `None`, and do not choose inputs, time themselves, serve HTTP, manage workers,
or retain mutable state between runs. The application remains responsible for copying the
shared input and enforcing normal per-algorithm size admission. Frequency additionally
guards its histogram allocation in the implementation.

`workload` is an admission estimate rather than a theoretical complexity claim. Phase 4
review found adversarial median-of-three inputs and tightened Quick's admission from the
initial `n_log_n` estimate to `quadratic`. The average complexity remains O(n log n).

## Validation

`tests/unit/test_algorithms.py` provides shared checks for all ten algorithms:

- Empty, singleton, sorted, reversed, negative, duplicate, alternating, and all-equal data.
- Exhaustive short arrays over three values and reproducible random arrays, checked
  against Python's sorted output and raw/counted equivalence.
- Caller-owned working-copy behavior with the original preserved.
- Complete event replay with valid source indices and event/metric consistency.
- Known two-element counts, no operations for trivial inputs, and explicit trace overflow.
- Frequency's negative offsets, exact span boundary, preallocation rejection, and histogram
  write counts.
- Inputs at the 10,000-element declared limit for Heap, Quick, and Frequency; duplicate-heavy
  and ordered inputs exercise nonrecursive behavior.
- Quick's pending-stack accounting and linear all-equal comparison count.

Run from the repository root after integration:

```bash
python -m pytest tests/unit/test_algorithms.py
ruff check src/algolab/algorithms tests/unit/test_algorithms.py
mypy src/algolab
```

The isolated phase check passed 367 tests, Ruff, and strict mypy for all 11 algorithm
package source files against the current domain contracts. Full application integration
checks remain part of the integrating branch's validation.

See [Algorithm variants and extension guide](../ALGORITHMS.md) for complexity assumptions,
metric conventions, primary-source references, and the steps for adding another algorithm.
