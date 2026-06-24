import random
from datetime import datetime
import random
from datetime import datetime, timedelta

def generate_synthetic_stream(device_id, cluster_id, attr_name=None,
                                start_value=None, start_time: str=None,
                                duration_hours: float=None, num_changes: int=None,
                                seed: int = 42):
    random.seed(seed)
    stream = []
    
    base = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    current_value = start_value
    
    for i in range(num_changes):
        # spread timestamps irregularly across duration_hours
        # hint: pick a random offset between 0 and duration_hours, sort them after
        offset_minutes = random.uniform(0, duration_hours * 60)  # think: random.uniform(0, duration_hours * 60)
        timestamp = base + timedelta(minutes=offset_minutes)
        
        # drift gradually, not jump randomly
        # hint: small delta around current_value, not a fresh random pick
        delta = random.uniform(-0.5, 0.5)  # think: random.uniform(-0.5, 0.5)
        current_value = current_value + delta
        
        stream.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "value": round(current_value, 2)
        })
    
    # sort by timestamp since offsets were random
    stream.sort(key=lambda x: x["timestamp"])
    return stream

if __name__ == "__main__":
    stream = generate_synthetic_stream(
        device_id="bathroom_air_conditioner_1",
        cluster_id="bathroom_air_conditioner_1.Thermostat",
        attr_name="LocalTemperature",
        start_value=25.0,
        start_time="2025-08-23 08:00:00",
        duration_hours=4,
        num_changes=20,
        seed=42
    )

    print(f"Generated {len(stream)} synthetic updates\n")
    for entry in stream:
        print(entry)

    print("\n--- sanity checks ---")
    timestamps = [e["timestamp"] for e in stream]
    print("Sorted correctly:", timestamps == sorted(timestamps))

    values = [e["value"] for e in stream]
    max_jump = max(abs(values[i] - values[i-1]) for i in range(1, len(values)))
    print(f"Max value jump between consecutive entries: {max_jump:.2f}")
    print(f"Value range: {min(values):.2f} to {max(values):.2f}")