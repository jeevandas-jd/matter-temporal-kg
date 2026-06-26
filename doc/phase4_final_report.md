# Phase 4 Final Report — Edge Optimization

**Status:** Complete
**Project:** Matter-Based Temporal Knowledge Graph for Edge Smart Home Reasoning

---

## 1. Objective

Phase 4 addresses the project's central engineering claim: that the temporal
knowledge graph built in Phases 1–3 can operate within the memory, latency,
and storage constraints of a constrained edge smart-home hub. This phase
implements interval coalescing, a three-tier memory architecture
(hot/episodic/semantic), interval compression for long-term storage, disk
persistence, and full-scale benchmarking against the SimuHome dataset.

---

## 2. Work Completed

### 2.1 State coalescing (`update_state()`)

A single function governs all mutation of the graph after initial ingestion.
Given an incoming `(cluster_id, attribute_name, value, timestamp)` update, it:

- Creates a new interval if none exists yet for that attribute.
- Does nothing if the value is unchanged from the currently active interval
  (coalescing — avoids fragmenting one continuous state into many redundant
  records).
- Closes the active interval and opens a new one if the value has genuinely
  changed.

A temporal ordering safety check was added after testing exposed a bug (see
Section 4): incoming timestamps earlier than the currently active interval's
`start_time` are rejected with a `ValueError`, preventing logically invalid
intervals (negative duration) from entering the graph. This also guards
against real-world out-of-order event delivery in a live deployment.

**Verification:** A 20-update synthetic test sequence, where the underlying
value only genuinely changed twice, was reduced to exactly 3 stored
intervals — an 85% reduction in storage relative to naive per-update
logging.

### 2.2 Synthetic multi-hour event stream

Since SimuHome episodes are single time-point snapshots rather than
continuous timelines, a synthetic generator (`generate_synthetic_stream()`)
was built to produce a plausible multi-hour sequence of attribute changes
for one fixed device, used specifically to validate tiering and compression
logic. The generator produces:

- A gradual random-walk drift (bounded per-step deltas) to simulate normal
  sensor behavior.
- An optional noise-injection mode that adds brief, high-amplitude spikes
  followed by a return toward the prior trend, simulating sensor glitches —
  used to generate realistic test cases for compression validation.

All generation uses a fixed random seed for reproducibility.

### 2.3 Three-tier memory classification

`TierManager.classify_tier()` assigns every interval to one of three tiers
based on how long ago it closed, relative to the current simulated time:

| Tier | Criterion |
|---|---|
| Hot | Active intervals (`end_time = None`), or closed within the last 20 minutes |
| Episodic | Closed within the last 1 hour (but outside the hot window) |
| Semantic | Closed more than 1 hour ago |

These threshold values (20 min / 1 hr) were chosen as reasonable engineering
defaults rather than empirically derived; this limitation is documented in
`docs/future_work.md`.

**Verification:** Applied to a populated graph built from the synthetic
4-hour stream, the classifier correctly distributed 26 total intervals
across all three tiers with no errors, and produced zero negative-duration
intervals after the timestamp ordering bug fix.

### 2.4 Interval compression (Option C)

For the episodic and semantic tiers, `compress_intervals()` merges
consecutive numeric-valued intervals when **both** of the following hold:

- The candidate interval's duration is below a configurable threshold
  (default 2 minutes), **and**
- Its value differs from the preceding kept interval's value by less than
  a configurable threshold (default 0.3, tested at 0.8).

This dual-condition design (Option C, selected from three alternatives
during design review) avoids two failure modes: erasing short-but-real
spikes, and erasing long-but-trivial drifts. Non-numeric attributes
(boolean/categorical, e.g. `OnOff`) are excluded from this rule, since
"value closeness" is not meaningful for them; their redundancy is already
handled by coalescing in `update_state()`.

`compress_tier()` correctly groups a tier's mixed intervals by
`(cluster_id, attribute_name)` before compressing each group independently,
preventing cross-attribute comparison errors.

**Verification — two test cases:**
- *Negative case:* on the original (non-noisy) synthetic stream, 11
  semantic-tier intervals produced zero merges, since no pair satisfied
  both conditions simultaneously — correctly confirming the function does
  not over-merge genuine drift.
- *Positive case:* on a stream with injected noise spikes, 25 semantic-tier
  intervals were compressed to 18 (28% reduction), with multiple confirmed
  merges of brief, low-amplitude fluctuations, while all genuine value
  changes exceeding the similarity threshold were correctly preserved.

### 2.5 SQLite persistence

A lightweight persistence layer (`src/memory/persistence.py`) stores
episodic and semantic tier intervals in a single-file SQLite database,
requiring no server process — directly addressing the limitation that
motivated replacing Neo4j. Three functions: `init_db()`, `save_intervals()`,
`load_intervals()`. Values are serialized via `json.dumps`/`json.loads` to
preserve type fidelity (bool, int, float, string, null) across the
text-based SQLite column.

**Verification:** Data was saved, then the process was terminated and
restarted independently. The same single row was loaded back with no
duplication and correct value type preservation, confirming both
persistence across restarts and idempotent re-saving via `INSERT OR
REPLACE`.

### 2.6 Full-scale benchmarking

All 600 SimuHome benchmark episodes were processed independently (each
episode ingested into a fresh graph, per the project's controlled-experiment
design) to measure ingestion memory, ingestion latency, and query latency.

| Metric | Average | Median | Maximum |
|---|---|---|---|
| Ingest time (ms) | 7.572 | 7.551 | 11.166 |
| Peak memory (KB) | 291.19 | 290.15 | 417.06 |
| Query time (ms) | 0.0353 | 0.0321 | 0.1638 |

All 600 episodes ingested successfully with zero failures. Full results
are available in `results/benchmark_results.json`, with detailed
interpretation in `results/benchmark_report.md`.

---

## 3. Key Result

The complete temporal knowledge graph for an average SimuHome episode
(~26–31 devices, 5 rooms) occupies under 300KB of memory and responds to
queries in fractions of a millisecond, using only in-process Python data
structures with no database server. This is approximately three orders of
magnitude lighter than the baseline memory overhead of a running Neo4j
server instance, directly supporting the project's central edge-deployment
claim.

---

## 4. Bugs Found and Fixed During This Phase

| Bug | Cause | Fix |
|---|---|---|
| Duplicate `state_interval_id` across devices sharing a cluster name | ID format omitted `device_id`, causing silent overwrite in the graph store dict | Included `device_id` in all interval IDs to guarantee global uniqueness |
| Negative-duration intervals | `update_state()` did not validate that incoming timestamps were chronologically after the active interval's `start_time`; exposed by test data misalignment (synthetic stream starting before episode `base_time`) | Added explicit `ValueError` check rejecting out-of-order timestamps |

Both are documented in detail as Architecture Decision Records and serve as
evidence of the project's testing rigor.

---

## 5. Limitations (see `docs/future_work.md` for full detail)

- Tier transition thresholds (20 min / 1 hr) are fixed defaults, not
  empirically derived or adaptive per room/device type.
- Benchmark comparison against the prior Neo4j implementation is currently
  qualitative (architectural), not a direct measured side-by-side on
  identical episodes.
- All benchmarking was performed on development hardware, not yet validated
  on physical constrained edge hardware (e.g. Raspberry Pi).
- Tiering and pruning have been validated on a single synthetic 4-hour
  scenario, not yet stress-tested under multi-day sustained load.

---

## 6. Next Steps

Phase 5 (Evaluation) — construct scenario-based test cases across common
smart-home situations, compare temporal-graph-based reasoning against a
rule-based baseline, and measure correctness, latency, memory footprint,
and explanation quality as a complete evaluation suite.
