from .allen import *
import json
import os
from src.ingestion.graph_store import GraphStore


def get_intervals_for_cluster(graph_store, cluster_id, attr_name=None):
    si_ids = graph_store.graph["intervals_by_cluster"].get(cluster_id, [])
    intervals = [graph_store.graph["state_intervals"][sid] for sid in si_ids]
    if attr_name:
        intervals = [i for i in intervals if i["attribute_name"] == attr_name]
    return intervals  # always a list, full fields kept (no stripping)


def get_intervals_for_room(graph_store, room_id, attr_name=None):
    """
    Traverses room → devices → clusters → state_intervals
    Returns all state intervals belonging to a room.
    """
    result = []
    location = graph_store.get_node("location_nodes", room_id)
    if not location:
        print(f"No location node found for room '{room_id}'")
        return []
    device_ids = location["devices"]

    for device_id in device_ids:
        device = graph_store.get_node("device_nodes", device_id)
        if not device:
            continue
        for cluster_name in device["clusters"]:
            cluster_id = f"{device_id}.{cluster_name}"
            intervals = get_intervals_for_cluster(graph_store, cluster_id, attr_name)
            result.extend(intervals)

    return result


# ──────────────────────────────────────────────────────────
# PROVENANCE HELPER — Phase 3 Task 3
# ──────────────────────────────────────────────────────────

def make_evidence(interval: dict) -> dict:
    """
    Builds a standard evidence record from a state interval.
    Every query function attaches this to its result so the
    answer is always traceable back to its source data.
    """
    return {
        "interval_id":  interval.get("state_interval_id"),
        "cluster_id":   interval.get("cluster_id"),
        "attribute":    interval.get("attribute_name"),
        "value":        interval.get("value"),
        "start_time":   interval.get("start_time"),
        "end_time":     interval.get("end_time"),
    }


def explain(evidence: dict) -> str:
    """
    Converts a structured evidence record into a human-readable
    sentence. This is what makes the system's answers explainable
    rather than just raw data dumps.
    """
    if evidence is None:
        return "No evidence available — no matching interval was found."

    attr   = evidence.get("attribute", "value")
    value  = evidence.get("value")
    start  = evidence.get("start_time")
    end    = evidence.get("end_time")
    iv_id  = evidence.get("interval_id")

    if end is None:
        return (f"{attr} = {value}, held since {start} "
                f"and still active (interval {iv_id}).")
    else:
        return (f"{attr} = {value}, held from {start} to {end} "
                f"(interval {iv_id}).")


# ──────────────────────────────────────────────────────────
# QUERY FUNCTIONS — now returning evidence alongside answers
# ──────────────────────────────────────────────────────────

def get_active_intervals(graph_store, room_id):
    """
    Returns all currently active (end_time is None) state intervals
    for a room, each with attached evidence.
    """
    intervals = get_intervals_for_room(graph_store=graph_store, room_id=room_id)
    active_intervals = []
    for si in intervals:
        if si["end_time"] is None:
            active_intervals.append({
                "value":    si["value"],
                "evidence": make_evidence(si)
            })
    return active_intervals


def did_overlap(graph_store, cluster_id_1: str, attr_1: str,
                 cluster_id_2: str, attr_2: str):
    """
    Checks whether the active intervals of two cluster attributes
    overlap in time (Allen 'overlaps' relation).
    Returns the result plus evidence from both sides.
    """
    c1_list = get_intervals_for_cluster(graph_store, cluster_id_1, attr_1)
    c2_list = get_intervals_for_cluster(graph_store, cluster_id_2, attr_2)

    if not c1_list or not c2_list:
        return {
            "result": False,
            "evidence": None,
            "explanation": "Could not find intervals for one or both attributes."
        }

    i1, i2 = c1_list[0], c2_list[0]
    result = overlaps(i1, i2)

    return {
        "result": result,
        "evidence": [make_evidence(i1), make_evidence(i2)],
        "explanation": (
            f"{explain(make_evidence(i1))} {explain(make_evidence(i2))} "
            f"→ overlap = {result}"
        )
    }


def state_at(graph_store, cluster_id: str, attr_name: str, timestamp: str):
    """
    Returns the value of a cluster attribute at a specific point in time,
    along with evidence for why that value was chosen.
    """
    intervals = get_intervals_for_cluster(graph_store, cluster_id, attr_name)
    if not intervals:
        return {"value": None, "evidence": None,
                 "explanation": "No intervals found for this attribute."}

    target = parse_time(timestamp)

    for interval in intervals:
        start = parse_time(interval["start_time"])
        end   = parse_time(interval["end_time"])
        if start <= target <= end:
            evidence = make_evidence(interval)
            return {
                "value": interval["value"],
                "evidence": evidence,
                "explanation": explain(evidence)
            }

    return {"value": None, "evidence": None,
             "explanation": "No interval covers this timestamp."}

if __name__ == "__main__":
    DATA = os.path.join(os.getcwd(), "src", "data", "test_episode.json")
    with open(DATA) as f:
        episode_json = json.load(f)

    graph_store = GraphStore()
    graph_store.load_episode(episode_json)

    print("=" * 60)
    print("GRAPH SUMMARY")
    print("=" * 60)
    graph_store.summary()

    print("\n" + "=" * 60)
    print("TEST 1 — state_at: bathroom AC LocalTemperature at base_time")
    print("=" * 60)
    result = state_at(
        graph_store,
        cluster_id="bathroom_air_conditioner_1.Thermostat",
        attr_name="LocalTemperature",
        timestamp="2025-08-23 10:00:00"
    )
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 60)
    print("TEST 2 — get_active_intervals: bathroom")
    print("=" * 60)
    active = get_active_intervals(graph_store, "bathroom")
    print(f"Active intervals found: {len(active)}")
    for a in active:
        print(json.dumps(a, indent=2))

    print("\n" + "=" * 60)
    print("TEST 3 — did_overlap: AC OnOff vs Fan OnOff")
    print("=" * 60)
    overlap_result = did_overlap(
        graph_store,
        cluster_id_1="bathroom_air_conditioner_1.OnOff", attr_1="OnOff",
        cluster_id_2="bathroom_fan_1.OnOff", attr_2="OnOff"
    )
    print(json.dumps(overlap_result, indent=2))

    print(f"{"="*20} debugging {"="*20}")
    print(graph_store.graph["intervals_by_cluster"].keys())

    for sid, si in graph_store.graph["state_intervals"].items():
        print(sid, "→", si["cluster_id"])