Good. Here's the complete Phase 4 task list, broken into the order we'll tackle them.

---

## Phase 4 — Edge Optimization: Full Task List

| # | Task | What it does | Depends on |
|---|---|---|---|
| **1** | `update_state()` | Core function: close/reopen intervals on real change, no-op on unchanged value. Foundation for everything else, including future agent integration. | Nothing — start here |
| **2** | Interval coalescing verification | Write a synthetic test: feed many repeated/changing values through `update_state()` and confirm interval count stays minimal, not 1-per-tick. | Task 1 |
| **3** | Synthetic multi-hour event stream generator | Take ONE fixed home config and generate a realistic sequence of state changes over several hours (e.g. AC cycling on/off, temperature drifting). This is the dataset for tiering demos. | Task 1 |
| **4** | Three-tier memory architecture | Split storage into Hot (RAM, recent), Episodic (SQLite, short-term history), Semantic (SQLite, long-term summaries/routines). | Tasks 1–3 |
| **5** | Tier transition policy | Decide and implement: when does a hot interval age into episodic? When does episodic get summarized into semantic? (e.g. age-based threshold) | Task 4 |
| **6** | Pruning / compression logic | When intervals move to episodic/semantic tier, compress: drop short-lived noise, merge consecutive similar values, summarize repeated routines. | Task 4, 5 |
| **7** | SQLite persistence layer | Implement actual read/write to a `.db` file for episodic and semantic tiers — schema design + save/load functions. | Task 4 |
| **8** | Benchmarking harness | Run all 600 SimuHome episodes independently (Option A from earlier), measure: memory footprint per episode, query latency per function call. | Independent of 4–7, can run anytime after Task 1 |
| **9** | Benchmark report | Summarize results into a table/chart — memory vs episode count, latency per query type. This becomes your Phase 4 deliverable for the paper. | Task 8 |

---

**Suggested order:** 1 → 2 → 8 (benchmark early, since it doesn't block on tiering) → 3 → 4 → 5 → 6 → 7 → 9

Running the benchmark (Task 8) early is a good idea even before tiering is built — it gives you a **baseline number** to compare against once pruning/compression exist later. Otherwise you won't know how much Phase 4's optimizations actually helped.

---

Ready to start Task 1 — `update_state()`? You already worked out the full logic in our last exchange, so this should be straightforward to write yourself now.
