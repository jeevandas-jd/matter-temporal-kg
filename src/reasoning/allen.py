from datetime import datetime
from typing import Optional, Dict, Any

def parse_time(t: Optional[str]) -> datetime:
    if t is None:
        return datetime.max
    return datetime.fromisoformat(t)

def normalize_interval(interval: Dict[str, Any]) -> tuple[datetime, datetime]:
    start = parse_time(interval.get("start"))
    end = parse_time(interval.get("end"))

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