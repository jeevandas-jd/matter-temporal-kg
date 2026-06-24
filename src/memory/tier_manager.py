from src.reasoning.allen import parse_time

class TierManager:
    def __init__(self, graph_store, hot_window_minutes=20, episodic_window_hours=1):
        self.graph_store = graph_store
        self.hot_window_minutes = hot_window_minutes
        self.episodic_window_hours = episodic_window_hours
    
    def classify_tier(self,interval: dict, current_time: str):


        if interval["end_time"]==None:
            return "HOT"
        
        start_time,end_time=parse_time(interval["start_time"]),parse_time(interval["end_time"])
        current_time=parse_time(current_time)


        
        diffrence=(current_time-end_time).total_seconds()
        if diffrence/60 <self.hot_window_minutes:
            return "HOT"
        if diffrence/3600 <=self.episodic_window_hours:
            return "EPISODIC"
        if diffrence/3600>self.episodic_window_hours:
            return "SEMANTIC"
    def get_tiered_intervals(self, current_time: str) -> dict:
        """
        Classifies every state interval in the graph_store into
        hot / episodic / semantic buckets.
        Returns: {"hot": [...], "episodic": [...], "semantic": [...]}
        """
        tiers = {"hot": [], "episodic": [], "semantic": []}
        
        for interval_id, interval in self.graph_store.graph["state_intervals"].items():
            tier = self.classify_tier(interval, current_time)
            tiers[tier.lower()].append(interval)
        
        return tiers
        

"""THE MAIN IS GENERATED"""

if __name__ == "__main__":
    import json
    import os
    from src.ingestion.graph_store import GraphStore
    from src.reasoning.updates import update_state
    from src.benchmark.synthetic_stream import generate_synthetic_stream

    # 1. load a base episode to get a populated graph
    DATA = os.path.join(os.getcwd(), "src", "data", "test_episode.json")
    with open(DATA) as f:
        episode_json = json.load(f)

    graph_store = GraphStore()
    graph_store.load_episode(episode_json)

    # 2. generate a synthetic 4-hour stream of temperature changes
    stream = generate_synthetic_stream(
        device_id="bathroom_air_conditioner_1",
        cluster_id="bathroom_air_conditioner_1.Thermostat",
        attr_name="LocalTemperature",
        start_value=25.0,
        start_time="2025-08-23 10:00:00",
        duration_hours=4,
        num_changes=20,
        seed=42
    )

    # 3. feed every update through update_state() to build a realistic interval history
    cluster_id = "bathroom_air_conditioner_1.Thermostat"
    attr_name  = "LocalTemperature"

    for entry in stream:
        update_state(
            graph_store,
            cluster_id=cluster_id,
            attr_name=attr_name,
            new_value=entry["value"],
            timestamp=entry["timestamp"]
        )

    # 4. classify all intervals — use the LAST stream timestamp as "now"
    current_time = stream[-1]["timestamp"]
    tm = TierManager(graph_store=graph_store, hot_window_minutes=20, episodic_window_hours=1)
    tiers = tm.get_tiered_intervals(current_time)

    print(f"Current simulated time: {current_time}\n")
    print(f"HOT intervals:      {len(tiers['hot'])}")
    print(f"EPISODIC intervals: {len(tiers['episodic'])}")
    print(f"SEMANTIC intervals: {len(tiers['semantic'])}")

    print("\n--- HOT tier contents ---")
    for iv in tiers["hot"]:
        print(f"  value={iv['value']:<6} start={iv['start_time']} end={iv['end_time']}")

    print("\n--- EPISODIC tier contents (first 5) ---")
    for iv in tiers["episodic"][:5]:
        print(f"  value={iv['value']:<6} start={iv['start_time']} end={iv['end_time']}")

    print("\n--- SEMANTIC tier contents (first 5) ---")
    for iv in tiers["semantic"][:5]:
        print(f"  value={iv['value']:<6} start={iv['start_time']} end={iv['end_time']}")