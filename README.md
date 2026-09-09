# rill

A stream processing engine, and the toolkit a stream processing engine is built from.

`rill` began as the machinery for moving unbounded event streams through time
correctly: watermarks, event-time windows, exactly-once delivery, backpressure,
dedup. Following those honestly led everywhere they lead in a real system. A
stream engine that survives needs the distributed-systems protocols underneath
it, the resilience patterns around it, the probabilistic sketches that keep its
state bounded, the numerical methods that summarize its metrics, and the graph,
dynamic-programming, string, and data-structure algorithms its operators stand
on. So the package is broad on purpose, and every corner of it earns its place
by being measured rather than asserted.

## The method

Every module was built the same way, and the discipline is the point:

- **A measured finding, not a claim.** Each module's docstring states what the
  code does and, where a first guess turned out wrong, keeps the wrong guess
  beside the measured truth. The correction is the most trustworthy sentence in
  the file. Merge sort is stable and the in-place sorts are not; the alias
  sampler is exact, not an approximation of the weighted draw; Simpson's rule is
  exact through cubics, not just quadratics; coordinate compression keeps order
  exactly and destroys distance. These are things the tests actually checked.

- **Tests lock the number or check against brute force.** Where there is a real
  measured value, a test pins it. Where there is a reference implementation, a
  property test runs the fast method and the obvious one on thousands of random
  inputs and asserts they agree: Manacher against expand-around-center, the
  suffix array against sorted suffixes, Dinic against Edmonds-Karp, the Hungarian
  assignment against the brute permutation minimum, Johnson against
  Floyd-Warshall, meet-in-the-middle against the full two-to-the-n enumeration.

- **Witnesses re-testify.** Under `rill/witnesses/` a set of depositions rebuild
  scenarios from the real modules and report numbers rather than adjectives, each
  carrying a `holds` flag the registry gates on. They are the standing evidence
  that the findings still hold when the organs run together.

- **Typed refusals.** Every module refuses bad input through the shared error
  types in `rill/errors.py`. A modular inverse that does not exist, a negative
  cycle, an odd interval count for Simpson, contradictory congruences for the
  Chinese remainder theorem: the honest response is to refuse, not to return a
  wrong number.

## By the numbers

- 30,000+ strict lines of code (excluding docstrings, comments, and blanks)
- 340 modules under `rill/`
- 2,167 tests, all green
- 22 witnesses, none broken
- ruff clean across the whole tree

## Quickstart

```python
from rill.aliasmethod import AliasSampler
from rill.suffixarray import suffix_array, search
from rill.dinic import Dinic

# constant-time weighted sampling
import random
rng = random.Random(0)
sampler = AliasSampler([1.0, 3.0, 6.0])
draws = [sampler.draw(rng.randrange, rng.random) for _ in range(1000)]

# all occurrences of a pattern via the suffix array
sa = suffix_array("banana")
print(search("banana", "ana", sa))          # [1, 3]

# maximum flow
d = Dinic(4)
for u, v, c in [(0, 1, 3), (0, 2, 2), (1, 2, 1), (1, 3, 2), (2, 3, 4)]:
    d.add_edge(u, v, c)
print(d.max_flow(0, 3))                       # 5
```

Run the witnesses and see the evidence:

```bash
python -m rill.cli summary   # 22 witnesses (0 broken)
python -m rill.cli check     # all witnesses hold
```

## What is inside

- **Streaming**: watermarks and generation, event-time reordering, windows
  (tumbling, hopping, sliding, session, global), exactly-once and dedup,
  backpressure, salting hot keys, checkpoints and savepoints, retractions,
  triggers, pipeline throughput.
- **Distributed systems**: CRDTs (counters, sets, registers), vector clocks and
  causal delivery, Raft commit rule, two-phase commit, Chandy-Lamport snapshots,
  leases and fencing tokens, quorums, read repair, hinted handoff, consistent
  hashing (ring, rendezvous, jump).
- **Resilience**: circuit breakers, backoff with jitter, hedged requests,
  bulkheads, AIMD and gradient limiters, GCRA and leaky-bucket rate limiting,
  visibility timeouts.
- **Sketches and sampling**: HyperLogLog, DGIM, reservoir and weighted reservoir,
  Morris counter, count sketch, MinHash, SimHash, Misra-Gries, Bloom and cuckoo
  filters, the alias method.
- **Numerical**: Welford variance, Kahan summation, EWMA with bias correction,
  online regression, Holt smoothing, root finding, Simpson integration, USL and
  Amdahl/Gustafson scaling.
- **Graphs**: Dijkstra, Bellman-Ford, Floyd-Warshall, Johnson, MST, bipartite
  matching, max flow (Edmonds-Karp and Dinic), SCC, bridges and articulation
  points, topological sort, LCA, Euler tour, Hierholzer trails, the Hungarian
  assignment.
- **Strings**: Rabin-Karp, KMP, the Z-algorithm, Horspool, Aho-Corasick,
  Manacher, Booth's least rotation, suffix array and Kasai LCP.
- **Algorithms and data structures**: segment trees, Fenwick trees, sparse
  tables, sqrt decomposition, tries and the XOR trie, skip lists, treaps,
  union-find with rollback, Mo's algorithm, knapsack and coin change, LIS and
  LCS, edit distance, Kadane, matrix exponentiation, number theory (extended
  Euclid, modular inverse, Chinese remainder theorem, the linear sieve),
  coordinate compression, Gray codes, next permutation, and the classic sorts.

## Layout

```
rill/            the modules
rill/errors.py   the shared typed refusals every module imports
rill/witnesses/  depositions that re-measure the findings, plus the registry
rill/cli.py      summary and check over the witnesses
tests/           one test file per module, locking measured numbers
```
