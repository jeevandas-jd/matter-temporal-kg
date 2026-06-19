import os
import json
from .parser import parse_episode
class GraphStore:

    def __init__(self):

        self.graph={}
    def load_episode(self, episode_json: dict):
        episode_data = parse_episode(episode_json)
        
        # convert lists → dicts for O(1) lookup
        self.graph["user_node"]       = episode_data["user_node"]
        self.graph["location_nodes"]  = {n["location_id"]: n 
                                        for n in episode_data["location_nodes"]}
        self.graph["device_nodes"]    = {n["device_id"]: n 
                                        for n in episode_data["device_nodes"]}
        self.graph["cluster_nodes"]   = {n["cluster_id"]: n 
                                        for n in episode_data["cluster_nodes"]}
        self.graph["state_intervals"] = {n["state_interval_id"]: n 
                                        for n in episode_data["state_intervals"]}
        self.graph["all_edges"]       = episode_data["all_edges"]
        self.graph["intervals_by_cluster"] = {}

        for si_id, si in self.graph["state_intervals"].items():
            cluster_id = si["cluster_id"]
            if cluster_id not in self.graph["intervals_by_cluster"]:
                self.graph["intervals_by_cluster"][cluster_id] = []
            self.graph["intervals_by_cluster"][cluster_id].append(si_id)
    def get_node(self, node_type, node_id):
        if node_type == "user_nodes":
            return self.graph["user_node"]
        return self.graph.get(node_type, {}).get(node_id)
    def get_edges(self,source_id):
        edges = []
        for edge in self.graph["edges"]:
            if edge["source"] == source_id:
                edges.append(edge)
        return edges
    def summary(self):
        """prints count of each node type and total edges"""
        print(f"User nodes: {len(self.graph.get('user_node', []))}")
        print(f"Location nodes: {len(self.graph.get('location_nodes', []))}")
        print(f"Device nodes: {len(self.graph.get('device_nodes', []))}")
        print(f"Cluster nodes: {len(self.graph.get('cluster_nodes', []))}")
        print(f"State Interval nodes: {len(self.graph.get('state_intervals', []))}")
        print(f"Event nodes: {len(self.graph.get('event_nodes', []))}")
        print(f"Total edges: {len(self.graph["all_edges"])}")
    def save_graph(self,path):
        try:
            with open(path,"w") as f:

                json.dump(self.graph,f,indent=2)
            print("graph saved successfully !")
        except Exception as e:

            print(f"error occourd : {e}")

if __name__ == "__main__":
    DATA = os.path.join(os.getcwd(), "src", "data", "qt1_feasible_seed_1.json")
    with open(DATA) as f:
        episode_json = json.load(f)
    graph_store = GraphStore()
    graph_store.load_episode(episode_json)
    #print(f"graph loaded preview: {graph_store.graph}")
    #print(f"Graph loaded with {len(graph_store.graph)} node types and {len(graph_store.get_edges("bathroom"))} edges.")
    #print(F"graph keys: {graph_store.graph.keys()}")
    #print(f"user node {graph_store.get_node('user_nodes', 'user_1')}")
    print(f"device node {graph_store.get_node('device_nodes', 'bathroom_air_conditioner_1')}")
    

    graph_store.save_graph()
    #print("\nRetrieving node 'user_1':")
    #user_node = graph_store.get_node("user_nodes", "user_1")
    #
    # print(user_node)
    #graph_store.summary()

