OPEN ITEM — Agent Integration (discovered while reviewing tkg_agent.py)
─────────────────────────────────────────────────────────────────────
1. update_state() — needed to close/reopen StateIntervals when the
   agent's execute_command / write_attribute changes a device value
   mid-episode. Currently the graph is frozen at episode-start state.

2. EdgeTKGRetriever — drop-in replacement for TKGRetriever, same
   method names (get_device_state, get_room_state, is_device_on,
   get_room_temperature, get_recent_changes), backed by GraphStore
   instead of Neo4j.

3. EdgeEpisodeIngestor — drop-in replacement for EpisodeIngestor,
   needs bootstrap() (you basically have this as load_episode) and
   ingest_observation() (new — writes agent's tool results into graph).

4. Once 1–3 exist, only 2 lines change in tkg_agent.py's __init__.
