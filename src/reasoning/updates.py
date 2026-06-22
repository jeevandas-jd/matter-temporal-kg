from src.ingestion.graph_store import GraphStore
from src.reasoning.queries import get_intervals_for_cluster
import os
import json


def update_state(graph_store: GraphStore, cluster_id: str, attr_name: str,
                  new_value, timestamp: str) -> dict:
    """
    Updates the state of a cluster attribute following coalescing rules:
    - If no active interval exists, creates a new one.
    - If an active interval exists with the SAME value, does nothing.
    - If an active interval exists with a DIFFERENT value, closes the old
      interval (sets end_time) and opens a new one.

    Returns a dict: {"action": "created" | "unchanged" | "updated", "interval": {...}}
    """
    intervals = get_intervals_for_cluster(graph_store, cluster_id, attr_name)
    active = next((i for i in intervals if i["end_time"] is None), None)

    # CASE 1 — no active interval exists yet → create the first one
    if active is None:
        new_id = f"si_{cluster_id}_{attr_name}_{timestamp}".replace(" ", "_").replace(":", "-")
        new_interval = {
            "state_interval_id": new_id,
            "cluster_id": cluster_id,
            "attribute_name": attr_name,
            "value": new_value,
            "start_time": timestamp,
            "end_time": None
        }
        graph_store.graph["state_intervals"][new_id] = new_interval
        graph_store.graph["intervals_by_cluster"].setdefault(cluster_id, []).append(new_id)
        return {"action": "created", "interval": new_interval}

    # CASE 2 — active interval exists, value unchanged → no-op (coalescing)
    if active["value"] == new_value:
        return {"action": "unchanged", "interval": active}

    # CASE 3 — active interval exists, value changed → close old, open new
    active["end_time"] = timestamp  # mutate in place, same dict object in graph_store

    new_id = f"si_{cluster_id}_{attr_name}_{timestamp}".replace(" ", "_").replace(":", "-")
    new_interval = {
        "state_interval_id": new_id,
        "cluster_id": cluster_id,
        "attribute_name": attr_name,
        "value": new_value,
        "start_time": timestamp,
        "end_time": None
    }
    graph_store.graph["state_intervals"][new_id] = new_interval
    graph_store.graph["intervals_by_cluster"].setdefault(cluster_id, []).append(new_id)

    return {"action": "updated", "interval": new_interval, "closed_interval": active}


if __name__ == "__main__":
    DATA = os.path.join(os.getcwd(), "src", "data", "test_episode.json")
    with open(DATA) as f:
        episode_json = json.load(f)

    graph_store = GraphStore()
    graph_store.load_episode(episode_json)

    cluster_id = "bathroom_air_conditioner_1.Thermostat"
    attr_name  = "LocalTemperature"

    print("=" * 60)
    print("BEFORE update — current intervals for this attribute")
    print("=" * 60)
    print(get_intervals_for_cluster(graph_store, cluster_id, attr_name))

    print("\n" + "=" * 60)
    print("TEST 1 — same value (should be 'unchanged')")
    print("=" * 60)
    result1 = update_state(graph_store, cluster_id, attr_name,
                            new_value=22.65, timestamp="2025-08-23 10:05:00")
    print(result1)

    print("\n" + "=" * 60)
    print("TEST 2 — different value (should be 'updated')")
    print("=" * 60)
    result2 = update_state(graph_store, cluster_id, attr_name,
                            new_value=21.00, timestamp="2025-08-23 10:07:00")
    print(result2)

    print("\n" + "=" * 60)
    print("AFTER updates — all intervals for this attribute")
    print("=" * 60)
    final_intervals = get_intervals_for_cluster(graph_store, cluster_id, attr_name)
    for iv in final_intervals:
        print(iv)