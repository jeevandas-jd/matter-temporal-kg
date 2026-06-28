"""
Edge TKG Backend — Integration Adapter
========================================
This is the single entry point that lets the existing tkg_agent.py
(originally built against Neo4jClient / EpisodeIngestor / TKGRetriever)
use the edge-optimized TKG instead, with zero changes to the agent code
itself.

Two classes are provided, matching the method signatures the agent
already expects:

    EdgeEpisodeIngestor  — replaces EpisodeIngestor
    EdgeTKGRetriever      — replaces TKGRetriever

Both are thin wrappers. All real logic (parsing, coalescing, querying,
tiering) lives in the existing, already-tested modules:
    src.ingestion.graph_store.GraphStore
    src.ingestion.parser.parse_episode / parse_device
    src.reasoning.queries.get_active_intervals / state_at / get_intervals_for_cluster
    src.reasoning.updates.update_state
"""

from src.ingestion.graph_store import GraphStore
from src.reasoning.queries import (
    get_active_intervals,
    get_intervals_for_cluster,
)
from src.reasoning.updates import update_state


# ─────────────────────────────────────────────────────────────────────
# EdgeEpisodeIngestor — replaces EpisodeIngestor
# ─────────────────────────────────────────────────────────────────────

class EdgeEpisodeIngestor:
    """
    Drop-in replacement for EpisodeIngestor, backed by GraphStore
    instead of Neo4j.
    """

    def __init__(self, graph_store: GraphStore):
        self.graph_store = graph_store
        self._episode_id = None

    def bootstrap(self, episode: dict) -> str:
        """
        Loads the episode's initial_home_config into the graph.
        Matches EpisodeIngestor.bootstrap()'s contract: takes the full
        episode dict, returns an episode_id string.
        """
        self.graph_store.load_episode(episode)
        # derive a simple episode id from meta info if available
        meta = episode.get("meta", {})
        self._episode_id = f"{meta.get('query_type', 'qt')}_seed{meta.get('seed', 0)}"
        return self._episode_id

    def ingest_observation(self, tool_name: str, tool_result: dict,
                            timestamp: str, episode_id: str,
                            step_id: int, tool_params: dict) -> int:
        """
        Called after every tool call the agent makes. Inspects the
        tool's result and, if it represents a device/attribute state
        change, writes it into the graph via update_state().

        Returns the number of facts (state changes) written — used
        by the agent for its facts_written metric.

        Currently handles the two tools that actually change device
        state: execute_command and write_attribute. Read-only tools
        (get_room_states, get_room_devices, etc.) write nothing.
        """
        written = 0

        if tool_name not in ("execute_command", "write_attribute"):
            return written

        data = tool_result.get("data", {})
        if not isinstance(data, dict):
            return written

        device_id = tool_params.get("device_id")
        cluster_name = tool_params.get("cluster_id")  # Matter cluster name, e.g. "OnOff"
        if not device_id or not cluster_name:
            return written

        cluster_id = f"{device_id}.{cluster_name}"

        # write_attribute gives us the attribute_id + value directly
        if tool_name == "write_attribute":
            attr_name = tool_params.get("attribute_id")
            new_value = tool_params.get("value")
            if attr_name is not None:
                update_state(self.graph_store, cluster_id, attr_name, new_value, timestamp)
                written += 1

        # execute_command's effect is usually reflected in the tool's
        # response data (e.g. {"OnOff": true} after an "On" command)
        elif tool_name == "execute_command":
            for attr_name, new_value in data.items():
                update_state(self.graph_store, cluster_id, attr_name, new_value, timestamp)
                written += 1

        return written


# ─────────────────────────────────────────────────────────────────────
# EdgeTKGRetriever — replaces TKGRetriever
# ─────────────────────────────────────────────────────────────────────

class EdgeTKGRetriever:
    """
    Drop-in replacement for TKGRetriever, backed by GraphStore instead
    of Neo4j. Method names and output shapes (formatted text blocks)
    match the original so tkg_agent.py needs no changes.
    """

    def __init__(self, graph_store: GraphStore, window_minutes: int = 30):
        self.graph_store = graph_store
        self.window_minutes = window_minutes

    def get_room_state(self, room_id: str) -> str:
        """
        Formatted summary of a room's current known environment,
        matching TKGRetriever.get_room_state()'s output shape.
        """
        room_id = room_id.replace("room:", "")
        active = get_active_intervals(self.graph_store, room_id)

        if not active:
            return f"[TKG] No facts found for room:{room_id}"

        lines = [f"[TKG] room:{room_id}"]
        for entry in active:
            ev = entry["evidence"]
            lines.append(
                f"  {ev['attribute']:<25} -> {entry['value']}  (t={ev['start_time']})"
            )
        return "\n".join(lines)

    def get_device_state(self, device_id: str) -> str:
        """
        Formatted summary of a device's currently known state,
        matching TKGRetriever.get_device_state()'s output shape.
        Pulls active intervals for every cluster belonging to this device.
        """
        device_id = device_id.replace("device:", "")
        device = self.graph_store.get_node("device_nodes", device_id)

        if not device:
            return f"[TKG] No facts found for device:{device_id}"

        lines = [f"[TKG] device:{device_id}"]
        found_any = False
        for cluster_name in device.get("clusters", []):
            cluster_id = f"{device_id}.{cluster_name}"
            intervals = get_intervals_for_cluster(self.graph_store, cluster_id)
            for iv in intervals:
                if iv["end_time"] is None:  # only currently active state
                    lines.append(
                        f"  {iv['attribute_name']:<25} -> {iv['value']}  (t={iv['start_time']})"
                    )
                    found_any = True

        if not found_any:
            return f"[TKG] No facts found for device:{device_id}"
        return "\n".join(lines)

    def is_device_on(self, device_id: str) -> bool:
        """Returns True/False/None for is_on state of a device."""
        device_id = device_id.replace("device:", "")
        cluster_id = f"{device_id}.OnOff"
        intervals = get_intervals_for_cluster(self.graph_store, cluster_id, "OnOff")
        active = next((i for i in intervals if i["end_time"] is None), None)
        if active is None:
            return None
        return bool(active["value"])

    def get_room_temperature(self, room_id: str):
        """Returns the room's current temperature, or None if unknown."""
        room_id = room_id.replace("room:", "")
        location = self.graph_store.get_node("location_nodes", room_id)
        if not location:
            return None
        return location.get("temperature")

    def get_recent_changes(self, since_timestamp=None, limit=15) -> str:
        """
        Formatted list of recently active intervals across the whole
        graph. Simplified relative to the Neo4j version (no real-time
        window arithmetic needed — SimuHome time is already simulated
        and tracked via the graph's own timestamps).
        """
        all_active = []
        for room_id, loc in self.graph_store.graph.get("location_nodes", {}).items():
            all_active.extend(get_active_intervals(self.graph_store, room_id))

        if not all_active:
            return "[TKG] No recent changes found"

        # sort by most recent start_time first, cap at limit
        all_active.sort(key=lambda e: e["evidence"]["start_time"], reverse=True)
        lines = ["[TKG] Recent changes:"]
        for entry in all_active[:limit]:
            ev = entry["evidence"]
            lines.append(
                f"  {ev['cluster_id']:<40} {ev['attribute']:<20} -> {entry['value']}  (t={ev['start_time']})"
            )
        return "\n".join(lines)

    def get_current_time_from_graph(self):
        """No dedicated clock node in this schema; agent falls back
        to its own current_time tracking. Returning None signals that."""
        return None
