# AlgoLab sorting algorithms

Every algorithm sorts a caller-owned `list[int]` into ascending order through `SortContext`.
The application must give each run its own copy of the experiment input. Algorithms do not
copy or retain the shared original, read clocks, generate input, or import API types.
`build_registry()` returns exactly the ten algorithms below, in the listed order.

## Implemented variants and limits

Here `n` is the array length and `k = max(values) - min(values) + 1` for nonempty input.
Complexities describe the chosen variants under the usual constant-cost integer-operation
model; they do not predict elapsed Python time or include the platform's input copies,
metrics objects, or optional trace storage. Empty and singleton arrays return without
counted operations.

| ID | Best | Average | Worst | Auxiliary space | Max size |
| --- | --- | --- | --- | --- | --- |
| `selection_sort` | O(n²) | O(n²) | O(n²) | O(1) | 1,000 |
| `bubble_sort` | O(n) | O(n²) | O(n²) | O(1) | 1,000 |
| `odd_even_sort` | O(n) | O(n²) | O(n²) | O(1) | 1,000 |
| `cocktail_sort` | O(n) | O(n²) | O(n²) | O(1) | 1,000 |
| `insertion_sort` | O(n) | O(n²) | O(n²) | O(1) | 1,000 |
| `binary_insertion_sort` | O(n) | O(n²) | O(n²) | O(1) | 1,000 |
| `frequency_sort` | O(n + k) | O(n + k) | O(n + k) | O(k) | 10,000 |
| `shell_sort` | O(n log n) | Not claimed | O(n²) | O(1) | 1,000 |
| `heap_sort` | O(n), equal keys allowed | O(n log n) | O(n log n) | O(1) | 10,000 |
| `quick_sort` | O(n), all keys equal | O(n log n), random input order | O(n²) | O(log n) | 10,000 |

- **Selection:** scan each unsorted suffix for its minimum, then exchange it into place.
  Equal minima are not exchanged during the scan, but the final nonadjacent exchange makes
  the general algorithm unstable.
- **Bubble:** swap adjacent inversions; the last swap bounds the next pass. Already sorted
  input needs one pass and no writes.
- **Odd-even:** perform an even-indexed pass and then an odd-indexed pass sequentially.
  Stop only after an entire cycle has no swaps. This implementation is not parallel.
- **Cocktail:** alternate forward and backward adjacent-swap passes with shrinking bounds.
  Stop when a pass performs no swaps.
- **Insertion:** hold the next value in a scalar, shift strictly greater values right, and
  insert the held value only when it moved.
- **Binary insertion:** first check whether the value already belongs at the prefix end.
  Otherwise use an upper-bound binary search and shift the suffix. The fast path gives a
  linear sorted-input best case. Binary search reduces key comparisons to O(n log n)
  overall, while shifts can still take quadratic time.
- **Frequency:** count occurrences by value and reconstruct the integer array in ascending
  numeric order. This is **Counting Sort**, not sorting values by occurrence frequency.
  Negative values use an offset from the minimum. A span greater than 100,000 is rejected
  before allocating the histogram; this is an inclusive span, so `[-50000, 49999]` is valid
  and `[-50000, 50000]` is not. Finding the minimum and maximum takes `2(n - 1)` key
  comparisons for `n >= 2`, despite `comparison_based=False`. The implementation rebuilds
  integer values and makes no stability promise for hypothetical records.
- **Shell:** use gaps `n // 2`, `n // 4`, ..., `1`, with gapped insertion. The metadata
  deliberately claims no average-case bound for this gap sequence. Its admission size
  is conservative because the worst case is quadratic.
- **Heap:** build a binary max heap bottom-up, then exchange the root with the last heap
  element and sift down. Sifting stops once heap order holds. Equal keys therefore permit
  a linear best case; the best case for distinct keys is O(n log n).
  [Princeton's heapsort analysis](https://algs4.cs.princeton.edu/24pq/) describes this
  distinction.
- **Quick:** choose the median of the first, middle, and last values, then partition into
  less-than, equal-to, and greater-than regions. An explicit stack replaces recursion.
  Process the smaller region immediately and defer the larger one, bounding pending
  storage by O(log n). All-equal input completes in one partition; adversarial inputs can
  still cause O(n²) time. The stated average assumes random input order, not a randomized
  pivot or a worst-case guarantee. See Princeton's descriptions of
  [three-way partitioning](https://algs4.cs.princeton.edu/23quicksort/index.php) and
  [smaller-partition-first nonrecursive quicksort](https://www.cs.princeton.edu/courses/archive/spr03/cs226/demo/qsort/).

Bubble, odd-even, cocktail, insertion, and binary insertion are stable because they never
move an equal value ahead of another equal value. For plain integers this property is not
observable; it describes the comparison-and-movement rule. Selection, frequency, shell,
heap, and quick make no stability guarantee.

`in_place=True` means the algorithm rearranges the working array without an auxiliary
value array. Quick Sort still needs its explicitly reported O(log n) bookkeeping stack.
Frequency Sort has `in_place=False` because it allocates the O(k) histogram.

The application uses `workload` as an admission estimate: `quadratic` for Quick and the
seven conservatively capped algorithms, `n_log_n` for Heap, and `linear_range` for Frequency.
Quick reserves quadratic work to account for adversarial median-of-three inputs; its
theoretical average remains O(n log n). A hard size limit and the aggregate work budget
both apply, so large repeated Quick experiments may be rejected below 10,000 elements.
Size admission is the application's responsibility; Frequency also checks its allocation
span inside the sort. These admission units are not a hard CPU-time guarantee.

## Metrics and trace semantics

All key comparisons go through `context.compare`, including pivot selection and finding
integer bounds. Index checks, loop bounds, and frequency-counter checks are not key
comparisons. Every main-array mutation goes through `swap` or `write`; no built-in sort
is used as an alternate implementation when instrumentation is disabled.

- A swap exchanges two distinct indices and counts as one swap and two array writes.
  A self-swap is ignored. Exchanging equal values at different indices still counts.
- An explicit main-array assignment counts as one array write. Insertion variants avoid
  a final assignment when the value stayed in its original place.
- Frequency initializes `k` histogram cells and increments `n` cells: `k + n` auxiliary
  writes for a nontrivial input. It then makes `n` main-array writes and no swaps.
- Quick counts each stored pending interval bound: two auxiliary writes per deferred
  interval. Popping bounds removes entries rather than assigning entries. Scalar pivot,
  loop, bound, and insertion-key assignments are excluded.
- The other algorithms use no auxiliary containers, so their auxiliary writes are zero.

Comparison events include operand values and available source indices. A held insertion
key, pivot, or remembered minimum/maximum may no longer have an array source index; these
comparisons identify only the current array operand. Swap event values are the values
after the exchange. Write events carry the assigned value. Auxiliary writes have no
main-array mutation event. Replaying mutation events on the original reconstructs the
final sorted array. Exceeding the configured trace cap raises an explicit error instead
of silently returning an incomplete trace.

`count=False, trace=False` runs the same implementation and still performs context method
calls and disabled-mode checks. Raw timing therefore describes these instrumentable
Python implementations; it is not a measurement of an independent optimized native sort.

## Adding an algorithm

1. Add `backend/src/algorithms/<stable_id>.py` with immutable `metadata` and a typed
   `sort(context: SortContext) -> None`. Depend only on domain contracts and the standard
   library. Keep the implementation free of API, storage, worker, and timing concerns.
2. Use `compare` for input-key comparisons, `swap`/`write` for main-array assignments,
   and `auxiliary_write` for logical auxiliary-container assignments. Document exactly
   what the auxiliary count means. Keep raw and counted execution in the same code path.
3. Describe the actual pivot/gap/heap/counting variant, stability, auxiliary storage,
   assumptions behind average-case claims, size limits, and any allocation-range limit.
   Do not copy another variant's complexity claims. Choose a conservative admission
   workload; add a new workload model only with a corresponding application decision.
4. Register `Algorithm(module.metadata, module.sort)` in `build_registry()`. IDs are public
   API identifiers; do not rename an existing ID without a compatibility decision.
5. Extend the explicit ID and limit expectations in `backend/tests/unit/test_algorithms.py`.
   Run the shared edge cases, exhaustive small inputs, seeded random inputs, original-copy
   isolation, raw/counted equivalence, metric examples, trace replay, and trace-cap checks.
   Add algorithm-specific allocation or large-input tests when needed.

The registry/domain contract lets the application discover a new algorithm without adding
algorithm-specific branches to API routes or benchmark orchestration.
