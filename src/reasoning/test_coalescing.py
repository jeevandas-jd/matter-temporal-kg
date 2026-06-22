from src.reasoning.updates import update_state
from src.ingestion.graph_store import GraphStore
from src.reasoning.queries import get_intervals_for_cluster
import json, os

def run_coalescing_test():
    # load any episode to get a populated graph_store
    DATA = os.path.join(os.getcwd(), "src", "data", "test_episode.json")
    with open(DATA) as f:
        episode_json = json.load(f)
    graph_store = GraphStore()
    graph_store.load_episode(episode_json)

    cluster_id = "bathroom_air_conditioner_1.Thermostat"
    attr_name  = "LocalTemperature"

    # 20 synthetic updates, value only changes 3 times total
    sequence = [
        22.65, 22.65, 22.65, 22.65, 22.65,   # 5x same
        22.80, 22.80, 22.80,                  # value changes once
        22.80, 22.80, 22.80, 22.80,           # 4x same
        23.00, 23.00,                          # value changes once
        23.00, 23.00, 23.00, 23.00, 23.00, 23.00  # 6x same
    ]

    base_minutes = 0
    actions = []
    for val in sequence:
        timestamp = f"2025-08-23 10:{base_minutes:02d}:00"
        result = update_state(graph_store, cluster_id, attr_name, val, timestamp)
        actions.append(result["action"])
        base_minutes += 1

    # count actions
    created = actions.count("created")
    updated = actions.count("updated")
    unchanged = actions.count("unchanged")

    print(f"Total updates sent: {len(sequence)}")
    print(f"created: {created}, updated: {updated}, unchanged: {unchanged}")

    final_intervals = get_intervals_for_cluster(graph_store, cluster_id, attr_name)
    print(f"\nTotal intervals stored: {len(final_intervals)}")
    for iv in final_intervals:
        print(f"  value={iv['value']:<6} start={iv['start_time']} end={iv['end_time']}")

if __name__ == "__main__":
    run_coalescing_test()
