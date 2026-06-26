import sqlite3
import json
import os
DB_PATH = "src/data/tkg_storage.db"

def init_db(db_path=DB_PATH):
    """Creates the database file and table if they don't exist."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS state_intervals (
            interval_id     TEXT PRIMARY KEY,
            cluster_id      TEXT NOT NULL,
            attribute_name  TEXT NOT NULL,
            value           TEXT,
            start_time      TEXT NOT NULL,
            end_time        TEXT,
            tier            TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_intervals(intervals: list, tier: str, db_path=DB_PATH):
    """
    Writes a list of interval dicts to SQLite, tagged with their tier.
    Uses INSERT OR REPLACE so re-saving an updated interval overwrites
    the old row instead of erroring on duplicate primary key.
    """
    conn = sqlite3.connect(db_path)
    for iv in intervals:
        conn.execute("""
            INSERT OR REPLACE INTO state_intervals
            (interval_id, cluster_id, attribute_name, value, start_time, end_time, tier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            iv["state_interval_id"],
            iv["cluster_id"],
            iv["attribute_name"],
            json.dumps(iv["value"]),   # json.dumps handles bool/number/string/null uniformly
            iv["start_time"],
            iv["end_time"],
            tier
        ))
    conn.commit()
    conn.close()


def load_intervals(tier: str = None, db_path=DB_PATH) -> list:
    """
    Reads intervals back from SQLite. If tier is given, filters to
    that tier only; otherwise returns everything.
    """
    conn = sqlite3.connect(db_path)
    if tier:
        rows = conn.execute(
            "SELECT * FROM state_intervals WHERE tier = ?", (tier,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM state_intervals").fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "state_interval_id": row[0],
            "cluster_id": row[1],
            "attribute_name": row[2],
            "value": json.loads(row[3]),
            "start_time": row[4],
            "end_time": row[5],
            "tier": row[6],
        })
    return results

if __name__ == "__main__":
    init_db()
    
    # use your compressed semantic intervals from Task 6 as test data
    test_intervals = [
        {"state_interval_id": "si_test_1", "cluster_id": "bathroom_air_conditioner_1.Thermostat",
         "attribute_name": "LocalTemperature", "value": 22.65,
         "start_time": "2025-08-23 10:00:00", "end_time": "2025-08-23 10:06:22"},
    ]
    
    save_intervals(test_intervals, tier="semantic")
    loaded = load_intervals(tier="semantic")
    
    print(f"Saved {len(test_intervals)} intervals")
    print(f"Loaded back {len(loaded)} intervals")
    for iv in loaded:
        print(iv)