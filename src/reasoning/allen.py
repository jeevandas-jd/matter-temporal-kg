from datetime import datetime
from typing import Optional, Dict, Any

def parse_time(t: Optional[str]) -> datetime:
    if t is None:
        return datetime.max
    return datetime.fromisoformat(t)

def normalize_interval(interval: Dict[str, Any]) -> tuple[datetime, datetime]:
    start = parse_time(interval.get("start_time"))
    end = parse_time(interval.get("end_time"))
    


    if start > end:
        raise ValueError(f"Invalid interval: start {start} is after end {end}")

    return start, end

def before(x: dict, y: dict) -> bool:
    xs, xe = normalize_interval(x)
    ys, ye = normalize_interval(y)
    return xe < ys

def equals(x: dict, y: dict) -> bool:
    xs, xe = normalize_interval(x)
    ys, ye = normalize_interval(y)
    return xs == ys and xe == ye

def meets(x: dict, y: dict) -> bool:
    xs, xe = normalize_interval(x)
    ys, ye = normalize_interval(y)
    return xe == ys

def overlaps(x: dict, y: dict) -> bool:
    xs, xe = normalize_interval(x)
    ys, ye = normalize_interval(y)
    return xs < ys < xe < ye

def starts(x: dict, y: dict) -> bool:
    xs, xe = normalize_interval(x)
    ys, ye = normalize_interval(y)
    return xs == ys and xe < ye

def finishes(x: dict, y: dict) -> bool:
    xs, xe = normalize_interval(x)
    ys, ye = normalize_interval(y)
    return xs > ys and xe == ye

def during(x: dict, y: dict) -> bool:
    xs, xe = normalize_interval(x)
    ys, ye = normalize_interval(y)
    return ys < xs < xe < ye

if __name__ == "__main__":
    A = {"start_time": "2025-08-23 08:00:00", "end_time": None}
    B = {"start_time": "2025-08-23 09:00:00", "end_time": "2025-08-23 11:00:00"}
    C = {"start_time": "2025-08-23 09:00:00", "end_time": "2025-08-23 09:30:00"}

    print(f"A before B:   {before(A, B)}")    # False
    print(f"A overlaps B: {overlaps(A, B)}")  # True
    print(f"C during A:   {during(C, A)}")    # True
    print(f"A meets ?:    {meets(A, B)}")     # False
    print(f"A equals A:   {equals(A, A)}")    # True