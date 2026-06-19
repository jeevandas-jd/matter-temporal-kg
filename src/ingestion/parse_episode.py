import json
import os

STATIC_CLUSTERS = {"BasicInformation", "Descriptor", "Identify"}
NORMALIZE_ATTRS = {"Temperature", "MeasuredValue", "Setpoint", "Humidity"}

class UserNode:
    def __init__(self, user_id=None, user_name=None, location=None):
        self.user_id = user_id
        self.user_name = user_name
        self.location = location
    def get_node(self):
        return {"user_id": self.user_id, "user_name": self.user_name, "location": self.location}

class LocationNode:
    def __init__(self, location_id=None, location_name=None, temperature=None,
                 humidity=None, illuminance=None, pm10=None, devices=None):
        self.location_id = location_id
        self.location_name = location_name
        self.temperature = temperature
        self.humidity = humidity
        self.illuminance = illuminance
        self.pm10 = pm10
        self.devices = devices or []
    def get_node(self):
        return {"location_id": self.location_id, "location_name": self.location_name,
                "temperature": self.temperature, "humidity": self.humidity,
                "illuminance": self.illuminance, "pm10": self.pm10, "devices": self.devices}

class DeviceNode:
    def __init__(self, device_id=None, device_name=None, room_id=None, vendor_name=None, clusters=None):
        self.device_id = device_id
        self.device_name = device_name
        self.room_id = room_id
        self.vendor_name = vendor_name
        self.clusters = clusters or []
    def get_node(self):
        return {"device_id": self.device_id, "device_name": self.device_name,
                "room_id": self.room_id, "vendor_name": self.vendor_name, "clusters": self.clusters}

class ClusterNode:
    def __init__(self, cluster_id=None, cluster_name=None, endpoint_id=None, device_id=None):
        self.cluster_id = cluster_id
        self.cluster_name = cluster_name
        self.endpoint_id = endpoint_id
        self.device_id = device_id
    def get_node(self):
        return {"cluster_id": self.cluster_id, "cluster_name": self.cluster_name,
                "endpoint_id": self.endpoint_id, "device_id": self.device_id}

class StateIntervalNode:
    def __init__(self, state_interval_id=None, cluster_id=None, attribute_name=None,
                 value=None, start_time=None, end_time=None):
        self.state_interval_id = state_interval_id
        self.cluster_id = cluster_id
        self.attribute_name = attribute_name
        self.value = value
        self.start_time = start_time
        self.end_time = end_time
    def get_node(self):
        return {"state_interval_id": self.state_interval_id, "cluster_id": self.cluster_id,
                "attribute_name": self.attribute_name, "value": self.value,
                "start_time": self.start_time, "end_time": self.end_time}

class EventNode:
    def __init__(self, event_id=None, event_type=None, timestamp=None, description=None, source_id=None):
        self.event_id = event_id
        self.event_type = event_type
        self.timestamp = timestamp
        self.description = description
        self.source_id = source_id
    def get_node(self):
        return {"event_id": self.event_id, "event_type": self.event_type,
                "timestamp": self.timestamp, "description": self.description,
                "source_id": self.source_id}


def parse_device(device: dict, room_id: str, base_time: str) -> dict:
    """
    Takes one device dict from SimuHome JSON,
    the room it belongs to, and the episode base_time.
    Returns a dict with keys: device_node, cluster_nodes, state_intervals, edges
    NOTE: BasicInformation cluster is retained in cluster_nodes and edges
    intentionally — vendor name and product identity may be useful
    for device-level filtering in future query functions.
    StateIntervals for BasicInformation are skipped (static metadata).
    """
    attributes = device["attributes"]
    device_id  = device["device_id"]

    # --- device node ---
    device_node = DeviceNode(
        device_id   = device_id,
        device_name = attributes.get("0.BasicInformation.ProductName", "Unknown"),
        room_id     = room_id,
        vendor_name = attributes.get("0.BasicInformation.VendorName", "Unknown"),
        clusters    = list(set(k.split(".")[1] for k in attributes.keys()))
    )

    # --- cluster nodes ---
    cluster_nodes = []
    seen_clusters = set()
    for key in attributes.keys():
        parts        = key.split(".")
        endpoint_id  = int(parts[0])
        cluster_name = parts[1]
        cluster_id   = f"{device_id}.{cluster_name}"
        if cluster_id not in seen_clusters:
            seen_clusters.add(cluster_id)
            cluster_nodes.append(ClusterNode(
                cluster_id   = cluster_id,
                cluster_name = cluster_name,
                endpoint_id  = endpoint_id,
                device_id    = device_id
            ).get_node())

    # --- state intervals ---
    state_intervals = []
    for key, value in attributes.items():
        parts        = key.split(".")
        cluster_name = parts[1]
        attr_name    = parts[2]

        # skip static metadata clusters for state intervals
        if cluster_name in STATIC_CLUSTERS:
            continue

        # normalize scaled values
        if any(n in attr_name for n in NORMALIZE_ATTRS) and value is not None:
            value = round(value / 100, 2)

        cluster_id = f"{device_id}.{cluster_name}"
        si_id = f"si_{device_id}_{parts[0]}_{cluster_name}_{attr_name}"
        state_intervals.append(StateIntervalNode(
            state_interval_id = si_id,
            cluster_id        = cluster_id,
            attribute_name    = attr_name,
            value             = value,
            start_time        = base_time,
            end_time          = None
        ).get_node())

    # --- edges ---
    edges = []
    # device → room
    edges.append({"source": device_id, "target": room_id, "edge_type": "INSTALLED_IN"})
    # device → clusters
    for cn in cluster_nodes:
        edges.append({"source": device_id, "target": cn["cluster_id"], "edge_type": "HAS_CLUSTER"})
    # cluster → state intervals
    for si in state_intervals:
        edges.append({"source": si["cluster_id"], "target": si["state_interval_id"], "edge_type": "HAS_STATE"})

    return {
        "device_node":     device_node.get_node(),
        "cluster_nodes":   cluster_nodes,
        "state_intervals": state_intervals,
        "edges":           edges
    }


def parse_episode(episode_json: dict) -> dict:
    """
    Takes a full SimuHome episode dict.
    Returns the complete graph with all nodes and edges
    for all rooms and devices.
    """
    base_time     = episode_json["initial_home_config"]["base_time"]
    rooms         = episode_json["initial_home_config"]["rooms"]
    user_location = episode_json["user_location"]

    # --- user node + LOCATED_IN edge ---
    user = UserNode(user_id="user_1", user_name="user_1", location=user_location)
    all_edges = [{"source": "user_1", "target": user_location,
                  "edge_type": "LOCATED_IN", "start": base_time, "end": None}]

    location_nodes = []
    all_device_nodes    = []
    all_cluster_nodes   = []
    all_state_intervals = []

    for room_id, room_data in rooms.items():
        state          = room_data["state"]
        devices_in_room = room_data["devices"]

        # build location node
        location = LocationNode(
            location_id   = room_id,
            location_name = room_id,
            temperature   = round(state["temperature"] / 100, 2),
            humidity      = round(state["humidity"] / 100, 2),
            illuminance   = round(state["illuminance"], 2),
            pm10          = round(state["pm10"], 2),
            devices       = [d["device_id"] for d in devices_in_room]
        )
        location_nodes.append(location.get_node())

        # parse every device in this room
        for device in devices_in_room:
            result = parse_device(device=device, room_id=room_id, base_time=base_time)
            all_device_nodes.append(result["device_node"])
            all_cluster_nodes.extend(result["cluster_nodes"])
            all_state_intervals.extend(result["state_intervals"])
            all_edges.extend(result["edges"])

    return {
        "user_node":       user.get_node(),
        "location_nodes":  location_nodes,
        "device_nodes":    all_device_nodes,
        "cluster_nodes":   all_cluster_nodes,
        "state_intervals": all_state_intervals,
        "all_edges":       all_edges
    }

"""
if __name__ == "__main__":
    DATA = os.path.join(os.getcwd(), "src", "data", "qt1_feasible_seed_1.json")
    with open(DATA) as f:
        episode_json = json.load(f)
    result = parse_episode(episode_json)

    with open("parsed_episode.json", "w") as f:
        json.dump(result, f, indent=2)

    # print summary instead of full dump — full output is very large
    print(f"user_node:       {result['user_node']}")
    print(f"location_nodes:  {len(result['location_nodes'])} rooms")
    print(f"device_nodes:    {len(result['device_nodes'])} devices")
    print(f"cluster_nodes:   {len(result['cluster_nodes'])} clusters")
    print(f"state_intervals: {len(result['state_intervals'])} intervals")
    print(f"all_edges:       {len(result['all_edges'])} edges")
    print("\nSample location node:")
    print(json.dumps(result["location_nodes"][0], indent=2))"""