import random
from datetime import datetime, timedelta

def generate_synthetic_stream(device_id, cluster_id, attr_name,
                                start_value, start_time: str,
                                duration_hours: float, num_changes: int,
                                seed: int = 42,
                                inject_noise: bool = False,
                                noise_probability: float = 0.2,
                                noise_spike_minutes: float = 1.0):
    """
    inject_noise: if True, occasionally inserts a brief spike interval
    that jumps away from the trend and returns close to it shortly after —
    simulating sensor noise. Used to validate compress_intervals() actually
    triggers a merge under realistic-looking noisy conditions.
    """
    random.seed(seed)
    stream = []

    base = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    current_value = start_value

    offsets = sorted(random.uniform(0, duration_hours * 60) for _ in range(num_changes))

    for offset_minutes in offsets:
        timestamp = base + timedelta(minutes=offset_minutes)
        delta = random.uniform(-0.5, 0.5)
        current_value = current_value + delta

        stream.append({
            "device_id": device_id,
            "cluster_id": cluster_id,
            "attribute_name": attr_name,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "value": round(current_value, 2)
        })

        # occasionally inject a brief noise spike right after this point
        if inject_noise and random.random() < noise_probability:
            spike_value = current_value + random.choice([-1, 1]) * random.uniform(1.0, 2.0)
            spike_time = timestamp + timedelta(minutes=noise_spike_minutes)
            stream.append({
                "device_id": device_id,
                "cluster_id": cluster_id,
                "attribute_name": attr_name,
                "timestamp": spike_time.strftime("%Y-%m-%d %H:%M:%S"),
                "value": round(spike_value, 2)
            })
            # value returns close to trend right after the brief spike
            return_time = spike_time + timedelta(minutes=noise_spike_minutes)
            stream.append({
                "device_id": device_id,
                "cluster_id": cluster_id,
                "attribute_name": attr_name,
                "timestamp": return_time.strftime("%Y-%m-%d %H:%M:%S"),
                "value": round(current_value + random.uniform(-0.2, 0.2), 2)
            })

    stream.sort(key=lambda x: x["timestamp"])
    return stream