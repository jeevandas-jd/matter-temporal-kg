# Future Work

This document tracks design decisions made for scoping or time reasons during
this project, which are identified as candidates for future research or
engineering work beyond the current thesis/paper.

---

## 1. Adaptive tier transition thresholds

**Current state:** The three-tier memory architecture (hot / episodic /
semantic) uses fixed threshold values to decide when an interval moves
between tiers:

- Hot tier window: 20 minutes
- Episodic tier window: 1 hour

**Limitation:** These values were chosen as reasonable engineering defaults
for prototype validation, not derived empirically. In practice, the right
threshold likely depends on context that varies across a real home:

- **Room volatility** — a kitchen or bathroom may have environmental state
  that changes frequently (temperature, humidity from cooking/showering),
  warranting a longer hot-tier window than a rarely-disturbed utility room.
- **Device type** — a thermostat's state may need different treatment than
  a binary on/off light switch.
- **User behavior patterns** — a home with a regular occupant schedule may
  benefit from different thresholds than one with irregular occupancy.

**Proposed future work:** Investigate empirically-derived or adaptive
threshold selection, potentially per-room or per-device-type, using
observed state-change frequency as a signal. This could be framed as a
follow-up study once sufficient longitudinal SimuHome or real-world data
is available to analyze actual state-change distributions.

---

## 2. Direct quantitative Neo4j comparison

**Current state:** Benchmark results (memory footprint, ingestion latency,
query latency) were measured for the proposed edge TKG across all 600
SimuHome episodes. Comparison against the team's prior Neo4j-based TKG
implementation is currently qualitative (architectural — e.g. "no server
process required") rather than a measured side-by-side benchmark on
identical episodes.

**Proposed future work:** Run the same 600-episode benchmark suite against
the Neo4j implementation and report direct comparative numbers (memory,
ingestion time, query latency) to make the edge-efficiency claim
quantitative rather than architectural.

---

## 3. Physical edge hardware validation

**Current state:** All benchmarking was performed on a development laptop.
Results (e.g. ~291KB average peak memory, ~7.5ms ingestion time) are
hardware-independent relative measurements, but have not been confirmed
on actual constrained hardware.

**Proposed future work:** Re-run the benchmark suite on a representative
edge device (e.g. Raspberry Pi Zero or similar) to report at least one
real hardware data point, strengthening the practical edge-deployability
claim.

---

## 4. LLM / ReAct planning integration

**Current state:** Per the original project plan (Phase 6), natural
language query understanding and tool-call routing is intentionally
deferred and handled by the existing SimuHome agent's LLM-based ReAct
loop, not by the temporal knowledge graph itself. The TKG exposes query
functions (`state_at`, `get_active_intervals`, `did_overlap`) as tools
for that external agent to call.

**Proposed future work:** Once the temporal graph core (Phases 1–5) is
fully validated, extend the system with local LLM or ReAct-style planning
that can call the TKG's query functions directly, as originally scoped
in Phase 6 of the implementation plan.

---

## 5. Agent integration completeness

**Current state:** Initial review of the existing `tkg_agent.py` /
`base_agent.py` / `retriever.py` code (written against the Neo4j backend)
identified the integration points needed to swap in the edge TKG:
an `EdgeTKGRetriever` and `EdgeEpisodeIngestor` class with method
signatures matching the existing `TKGRetriever` / `EpisodeIngestor`
interfaces, backed by `GraphStore` and `update_state()` instead of Neo4j.

**Limitation:** This integration has been scoped and the foundational
piece (`update_state()`) has been built and tested, but the adapter
classes themselves (`EdgeTKGRetriever`, `EdgeEpisodeIngestor`) have not
yet been implemented.

**Proposed future work:** Complete the two adapter classes and run the
existing SimuHome agent end-to-end against the edge TKG backend instead
of Neo4j, to validate real integration (not just isolated unit-level
correctness).

---

## 6. Tiering and pruning under sustained load

**Current state:** Coalescing (Task 2) has been validated showing strong
storage efficiency (20 synthetic updates → 3 stored intervals). The full
three-tier architecture's behavior under sustained, longer-duration load
(e.g. multiple days of continuous operation) has not yet been benchmarked.

**Proposed future work:** Extend the synthetic event stream generator to
simulate multi-day operation across multiple devices simultaneously, and
benchmark memory growth, tier transition overhead, and pruning
effectiveness at that scale.
