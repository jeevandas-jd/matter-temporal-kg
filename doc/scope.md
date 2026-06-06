# Project Scope — Matter-Based Temporal Knowledge Graph for Edge Smart Home Reasoning

**Document status:** Finalized  
**Last updated:** 2025-08  
**Authors:** [Your name]

---

## 1. One-sentence scope statement

Design, implement, and evaluate a compact Matter-aligned temporal knowledge graph that replaces a Neo4j-based TKG as the knowledge layer of an existing smart home agent, enabling the same temporal reasoning capability to run on a constrained edge hub.

---

## 2. Background and motivation

### 2.1 Prior work this project builds on

This project is not a new agent from scratch. A smart home agent was previously built and tested using [SimuHome](https://github.com/[your-repo]), a simulated smart home environment that generates benchmark episodes. In those experiments, the agent used Neo4j as its temporal knowledge graph backend. The agent received a natural language query and a full home snapshot, reasoned over the TKG, issued tool calls (e.g. `get_room_states`, `set_device`), and was evaluated against expected actions and goal states.

Those experiments confirmed that a TKG-based reasoning approach works correctly. The problem is that Neo4j is a server-grade graph database — it requires significant RAM, a running server process, and network access — making it unsuitable for deployment on constrained edge hardware such as a Raspberry Pi-class hub.

### 2.2 The gap this project fills

Matter standardizes device-level interoperability but provides no high-level memory structure for temporal reasoning. Neo4j fills that gap well in a server environment but not at the edge. This project fills the gap between the two: a TKG that is Matter-aligned, temporally expressive, and edge-deployable.

---

## 3. What is in scope

### 3.1 Core system

| Component | Description |
|---|---|
| Matter-aligned graph schema | Formal mapping of Matter's device hierarchy (Node → Endpoint → Cluster → Attribute) into temporal graph entities |
| Temporal entity layer | StateInterval, ActivityInterval, Event, UserContext, Routine nodes on top of the structural graph |
| Allen interval reasoning engine | Implementation of the 13 Allen interval relations for qualitative temporal queries |
| Three-tier memory model | Hot graph (in-memory, recent context) · Episodic store (compressed short-term) · Semantic layer (long-term routines) |
| SimuHome ingestion pipeline | Parser that reads SimuHome JSON episode snapshots and populates the TKG |
| Query interface | Functions answering questions such as: which device states overlapped with occupancy, what changed before a comfort request, which events occurred during a weather condition |
| Provenance links | Explainability edges so every inferred state or action can be traced back to evidence |

### 3.2 Evaluation

| Item | Description |
|---|---|
| Benchmark dataset | SimuHome — 600 episodes, seed-controlled, 5 rooms, 26 devices, multiple query types |
| Metrics | Tool-call correctness · goal-state match · query latency · memory footprint · explanation quality |
| Baseline comparison | Rule-based automation system on the same episodes |
| Controlled experiment | Only the TKG layer changes between Neo4j baseline and the edge TKG; the agent, simulator, and evaluator remain identical |

### 3.3 Documentation and research output

- Architecture decision records (ADRs) for every major design choice
- Formal schema specification
- Experiment logs with config, results, and interpretation for every benchmark run
- Research paper / thesis as the primary written deliverable

---

## 4. What is out of scope

The following are explicitly deferred to future work and will not be implemented in this project.

| Excluded item | Reason |
|---|---|
| Real Matter hardware | All experiments use SimuHome simulated data; physical deployment is a future validation step |
| LLM / ReAct planning integration | The temporal graph core must be stable before adding an LLM reasoning layer |
| Cloud synchronization or multi-hub federation | Out of the constrained edge deployment model |
| Full OWL ontology or SPARQL | A custom compact schema is preferred over a heavyweight semantic web stack for edge constraints |
| Voice or natural language interface | The agent interface is already handled by the existing system |
| User-facing dashboard or UI | Not required for the research contribution |

---

## 5. The controlled experiment framing

The paper's central empirical claim is:

> A Matter-aligned temporal knowledge graph with Allen interval reasoning achieves comparable or better correctness on SimuHome benchmark episodes compared to the Neo4j-based TKG, while operating within edge memory and latency constraints that Neo4j cannot meet.

The experimental design is a clean swap:

```
SimuHome 600 episodes
        │
        ├─── Agent + Neo4j TKG   →  scores (baseline)
        │
        └─── Agent + Edge TKG    →  scores + latency + memory (proposed)
```

Everything except the TKG layer is held constant. This isolation is what makes the comparison scientifically valid.

---

## 6. SimuHome data model (relevant to TKG schema)

SimuHome episodes provide the following structure that the TKG must ingest:

```
Episode
├── meta          (seed, query_type, num_rooms, num_devices)
├── query         (natural language question)
├── user_location (current room of the user)
├── eval
│   ├── required_actions  (expected tool calls with params)
│   └── goals             (expected room/device state values)
└── initial_home_config
    ├── tick_interval
    ├── base_time
    └── rooms
        └── <room_id>
            ├── state     (temperature, humidity, illuminance, pm10)
            └── devices
                └── <device>
                    ├── device_id
                    ├── device_type
                    └── attributes  (Matter cluster attributes, e.g. 1.Thermostat.LocalTemperature)
```

**Note on attribute encoding:** Matter attribute values in SimuHome are scaled by 100 (e.g. `LocalTemperature: 2265` = 22.65 °C). The TKG ingestion layer must normalize these before storing.

---

## 7. Scope boundaries summary

| Question | Answer |
|---|---|
| Is this a new agent? | No. It replaces one component (the TKG) of an existing agent. |
| What is the primary deliverable? | A research paper / thesis backed by a working implementation. |
| What hardware does it run on? | Simulated edge environment (constrained memory/CPU budget); no physical device required. |
| What is the data source? | SimuHome simulator (600 benchmark episodes, simulated Matter devices). |
| What is the comparison baseline? | The same agent running with Neo4j as the TKG backend. |
| What makes this a research contribution? | Novel schema mapping Matter → temporal KG + Allen reasoning, proven viable on edge constraints. |
