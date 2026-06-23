import json
import os
import time
import tracemalloc
from src.ingestion.graph_store import GraphStore
from src.reasoning.queries import state_at, get_active_intervals

DATA_DIR = os.path.join(os.getcwd(), "src", "data")

def benchmark_episode(filepath):
    """Loads one episode and measures memory + query latency."""
    
    with open(filepath) as f:
        episode_json = json.load(f)

    # --- measure ingestion memory + time ---
    tracemalloc.start()
    t0 = time.perf_counter()
    
    graph_store = GraphStore()
    graph_store.load_episode(episode_json)
    
    ingest_time = time.perf_counter() - t0
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # --- measure query latency (run a few representative queries) ---
    first_room = list(episode_json["initial_home_config"]["rooms"].keys())[0]
    
    t1 = time.perf_counter()
    _ = get_active_intervals(graph_store, first_room)
    query_time = time.perf_counter() - t1

    return {
        "file": os.path.basename(filepath),
        "ingest_time_ms": round(ingest_time * 1000, 3),
        "peak_memory_kb": round(peak / 1024, 2),
        "query_time_ms": round(query_time * 1000, 4),
        "num_devices": episode_json["meta"].get("num_devices", "?"),
        "num_rooms": episode_json["meta"].get("num_rooms", "?"),
    }


def run_benchmark_suite(episode_files):
    results = []
    for filepath in episode_files:
        result = benchmark_episode(filepath)
        results.append(result)
        print(result)
    return results


if __name__ == "__main__":
    # start small — just the episodes you already have
    episode_files = [
        os.path.join(DATA_DIR, "qt1_feasible_seed_1.json"),
        os.path.join(DATA_DIR, "test_episode.json"),
    ]
    
    results = run_benchmark_suite(episode_files)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    avg_ingest = sum(r["ingest_time_ms"] for r in results) / len(results)
    avg_memory = sum(r["peak_memory_kb"] for r in results) / len(results)
    avg_query  = sum(r["query_time_ms"] for r in results) / len(results)
    print(f"Avg ingest time:  {avg_ingest:.3f} ms")
    print(f"Avg peak memory:  {avg_memory:.2f} KB")
    print(f"Avg query time:   {avg_query:.4f} ms")
