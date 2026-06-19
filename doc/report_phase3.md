# Progress Report — Matter-Based Temporal Knowledge Graph for Edge Smart Home Reasoning

**Reporting period:** Phase 1 → Phase 3 (complete)
**Prepared by:** Jeevandas

---

## Summary

Phases 1 through 3 of the implementation plan are complete. The project has moved
from schema design through a working ingestion pipeline to a functioning temporal
reasoning layer with explainability support, all tested against simulated SimuHome
smart-home data.

---

## Phase 1 — Problem Framing and Schema Design 

- Finalized project scope: replacing a previously-built Neo4j-based temporal
  knowledge graph (used in earlier smart-home agent experiments) with a compact,
  Matter-aligned TKG suitable for constrained edge hubs.
- Designed a 6-node graph schema: `User`, `Location`, `Device`, `Cluster`,
  `StateInterval`, `Event` — directly mirroring the Matter device hierarchy
  (Node → Endpoint → Cluster → Attribute) with an added temporal layer on top.
- Defined structural edges (`INSTALLED_IN`, `HAS_CLUSTER`, `HAS_STATE`) and
  temporal edges (`LOCATED_IN` with start/end timestamps).
- Documented the schema with diagrams and an architecture decision record
  explaining why historical state (not just current state) must be preserved
  for temporal reasoning to be possible.

## Phase 2 — Data Modeling and Ingestion 

- Built `parse_device()` — converts a single SimuHome device JSON object into
  graph-ready nodes (Device, Cluster, StateInterval) and edges.
- Built `parse_episode()` — processes a full SimuHome episode (all rooms, all
  devices) into the complete graph structure.
- Implemented value normalization (Matter attributes are scaled ×100 in
  SimuHome; values are corrected on ingestion).
- Built `GraphStore` — an in-memory graph store with O(1) dictionary-based
  lookup by node ID, plus a secondary index (`intervals_by_cluster`) for
  efficient interval queries.
- Verified correctness by manually tracing one device (bathroom air
  conditioner) end-to-end and confirming the code output matched the
  hand-traced expected result.

## Phase 3 — Temporal Reasoning Layer 

- Implemented Allen's interval algebra (`allen.py`): `before`, `meets`,
  `overlaps`, `starts`, `finishes`, `during`, `equals` — 7 of the 13 standard
  relations, sufficient for the project's current query needs.
- Built query functions (`queries.py`):
  - `state_at()` — value of an attribute at a given point in time
  - `get_active_intervals()` — all currently-active states in a room
  - `did_overlap()` — whether two device attributes' active periods overlap
- Added a provenance/explainability layer: every query result now returns
  structured evidence (`make_evidence()`) and a human-readable explanation
  (`explain()`), directly addressing the research question on explainable
  reasoning.
- Found and fixed a real bug during testing: state interval IDs were colliding
  across different devices sharing the same cluster name (e.g. two devices
  both having an "OnOff" cluster), causing silent data loss in the graph
  store. Fixed by including `device_id` in the interval ID to guarantee
  uniqueness — documented as an ADR.

---

## Verification

All three phases were tested using both the full SimuHome benchmark episode
and a minimal hand-constructed test episode (1 room, 2 devices) small enough
to verify every output by hand. All test cases pass as expected.

---

## Current status / next step

Moving into **Phase 4: Edge Optimization** — splitting the graph into
hot/episodic/semantic memory tiers, implementing pruning and interval
coalescing, and benchmarking memory and latency to validate the "edge-ready"
claim central to the project's contribution.

