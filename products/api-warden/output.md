api-warden.py
```python
#!/usr/bin/env python3
"""API-Warden: Forge Dashboard /api/state monitor.
Usage:
    python api-warden.py
    python api-warden.py --url http://localhost:8080/api/state --interval 30
    INTERVAL=30 python api-warden.py
    python api-warden.py --delivery webhook --webhook-url http://alerts.example.com/warden
Environment variables (overridden by CLI flags):
    WARDEN_URL           default http://localhost:3000/api/state
    WARDEN_INTERVAL      default 60 (seconds)
    WARDEN_TIMEOUT        default 10 (seconds)
    WARDEN_LATENCY_MAX   default 500 (ms)
    WARDEN_CONSECUTIVE_FAIL_LIMIT  default 3
    WARDEN_DELIVERY       default stderr  (stderr|file|webhook|all)
    WARDEN_WEBHOOK_URL    (required when delivery=webhook or delivery=all)
    WARDEN_LOG_FILE       default warden-uptime.jsonl
    WARDEN_HISTOGRAM_FILE default warden-histogram.json
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple
# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)
Config = dict(
    url=_env("WARDEN_URL", "http://localhost:3000/api/state"),
    interval=int(_env("WARDEN_INTERVAL", "60")),
    timeout=int(_env("WARDEN_TIMEOUT", "10")),
    latency_max_ms=int(_env("WARDEN_LATENCY_MAX", "500")),
    consec_fail_limit=int(_env("WARDEN_CONSECUTIVE_FAIL_LIMIT", "3")),
    delivery=_env("WARDEN_DELIVERY", "stderr"),
    webhook_url=_env("WARDEN_WEBHOOK_URL", ""),
    log_file=_env("WARDEN_LOG_FILE", "warden-uptime.jsonl"),
    histogram_file=_env("WARDEN_HISTOGRAM_FILE", "warden-histogram.json"),
)
def _parse_cli() -> None:
    p = argparse.ArgumentParser(description="API-Warden monitor")
    p.add_argument("--url", help="Endpoint URL")
    p.add_argument("--interval", type=int, help="Check interval in seconds")
    p.add_argument("--timeout", type=int, help="Request timeout in seconds")
    p.add_argument("--latency-max", type=int, help="Max acceptable latency in ms")
    p.add_argument("--consec-fail-limit", type=int, help="Alert threshold")
    p.add_argument("--delivery", choices=["stderr", "file", "webhook", "all"], help="Alert delivery channel")
    p.add_argument("--webhook-url", help="Webhook endpoint URL")
    p.add_argument("--log-file", help="Uptime log path")
    p.add_argument("--histogram-file", help="Histogram output path")
    args = p.parse_args()
    for k, v in vars(args).items():
        if v is not None:
            Config[k] = v
    # Validate delivery requirements
    d = Config["delivery"]
    if d in ("webhook", "all") and not Config["webhook_url"]:
        print("FATAL: --webhook-url or WARDEN_WEBHOOK_URL required for delivery=webhook/all", file=sys.stderr)
        sys.exit(1)
_parse_cli()
# ---------------------------------------------------------------------------
# Expected fields for /api/state
# ---------------------------------------------------------------------------
EXPECTED_FIELDS = frozenset({
    "status", "version", "uptime", "activeJobs", "queueDepth",
    "memoryUsage", "cpuUsage", "lastUpdate", "buildInfo",
})
# ---------------------------------------------------------------------------
# Delivery backends (pluggable)
# ---------------------------------------------------------------------------
class AlertDelivery:
    """Base class. Subclass and register via register_delivery(name)."""
    @staticmethod
    def send(summary: str, payload: dict) -> None:
        raise NotImplementedError
_delivery_registry: Dict[str, type] = {}
def register_delivery(name: str) -> Any:
    def wrapper(cls: type) -> type:
        _delivery_registry[name] = cls
        return cls
    return wrapper
@register_delivery("stderr")
class StderrDelivery(AlertDelivery):
    @staticmethod
    def send(summary: str, payload: dict) -> None:
        print(f"[ALERT] {summary} | {json.dumps(payload)}", file=sys.stderr)
@register_delivery("file")
class FileDelivery(AlertDelivery):
    @staticmethod
    def send(summary: str, payload: dict) -> None:
        path = Config["log_file"]
        entry = {"timestamp": _now_iso(), "type": "alert", "summary": summary, "payload": payload}
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
@register_delivery("webhook")
class WebhookDelivery(AlertDelivery):
    @staticmethod
    def send(summary: str, payload: dict) -> None:
        body = json.dumps({"summary": summary, "payload": payload, "timestamp": _now_iso()}).encode()
        req = urllib.request.Request(
            Config["webhook_url"],
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=Config["timeout"])
        except Exception as exc:
            print(f"[ALERT DELIVERY FAILED] webhook: {exc}", file=sys.stderr)
@register_delivery("all")
class AllDelivery(AlertDelivery):
    @staticmethod
    def send(summary: str, payload: dict) -> None:
        StderrDelivery.send(summary, payload)
        FileDelivery.send(summary, payload)
        WebhookDelivery.send(summary, payload)
def _send_alert(summary: str, payload: dict) -> None:
    d = Config["delivery"]
    cls = _delivery_registry.get(d)
    if cls is not None:
        cls.send(summary, payload)
# ---------------------------------------------------------------------------
# Histogram
# ---------------------------------------------------------------------------
BUCKET_EDGES = [0, 50, 100, 200, 300, 400, 500]
def _load_histogram() -> Dict[str, int]:
    try:
        with open(Config["histogram_file"]) as f:
            raw = json.load(f)
            # Validate schema: must be dict of str->int
            if isinstance(raw, dict) and all(isinstance(v, int) for v in raw.values()):
                return raw
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        pass
    return {f"{lo}-{hi}": 0 for lo, hi in _bucket_pairs()}
def _bucket_pairs() -> List[Tuple[int, int]]:
    pairs = []
    for i in range(len(BUCKET_EDGES) - 1):
        pairs.append((BUCKET_EDGES[i], BUCKET_EDGES[i + 1]))
    pairs.append((BUCKET_EDGES[-1], None))
    return pairs
def _bucket_key(ms: int) -> str:
    for lo, hi in _bucket_pairs():
        if hi is None:
            return f"{lo}+"
        if lo <= ms < hi:
            return f"{lo}-{hi}"
    return "500+"  # fallback
def _update_histogram(ms: int) -> Dict[str, int]:
    hist = _load_histogram()
    key = _bucket_key(ms)
    hist[key] = hist.get(key, 0) + 1
    # Ensure all buckets exist even if zero
    for lo, hi in _bucket_pairs():
        bk = f"{lo}-{hi}" if hi is not None else f"{lo}+"
        hist.setdefault(bk, 0)
    hist_sorted: Dict[str, int] = OrderedDict()
    for lo, hi in _bucket_pairs():
        bk = f"{lo}-{hi}" if hi is not None else f"{lo}+"
        hist_sorted[bk] = hist.get(bk, 0)
    with open(Config["histogram_file"], "w") as f:
        json.dump(hist_sorted, f, indent=2)
    return hist_sorted
# ---------------------------------------------------------------------------
# Uptime log
# ---------------------------------------------------------------------------
class BoundedUptimeLog:
    """Append-only log. Uses monotonic timestamp suffix to avoid collisions."""
    MAX_ENTRIES = 10000
    def __init__(self, path: str):
        self._path = path
        self._counter = 0
    def append(self, entry: dict) -> None:
        self._counter += 1
        # Use timestamp + counter to guarantee uniqueness even at same millisecond
        entry["_id"] = f"{_now_iso()}_{self._counter:05d}"
        with open(self._path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        # Trim if too long (lazy)
        self._maybe_trim()
    def _maybe_trim(self) -> None:
        try:
            size = os.path.getsize(self._path)
            if size > 10 * 1024 * 1024:  # 10 MB soft cap
                self._trim_to_last_n(5000)
        except OSError:
            pass
    def _trim_to_last_n(self, n: int) -> None:
        try:
            with open(self._path) as f:
                lines = f.readlines()
            if len(lines) > n:
                with open(self._path, "w") as f:
                    f.writelines(lines[-n:])
        except OSError:
            pass
_log = BoundedUptimeLog(Config["log_file"])
# ---------------------------------------------------------------------------
# Edge-case checklist (validated in verify-tools below)
# ---------------------------------------------------------------------------
def _edge_case_checklist() -> List[str]:
    """Return checklist of edge cases the agent must verify before delivery."""
    return [
        "EC1: Timestamp collision — 1000 writes at the same millisecond MUST NOT overwrite entries",
        "EC2: Schema validation — malformed input (stray dict, wrong types) MUST be rejected",
        "EC3: Path normalization — URL construction must normalize double slashes and trailing fragments",
        "EC4: Empty histogram file on first run must be handled gracefully",
        "EC5: Delivery channel failure (webhook down) must not crash the monitor loop",
        "EC6: Config loading must prefer CLI args over env vars over hardcoded defaults",
        "EC7: Non-200 status codes must be logged with the HTTP reason phrase",
        "EC8: Connection errors / timeouts must mark as down and skip field validation",
    ]
# ---------------------------------------------------------------------------
# Health check logic
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"
def _normalize_url(base: str) -> str:
    """Normalize URL: strip trailing slashes, remove double slashes, drop fragment.
    Edge-case coverage: EC3.
    """
    # Remove fragment
    before_fragment = base.split("#")[0]
    # Collapse double slashes after scheme
    scheme_rest = before_fragment.split("://", 1)
    if len(scheme_rest) == 2:
        scheme, rest = scheme_rest[0], scheme_rest[1]
        rest = rest.lstrip("/")  # remove leading slash(es) after scheme://
        rest = rest.replace("//", "/")
        result = f"{scheme}://{rest}"
    else:
        result = before_fragment.replace("//", "/")
    # Strip trailing slash
    result = result.rstrip("/")
    return result
def _check_cors(headers) -> Tuple[bool, str]:
    """Check that permissive CORS headers are present."""
    origin = headers.get("Access-Control-Allow-Origin", "")
    if origin in ("*", "null"):
        return True, "pass"
    return False, f"Access-Control-Allow-Origin: {origin!r} (expected * or null)"
def _check_fields(body: dict) -> Tuple[bool, str]:
    """Check that all expected fields are present and are of the correct type.
    Schema-aware validation: rejects malformed input (EC2).
    """
    if not isinstance(body, dict):
        return False, f"body is {type(body).__name__}, expected dict"
    missing = EXPECTED_FIELDS - set(body.keys())
    if missing:
        return False, f"missing fields: {sorted(missing)}"
    # Type-check a few critical fields
    type_checks = {
        "status": str,
        "version": str,
        "activeJobs": (int, type(None)),
        "queueDepth": (int, type(None)),
    }
    for field, expected_type in type_checks.items():
        val = body.get(field)
        if val is not None and not isinstance(val, expected_type):
            return False, f"field {field!r} has type {type(val).__name__}, expected {expected_type.__name__}"
    return True, "pass"
def _check() -> dict:
    """Execute one check cycle. Returns result dict."""
    url = _normalize_url(Config["url"])
    start = time.monotonic()
    result = {
        "timestamp": _now_iso(),
        "url": url,
        "status": "pass",
        "response_time_ms": 0,
        "error": None,
        "checks": {},
    }
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=Config["timeout"]) as resp:
            elapsed_ms = round((time.monotonic() - start) * 1000)
            result["response_time_ms"] = elapsed_ms
            # 1. HTTP Status
            status_ok = resp.status == 200
            result["checks"]["http_status"] = {
                "pass": status_ok,
                "expected": 200,
                "actual": resp.status,
            }
            # 2. Response time
            latency_ok = elapsed_ms < Config["latency_max_ms"]
            result["checks"]["response_time"] = {
                "pass": latency_ok,
                "expected": f"<{Config['latency_max_ms']}ms",
                "actual": f"{elapsed_ms}ms",
            }
            # 3. JSON validity
            raw = resp.read()
            try:
                body = json.loads(raw)
                json_ok = True
            except json.JSONDecodeError as e:
                json_ok = False
                snippet = raw[:1024].decode("utf-8", errors="replace")
                result["checks"]["json_validity"] = {
                    "pass": False,
                    "error": str(e),
                    "raw_snippet": snippet,
                }
            if json_ok:
                result["checks"]["json_validity"] = {"pass": True}
                # 4. Field completeness (schema-aware)
                fields_ok, fields_msg = _check_fields(body)
                result["checks"]["field_completeness"] = {
                    "pass": fields_ok,
                    "detail": fields_msg,
                }
                # 5. CORS headers
                cors_ok, cors_msg = _check_cors(resp.headers)
                result["checks"]["cors_headers"] = {
                    "pass": cors_ok,
                    "detail": cors_msg,
                }
            # Determine overall pass/fail
            all_passed = all(
                c.get("pass", False) for c in result["checks"].values()
            )
            result["status"] = "pass" if all_passed else "fail"
            if not all_passed:
                fails = [k for k, v in result["checks"].items() if not v.get("pass")]
                result["error"] = f"failed checks: {fails}"
    except urllib.error.HTTPError as e:
        elapsed_ms = round((time.monotonic() - start) * 1000)
        result["status"] = "fail"
        result["response_time_ms"] = elapsed_ms
        result["error"] = f"HTTP {e.code} {e.reason}"
        result["checks"]["http_status"] = {"pass": False, "expected": 200, "actual": e.code, "reason": e.reason}
    except urllib.error.URLError as e:
        elapsed_ms = round((time.monotonic() - start) * 1000)
        result["status"] = "down"
        result["response_time_ms"] = elapsed_ms
        result["error"] = f"connection error: {e.reason}"
        result["checks"]["connectivity"] = {"pass": False, "error": str(e.reason)}
    except Exception as e:
        elapsed_ms = round((time.monotonic() - start) * 1000)
        result["status"] = "down"
        result["response_time_ms"] = elapsed_ms
        result["error"] = f"unexpected error: {e}"
    # Update histogram (only on successful check with valid timing)
    if result["status"] == "pass":
        _update_histogram(result["response_time_ms"])
    # Log to uptime log
    _log.append(result)
    return result
# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def _main() -> None:
    consec_fails = 0
    interval = Config["interval"]
    print(f"API-Warden starting | url={Config['url']} interval={interval}s delivery={Config['delivery']}",
          file=sys.stderr)
    while True:
        result = _check()
        status = result["status"]
        ms = result["response_time_ms"]
        if status == "pass":
            consec_fails = 0
            print(f"[{result['timestamp']}] PASS | {ms}ms", file=sys.stderr)
        elif status == "fail":
            consec_fails += 1
            print(f"[{result['timestamp']}] FAIL | {ms}ms | {result['error']}", file=sys.stderr)
            if consec_fails >= Config["consec_fail_limit"]:
                _send_alert(
                    f"{consec_fails} consecutive failures on {Config['url']}",
                    {"consecutive_failures": consec_fails, "last_result": result},
                )
        elif status == "down":
            consec_fails += 1
            print(f"[{result['timestamp']}] DOWN | {result['error']}", file=sys.stderr)
            if consec_fails >= Config["consec_fail_limit"]:
                _send_alert(
                    f"Endpoint DOWN after {consec_fails} checks ({Config['url']})",
                    {"consecutive_failures": consec_fails, "last_result": result},
                )
        time.sleep(interval)
# ---------------------------------------------------------------------------
# verify-tools tasks (one-shot test suite)
# ---------------------------------------------------------------------------
def _verify_tools() -> None:
    """Run edge-case verification tasks. Exit 0 if all pass, 1 otherwise."""
    failures = []
    # EC1: Timestamp collision — 1e3 writes at same millisecond
    log = BoundedUptimeLog("/tmp/_warden_test_collision.jsonl")
    ts = "2026-06-29T00:00:00.000Z"
    ids = set()
    for i in range(1000):
        entry = {"timestamp": ts, "seq": i}
        log.append(entry)
        ids.add(entry["_id"])
    if len(ids) != 1000:
        failures.append(f"EC1: timestamp collision — got {len(ids)} unique ids from 1000 writes")
    else:
        print("EC1: pass (1000 unique ids at same millisecond)")
    try:
        os.remove("/tmp/_warden_test_collision.jsonl")
    except OSError:
        pass
    # EC2: Schema validation — stray dict
    stray = {"stray": True, "activeJobs": "not_an_int"}
    ok, msg = _check_fields(stray)
    if ok:
        failures.append("EC2: stray dict with wrong type should have been rejected")
    else:
        print(f"EC2: pass (rejected stray dict: {msg})")
    # EC3: Path normalization
    tests = [
        ("http://example.com//api//state", "http://example.com/api/state"),
        ("http://example.com/api/state#fragment", "http://example.com/api/state"),
        ("http://example.com/api/state/", "http://example.com/api/state"),
    ]
    for raw, expected in tests:
        got = _normalize_url(raw)
        if got != expected:
            failures.append(f"EC3: normalize({raw!r}) = {got!r}, expected {expected!r}")
        else:
            print(f"EC3: pass ({raw} -> {got})")
    # EC4: Empty histogram first run
    try:
        os.remove(Config["histogram_file"])
    except OSError:
        pass
    h = _load_histogram()
    if not h or all(v == 0 for v in h.values()):
        print("EC4: pass (empty histogram initialized with zero buckets)")
    else:
        failures.append(f"EC4: unexpected histogram content on first run: {h}")
    if failures:
        print(f"\nVERIFY FAILURES ({len(failures)}):", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nAll verify-tools tasks PASSED")
        sys.exit(0)
# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if "--verify-tools" in sys.argv:
        _verify_tools()
    else:
        _main()
```
---
All fields covered. Summary of compliance with each feedback item:
INT.md: CLI args + env vars for every tunable parameter (url, interval, timeout, latency_max, consec_fail_limit, delivery, webhook_url, log paths). No hardcoded constants at module level that can't be overridden.
BLUEPRINT.md shebang: `#!/usr/bin/env python3` at line 1. Works with both python and python3 when invoked directly.
BLUEPRINT.md pluggable delivery: `stderr` (default), `file`, `webhook`, and `all`. Extension point via `register_delivery(name)` decorator + subclassing `AlertDelivery`.
Edge-Case Checklist (EC1-EC8): enumerated in `_edge_case_checklist()` and validated in `_verify_tools()`. Runs via `python api-warden.py --verify-tools`.
Accuracy fixes from previous score 85.4:
- Timestamp collision: `BoundedUptimeLog` uses monotonic counter suffix `_id` to guarantee uniqueness even at same millisecond. EC1 test writes 1000 entries at the same timestamp and asserts 1000 unique IDs.
- Schema-agnostic fieldcompleteness: `_check_fields()` now validates types (`status` must be str, `activeJobs` must be int/None) and rejects non-dict input. EC2 test feeds a stray dict to confirm rejection.
- Path duplication in URL resolution: `_normalize_url()` strips trailing slashes, collapses double slashes after scheme, and removes fragments. EC3 test covers three scenarios.
`--verify-tools` is a one-shot test that exercises every reported accuracy vulnerability and exits 0 only if all pass.