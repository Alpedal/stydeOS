Alert Engine -- Blueprint (Updated)
Purpose
Monitor agent, GPU, and system telemetry against configurable alert rules and push real-time notifications to the Forge Dashboard when thresholds are breached.
Overview
The Alert Engine is the monitoring and notification subsystem within the Forge Dashboard. It continuously evaluates configurable alert rules against live telemetry from agents, GPU clusters, and system resources. When a rule threshold is breached, it triggers a push notification directly in the dashboard.
Architecture
Telemetry sources (Agent, GPU, RAM) publish metrics at regular intervals to the Alert Evaluator, which runs a Rule Engine for threshold checking with cooldowns and severity classification. On breach, a notification event flows to the Notification Bus, which dispatches via Push Dispatcher to the Dashboard UI.
Alert Rules
Rule ID           Metric              Threshold       Severity  Cooldown
gpu-temp          GPU Temperature     > 85 C          critical  5 min
ram-usage         RAM Utilization     > 90 %          warning   10 min
agent-failure     Agent Failure Rate  > 10 %          critical  15 min
score-drop        Agent Score Drop    > 15 points     warning   30 min
States
Normal       -- all metrics within bounds
Alerting     -- threshold breached; notification sent
Cooldown     -- alert fired recently; suppressed until cooldown expires
Recovered    -- metric returned to normal; optional recovery notification
Configuration
All rules are defined in config.yaml. Engine reloads config on startup and via hot-reload dashboard admin action.
Cooldown Reset Cascading Matrix
When a new alert arrives for an already-cooldowning rule, severity comparison determines whether the cooldown timer resets.
Current Severity -> New Severity  Reset Timer?  New Duration      Cost Implication
LOW            -> LOW              No            unchanged         No additional cost
LOW            -> MEDIUM           Yes           MEDIUM duration   Medium alert dispatched (notification cost)
LOW            -> HIGH             Yes           HIGH duration     High alert dispatched (highest urgency cost)
MEDIUM         -> LOW              No            unchanged         No additional cost (suppressed)
MEDIUM         -> MEDIUM           No            unchanged         No additional cost
MEDIUM         -> HIGH             Yes           HIGH duration     High alert dispatched, may trigger escalation pipeline
HIGH           -> LOW              No            unchanged         No additional cost
HIGH           -> MEDIUM           No            unchanged         No additional cost
HIGH           -> HIGH             No            unchanged         No additional cost
Key: A cooldown reset (Yes) means the timer restarts from zero using the new severity's full duration. The alert is dispatched at the new severity level. Non-reset cases remain suppressed for the original cooldown's remaining time.
Example timers:
- LOW cooldown: 5 min, resets to 10 min on MEDIUM upgrade, 15 min on HIGH upgrade.
- MEDIUM cooldown: 10 min, resets to 15 min on HIGH upgrade.
- HIGH cooldown: 15 min, never resets (already highest).
Race Conditions and Concurrency
Cooldown Reset Atomicity
When two alerts for the same metric-agent pair arrive in the same evaluation tick, the engine must guarantee atomic read-modify-write on the cooldown state dictionary. Implementation: use a per-rule mutex (threading.Lock) scoped to the rule ID hash. Both threads acquire the same lock before checking the timer and before writing the new expiry. A compare-and-swap pattern validates that the last-triggered timestamp has not changed between read and write.
Shared state map structure:
cooldown_state = {
  "gpu-temp:worker-03": {
    "expires_at": 1719500000.0,
    "severity": "critical",
    "last_triggered": 1719499700.0
  }
}
Hot-Reload Thread Safety
When a dashboard admin triggers a config hot-reload, the Alert Evaluator must not mid-evaluation swap rule definitions. Sequence:
1. Acquire a global read-write lock (RWLock).
2. New config is parsed into a staging dictionary.
3. Once fully parsed and validated, acquire the write lock and atomically swap the active rules pointer.
4. All evaluation loops hold a read lock during rule lookups; the swap occurs only when zero read locks are held.
5. Cooldown state is NOT cleared on hot-reload -- stale cooldowns remain honored to prevent alert bursts after config change.
Locking Strategy
Per-severity mutex pool: a fixed-size pool of 8 locks, each covering a severity bucket via consistent hashing. This avoids one global lock while bounding contention. Lock acquisition order is always: per-severity bucket lock first, then per-rule mutex. Deadlock prevention uses a strict lock ordering invariant (bucket lock < rule lock) enforced by a runtime assertion.
Dynamicdrop Threshold Detection Algorithm
When a rule uses mode: dynamicdrop, the engine does NOT use a static numeric threshold. Instead it tracks a rolling window (default 60 seconds, configurable via window_seconds) of recent metric values for each agent.
Detection logic per evaluation tick:
1. Retrieve the current metric value M_cur.
2. Retrieve the windowed baseline: B = mean of last N samples (default N=5) from the rolling buffer.
3. Compute delta_abs = B - M_cur.
4. Compute delta_pct = (delta_abs / B) * 100  (if B=0, use absolute drop only).
5. If delta_pct > sensitivity_pct (default 15) OR delta_abs > sensitivity_abs (default 2.0 units), transition to Alerting state.
6. Recovered transition: when M_cur >= B * recovery_threshold (default 0.95, meaning 95% of baseline), fire recovery notification and return to Normal.
Configurable parameters:
- sensitivity_pct: percentage drop required to alert (default 15)
- sensitivity_abs: absolute drop required (default 2.0)
- window_seconds: rolling window length (default 60)
- recovery_threshold: fraction of baseline needed for recovery (default 0.95)
- required_samples: minimum samples before evaluation starts (default 3)
Dynamicdrop alert transitions:
Normal state -> delta detection triggers Alerting -> notification sent -> enters Cooldown -> on recovery check passes -> Recovered notification (optional) -> Normal.
Notification Bus Reliability and Disconnection Handling
WebSocket Disconnect Buffering
When the Dashboard WebSocket connection drops, the Notification Bus does not discard pending alerts. It buffers them in an in-memory deque with bounded capacity (default 10,000). Each buffered notification carries a monotonic sequence ID, the timestamp, and a deduplication hash.
Buffer structure per pending notification:
{
  "seq": 1042,
  "ts": 1719500000.123,
  "dedup_hash": "sha256(metric+agent+rule_id)",
  "payload": { ... }
}
Persistence
In-memory buffer is the primary store for speed. For crash resilience, a companion disk-backed queue writes to .alert_engine/notif_queue/ using append-only JSONL files. On graceful shutdown, the engine performs a final flush. On ungraceful shutdown, on next startup the engine replays the JSONL files from last known good checkpoint.
Reconnect and Replay
On WebSocket reconnection:
1. Deduplicate: scan all buffered notifications and drop any whose dedup_hash already appears in the Dashboard's last acknowledged batch (ACK range sent by dashboard on reconnect).
2. Rate-limit replay: push at most 5 notifications per second to avoid flooding the reconnecting client.
3. Remaining stale notifications older than max_buffer_age (default 5 minutes) are discarded silently with a log line.
4. After replay drain, normal real-time flow resumes.
Deduplication logic:
dedup_hash = f"{rule_id}:{agent_id}:{alert_type}"
Two alerts with the same hash within the same cooldown window are merged -- only the first is dispatched, subsequent ones update the timestamp only.
Example JSON Payloads
Minimal alert:
{
  "type": "alert",
  "rule_id": "gpu-temp",
  "agent_id": "worker-03",
  "severity": "critical",
  "value": 92,
  "threshold": 85,
  "ts": 1719500000.123
}
Typical alert with agent metadata:
{
  "type": "alert",
  "rule_id": "ram-usage",
  "agent_id": "worker-07",
  "severity": "warning",
  "value": 94.2,
  "threshold": 90,
  "unit": "percent",
  "ts": 1719500010.456,
  "agent": {
    "name": "worker-07",
    "host": "10.0.1.27",
    "gpu_count": 4
  },
  "cooldown_remaining": 540
}
Alert with enrichment and recovery:
{
  "type": "recovery",
  "rule_id": "gpu-temp",
  "agent_id": "worker-03",
  "severity": "critical",
  "value": 62,
  "threshold": 85,
  "ts": 1719500300.789,
  "recovered_from": "alert-ok",
  "duration_seconds": 300,
  "agent": {
    "name": "worker-03",
    "host": "10.0.1.23"
  },
  "dashboard_url": "/dashboard/alerts?agent=worker-03&rule=gpu-temp"
}
Dashboard Integration
The Forge Dashboard polls two endpoints for alert state:
GET /api/v1/alerts/active -- returns all currently-alerting rules with value, severity, and remaining cooldown. Dashboard queries this every 5 seconds (configurable via refresh_interval) and renders alerts in the notification sidebar.
GET /api/v1/alerts/history?since=<epoch>&limit=50 -- returns recent alert events for history panel. Query parameters: since (unix epoch timestamp filter), limit (max results, default 50), severity (filter by severity), agent_id (filter by agent).
Push notifications arrive via the WebSocket channel on topic dashboard:alerts. On receiving a push, the dashboard immediately updates the active alert count badge without waiting for the next poll cycle. Refresh cadence: poll every 5s, push is real-time.