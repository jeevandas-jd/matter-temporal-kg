from .allen import *
import json
import os
from src.ingestion.graph_store import GraphStore
def get_intervals_for_cluster(graph_store, cluster_id, attr_name=None):
    si_ids = graph_store.graph["intervals_by_cluster"].get(cluster_id, [])
    intervals = [graph_store.graph["state_intervals"][sid] for sid in si_ids]
    if attr_name:
        intervals = [i for i in intervals if i["attribute_name"] == attr_name]
    return intervals  
    
def get_intervals_for_room(graph_store, room_id, attr_name=None):
    """
    Traverses room → devices → clusters → state_intervals
    Returns all state intervals belonging to a room.
    """
    result = []
    
    # step 1 — get devices in room
    location = graph_store.get_node("location_nodes", room_id)
    #print(f"Location node for room '{room_id}': {location}")
    if not location:
        print(f"No location node found for room '{room_id}'")
        return []
    device_ids = location["devices"]
    #print(f"devices found {device_ids}")
    
    # step 2 — for each device get its clusters
    for device_id in device_ids:
        #print(f"looking for {device_id}")
        device = graph_store.get_node("device_nodes", device_id)
        #print(f"recived the device node of {device_id}*****************\n the node is :{device}")
        #print(f"device found :{type(device)}")
        if not device:
            continue
        for cluster_name in device["clusters"]:
            cluster_id = f"{device_id}.{cluster_name}"

            #print(f"we are looking for the {cluster_id}")
            
            # step 3 — get intervals for this cluster
            intervals = get_intervals_for_cluster(
                graph_store, cluster_id, attr_name
            )
            result.extend(intervals)
    
    return result
def get_active_intervals(graph_store,room_id):
    intervals=get_intervals_for_room(graph_store=graph_store,room_id=room_id)
    active_intervals=[]
    for si in intervals:
        if si["end_time"]==None:
            obj={}
            obj["state_interval_id"]=si["state_interval_id"]
            obj["start_time"]=si["start_time"]
            active_intervals.append(obj)
    return active_intervals
 # ← return full dicts, always a list, no stripping
def did_overlap(graph_store,cluster_id_1:str,attr_1:str,cluster_id_2:str,attr_2:str):
    c1_interval=get_intervals_for_cluster(graph_store=graph_store,cluster_id=cluster_id_1,attr_name=attr_1)
    c2_interval=get_intervals_for_cluster(graph_store=graph_store,cluster_id=cluster_id_2,attr_name=attr_2)
    if not c1_interval or not c2_interval:
     return False
    return overlaps(c1_interval[0], c2_interval[0])

    

def state_at(graph_store, cluster_id: str, attr_name: str, timestamp: str):
    """
    Returns the value of a cluster attribute at a specific point in time.
    Finds the interval where start_time <= timestamp <= end_time
    (treating end_time=None as "still active / now").
    """
    intervals = get_intervals_for_cluster(graph_store, cluster_id, attr_name)
    if not intervals:
        return None

    target = parse_time(timestamp)

    for interval in intervals:
        start = parse_time(interval["start_time"])
        end   = parse_time(interval["end_time"])  # None → datetime.max
        if start <= target <= end:
            return interval["value"]

    return None  # no interval covers this timestamp
if __name__ == "__main__":
    DATA = os.path.join(os.getcwd(), "src", "data", "qt1_feasible_seed_1.json")
    with open(DATA) as f:
        episode_json = json.load(f)

    graph_store = GraphStore()
    graph_store.load_episode(episode_json)

    print("=" * 60)
    print("TEST 1 — get_intervals_for_cluster")
    print("=" * 60)
    gic = get_intervals_for_cluster(
        graph_store,
        cluster_id="utility_room_air_purifier_1.FanControl",
        attr_name="FanModeSequence"
    )
    print(f"Intervals found: {len(gic)}")
    print(gic)

    print("\n" + "=" * 60)
    print("TEST 2 — get_intervals_for_room")
    print("=" * 60)
    room_intervals = get_intervals_for_room(graph_store, "utility_room")
    print(f"Total intervals in bathroom: {len(room_intervals)}")
    print("Sample:", room_intervals[0] if room_intervals else "none")

    print("\n" + "=" * 60)
    print("TEST 3 — get_active_intervals")
    print("=" * 60)
    active = get_active_intervals(graph_store, "utility_room")
    print(f"Active intervals in bathroom: {len(active)}")
    print("Sample:", active[0] if active else "none")

    print("\n" + "=" * 60)
    print("TEST 4 — state_at")
    print("=" * 60)
    val = state_at(
        graph_store,
        cluster_id="bathroom_air_conditioner_1.Thermostat",
        attr_name="LocalTemperature",
        timestamp="2025-08-23 10:01:47"
    )
    print(f"Bathroom AC LocalTemperature at base_time: {val}")

    print("\n" + "=" * 60)
    print("TEST 5 — did_overlap")
    print("=" * 60)
    overlap_result = did_overlap(
        graph_store,
        cluster_id_1="bathroom_air_conditioner_1.OnOff", attr_1="OnOff",
        cluster_id_2="bathroom_fan_1.OnOff", attr_2="OnOff"
    )
    print(f"AC OnOff overlaps Fan OnOff: {overlap_result}")