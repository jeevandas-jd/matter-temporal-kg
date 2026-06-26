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
        
def compress_intervals(intervals, max_gap_minutes=2.0, max_value_diff=0.3):
    if not intervals:
        return []

    intervals = [dict(iv) for iv in intervals]
    merged = [intervals[0]]

    for idx, current in enumerate(intervals[1:], start=1):
        previous = merged[-1]
        prev_value = previous["value"]
        curr_value = current["value"]

        both_numeric = isinstance(prev_value, (int, float)) and isinstance(curr_value, (int, float))

        print(f"\n[iter {idx}] comparing prev_value={prev_value} curr_value={curr_value} both_numeric={both_numeric}")

        if not both_numeric:
            merged.append(current)
            continue

        start = parse_time(current["start_time"])
        end   = parse_time(current["end_time"])
        duration_minutes = (end - start).total_seconds() / 60
        value_diff = abs(curr_value - prev_value)

        is_brief        = duration_minutes < max_gap_minutes
        is_close_enough = value_diff < max_value_diff

        print(f"[iter {idx}] diff={value_diff:.3f} (thresh {max_value_diff}) "
              f"duration={duration_minutes:.3f} (thresh {max_gap_minutes}) "
              f"is_brief={is_brief} is_close_enough={is_close_enough}")

        if is_brief and is_close_enough:
            previous["end_time"] = current["end_time"]
            previous["merged_count"] = previous.get("merged_count", 0) + 1
            print(f"[iter {idx}] >>> MERGED")
        else:
            merged.append(current)
            print(f"[iter {idx}] kept separate")

    return merged

def compress_tier(graph_store, tier_intervals: list,
                   max_gap_minutes: float = 2.0, max_value_diff: float = 0.3) -> list:
    
    groups = {}
    for iv in tier_intervals:
        key = (iv["cluster_id"], iv["attribute_name"])
        groups.setdefault(key, []).append(iv)

    print("DEBUG — groups found:")
    for key, group in groups.items():
        print(f"  {key}: {len(group)} intervals")
    """
    Applies compress_intervals() correctly across a tier's worth of
    mixed intervals (which may span many different attributes/clusters).

    Groups intervals by (cluster_id, attribute_name) first, since
    compression must only ever compare an attribute against ITSELF
    over time — never against a different attribute.

    Returns the flattened, compressed list across all attributes.
    """
    groups = {}
    for iv in tier_intervals:
        key = (iv["cluster_id"], iv["attribute_name"])
        groups.setdefault(key, []).append(iv)

    compressed_all = []
    for key, group in groups.items():
        group_sorted = sorted(group, key=lambda x: x["start_time"])
        compressed_all.extend(
            compress_intervals(group_sorted, max_gap_minutes, max_value_diff)
        )

    return compressed_all
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
        seed=42,
        inject_noise=True
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

    
    print("\n" + "=" * 60)
    print("TASK 6 — compression test on SEMANTIC tier")
    print("=" * 60)
    semantic_before = tiers["semantic"]
    print(f"Before compression: {len(semantic_before)} intervals")

    semantic_compressed = compress_tier(graph_store, semantic_before,
                                        max_gap_minutes=2.0, max_value_diff=0.8)
    print(f"After compression:  {len(semantic_compressed)} intervals")

    for iv in semantic_compressed:
        merged = iv.get("merged_count", 0)
        print(f"  value={iv['value']:<6} start={iv['start_time']} end={iv['end_time']} "
            f"merged={merged}")