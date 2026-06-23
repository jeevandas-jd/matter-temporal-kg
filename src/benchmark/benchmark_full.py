import json
import os
import time
import glob
import tracemalloc
import statistics
from src.ingestion.graph_store import GraphStore
from src.reasoning.queries import state_at, get_active_intervals

DATA_DIR = os.path.join(os.getcwd(), "src", "data", "benchmark")


def benchmark_episode(filepath):
    """Loads one episode and measures memory + query latency."""
    try:
        with open(filepath) as f:
            episode_json = json.load(f)
    except Exception as e:
        return {"file": os.path.basename(filepath), "error": str(e)}

    # --- measure ingestion memory + time ---
    tracemalloc.start()
    t0 = time.perf_counter()

    try:
        graph_store = GraphStore()
        graph_store.load_episode(episode_json)
    except Exception as e:
        tracemalloc.stop()
        return {"file": os.path.basename(filepath), "error": f"ingestion failed: {e}"}

    ingest_time = time.perf_counter() - t0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # --- measure query latency ---
    try:
        first_room = list(episode_json["initial_home_config"]["rooms"].keys())[0]
        t1 = time.perf_counter()
        _ = get_active_intervals(graph_store, first_room)
        query_time = time.perf_counter() - t1
    except Exception as e:
        query_time = None

    return {
        "file": os.path.basename(filepath),
        "ingest_time_ms": round(ingest_time * 1000, 4),
        "peak_memory_kb": round(peak / 1024, 2),
        "query_time_ms": round(query_time * 1000, 4) if query_time is not None else None,
        "num_devices": episode_json.get("meta", {}).get("num_devices", "?"),
        "num_rooms": episode_json.get("meta", {}).get("num_rooms", "?"),
    }


def run_full_benchmark():
    episode_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.json")))
    print(f"Found {len(episode_files)} episode files in {DATA_DIR}\n")

    results = []
    errors = []
    for i, filepath in enumerate(episode_files, 1):
        result = benchmark_episode(filepath)
        if "error" in result:
            errors.append(result)
        else:
            results.append(result)
        if i % 100 == 0:
            print(f"  processed {i}/{len(episode_files)}...")

    print(f"\nSuccessful: {len(results)}  |  Failed: {len(errors)}")
    if errors:
        print("First few errors:")
        for e in errors[:5]:
            print(f"  {e['file']}: {e['error']}")

    if not results:
        print("No successful results to summarize.")
        return

    ingest_times = [r["ingest_time_ms"] for r in results]
    memories     = [r["peak_memory_kb"] for r in results]
    query_times  = [r["query_time_ms"] for r in results if r["query_time_ms"] is not None]

    print("\n" + "=" * 60)
    print(f"BENCHMARK SUMMARY  (n={len(results)} episodes)")
    print("=" * 60)
    print(f"Ingest time (ms)  — avg: {statistics.mean(ingest_times):.3f}  "
          f"median: {statistics.median(ingest_times):.3f}  "
          f"max: {max(ingest_times):.3f}")
    print(f"Peak memory (KB)  — avg: {statistics.mean(memories):.2f}  "
          f"median: {statistics.median(memories):.2f}  "
          f"max: {max(memories):.2f}")
    if query_times:
        print(f"Query time (ms)   — avg: {statistics.mean(query_times):.4f}  "
              f"median: {statistics.median(query_times):.4f}  "
              f"max: {max(query_times):.4f}")

    # save raw results to a file for the paper
    out_path = os.path.join(os.getcwd(), "results", "benchmark_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"results": results, "errors": errors}, f, indent=2)
    print(f"\nFull results saved to: {out_path}")


if __name__ == "__main__":
    run_full_benchmark()
