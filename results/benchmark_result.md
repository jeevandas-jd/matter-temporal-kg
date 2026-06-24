# Benchmark Report — Edge Resource Usage
## Phase 4, Task 8–9: Memory and Latency Benchmarking

**Status:** Complete
**Dataset:** 600 SimuHome benchmark episodes
**Hardware:** Development laptop (not yet validated on physical edge hardware — see Limitations)

---

## 1. Purpose

This benchmark measures the resource cost of ingesting a full SimuHome episode
into the proposed temporal knowledge graph and answering a representative query
against it. The goal is to provide quantitative evidence for the project's
central claim: that a Matter-aligned temporal knowledge graph can run within
the memory and latency constraints of a constrained edge smart-home hub,
unlike a server-based graph database such as Neo4j.

---

## 2. Methodology

Each of the 600 SimuHome episodes was processed independently (no cross-episode
state was carried over, consistent with the project's controlled-experiment
design — see `docs/scope.md`, Section 5). For each episode:

1. The raw episode JSON was loaded from disk.
2. `parse_episode()` converted it into the full node/edge graph structure.
3. `GraphStore.load_episode()` ingested the result into in-memory dictionaries.
4. Peak memory consumption during steps 2–3 was measured using Python's
   `tracemalloc` module.
5. Wall-clock ingestion time was measured using `time.perf_counter()`.
6. One representative query (`get_active_intervals()` for the first room in
   the episode) was timed to measure query latency on the resulting graph.

No database server, network call, or external process was involved at any
point — the entire pipeline runs as in-process Python using only standard
library data structures (dicts and lists).

---

## 3. Results

| Metric | Average | Median | Maximum |
|---|---|---|---|
| Ingest time (ms) | 7.572 | 7.551 | 11.166 |
| Peak memory (KB) | 291.19 | 290.15 | 417.06 |
| Query time (ms) | 0.0353 | 0.0321 | 0.1638 |

**Sample size:** n = 600 episodes
**Success rate:** 600 / 600 (100%) — no ingestion failures across the full dataset
**Typical episode size:** ~26–31 devices across 5 rooms

---

## 4. Interpretation

### 4.1 Memory footprint

The full temporal knowledge graph for an average smart home (≈30 devices,
5 rooms, all associated clusters and state intervals) consumes under 300 KB
of peak memory, with a worst case across 600 episodes of 417 KB. For context,
this is approximately **0.08% of the RAM available on a Raspberry Pi Zero**
(512 MB), one of the most resource-constrained boards commonly used for
edge/IoT hub deployments. A Neo4j server, by comparison, requires a persistent
server process with a baseline memory footprint typically in the hundreds of
megabytes before any data is stored — three orders of magnitude greater than
the entire graph produced by this system.

### 4.2 Ingestion latency

A full home snapshot is parsed and loaded into a queryable graph structure in
single-digit milliseconds (7.6 ms average, 11.2 ms worst case). This is fast
enough to treat ingestion as effectively instantaneous relative to human-scale
smart-home events (the fastest plausible real-world device state change —
a light switch toggle — occurs on a timescale of hundreds of milliseconds at
minimum).

### 4.3 Query latency

Queries against the loaded graph return in well under one millisecond on
average (0.035 ms), confirming that the O(1) dictionary-based lookup design
(Phase 2) delivers on its intended purpose. This is fast enough to support
real-time agent reasoning loops without the graph layer becoming a bottleneck.

### 4.4 Reliability

All 600 episodes were ingested successfully with zero errors, indicating the
ingestion pipeline (Phase 2) generalizes robustly across the full variety of
room counts, device counts, and device types present in the SimuHome benchmark
set, not just the examples used during development.

---

## 5. Comparison context (qualitative)

| | This system | Neo4j (prior approach) |
|---|---|---|
| Runtime dependency | None — pure Python in-process | Requires a running database server |
| Baseline memory overhead | None (no server) | Typically hundreds of MB minimum |
| Per-episode graph memory | ~291 KB average | Not directly comparable — server-resident, not per-episode |
| Deployment on Pi Zero–class hardware | Feasible | Not feasible |

*Note: a direct head-to-head memory benchmark against the team's prior Neo4j
implementation has not yet been run and is recommended as follow-up work
(see Limitations).*

---

## 6. Limitations

- **No physical edge hardware validation yet.** All measurements were taken
  on a development laptop. The relative memory/latency figures are accurate
  and hardware-independent, but a single confirmatory run on actual
  constrained hardware (e.g. Raspberry Pi) would strengthen the edge-viability
  claim for the final paper.
- **No direct Neo4j memory benchmark yet run on the same 600 episodes.** This
  report establishes the proposed system's footprint in isolation; a
  side-by-side measurement against the Neo4j baseline is needed to make the
  comparison quantitative rather than qualitative.
- **Memory measurement covers ingestion only**, not sustained operation under
  the three-tier hot/episodic/semantic memory architecture (Phase 4, Tasks
  3–7), which has not yet been benchmarked and may show different
  characteristics once update traffic and tier transitions are included.
- **Single representative query per episode.** Latency was measured using
  one query type (`get_active_intervals`); `state_at` and `did_overlap` were
  not benchmarked at this scale and may have different performance profiles.

---

## 7. Raw data

Full per-episode results (all 600 entries) are stored at:
`results/benchmark_results.json`

This file is suitable for generating additional charts (e.g. memory vs. device
count scatter plot, latency distribution histogram) for the final report or
publication.
