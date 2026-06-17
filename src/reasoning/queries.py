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

def did_overlap(graph_store,cluster_id_1:str,attr_1:str,cluster_id_2:str,attr_2:str):
    pass

if __name__ == "__main__":
    DATA = os.path.join(os.getcwd(), "src", "data", "qt1_feasible_seed_1.json")
    with open(DATA) as f:
        episode_json = json.load(f)
    graph_store = GraphStore()
    graph_store.load_episode(episode_json)
    #graph_store.summary()

    intervals = get_intervals_for_room(graph_store, "utility_room")
    print(intervals[0])
    #print(f"Intervals for room 'bathroom': {intervals}")