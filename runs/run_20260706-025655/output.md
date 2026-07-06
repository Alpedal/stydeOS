```python
"""
forge_dashboard.py — Data pipeline for Forge Command Center.

Reads forge.json and all run directories, computes per-blueprint statistics
(avg score, trend, fail rate) and returns a JSON-ready dict.
All file I/O is done from disk; no caching. Stdlib only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_eval(run_dir: Path) -> tuple[Optional[float], Optional[str]]:
    """
    Load eval.json from a run directory.

    Returns (score, result). Either value may be None if the file is missing
    or the field is absent.
    """
    eval_path = run_dir / "eval.json"
    if not eval_path.exists():
        return None, None

    try:
        with open(eval_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None, None

    score = data.get("score")  # expected float 0..1
    result = data.get("result")  # "pass" / "fail"
    # Ensure score is a number if present
    if score is not None and not isinstance(score, (int, float)):
        score = None
    if result is not None and not isinstance(result, str):
        result = None
    return score, result


def _is_fail(score: Optional[float], result: Optional[str]) -> Optional[bool]:
    """
    Determine whether a run is a failure based on score or result.

    - If score is present, fail if score < 0.5.
    - If only result is present, fail if result == "fail".
    - If nothing is present, return None (unknown).
    """
    if score is not None:
        # score is a number, treat < 0.5 as fail
        return score < 0.5
    if result is not None:
        return result == "fail"
    return None


def _compute_blueprint_stats(
    name: str,
    runs: list[dict[str, Any]],
    forge_root: Path,
) -> dict[str, Any]:
    """
    Compute statistics for a single blueprint.

    Parameters
    ----------
    name : str
        Blueprint identifier.
    runs : list of run dicts from forge.json (each must have 'run_id').
    forge_root : Path
        Directory containing forge.json (parent of 'runs/').

    Returns
    -------
    dict with keys: name, total_runs, avg_score, trend, fail_rate.
    """
    scores: list[float] = []
    fails: list[bool] = []

    for run in runs:
        run_id = run.get("run_id")
        if not isinstance(run_id, str):
            continue

        run_dir = forge_root / "runs" / f"run_{run_id}"
        if not run_dir.is_dir():
            continue

        score, result = _read_eval(run_dir)
        if score is not None:
            scores.append(score)
        fail_flag = _is_fail(score, result)
        if fail_flag is not None:
            fails.append(fail_flag)

    total_runs = len(runs)

    # Average score (only over runs where score is known)
    avg_score: Optional[float] = None
    if scores:
        avg_score = sum(scores) / len(scores)

    # Trend: scores of the last 5 runs (chronological order as in forge.json)
    # runs list is in the order they appear in forge.json, oldest first.
    trend = scores[-5:] if len(scores) >= 5 else scores  # keep oldest-first

    # Fail rate (only over runs where failure could be determined)
    fail_rate: Optional[float] = None
    if fails:
        fail_rate = sum(1 for f in fails if f) / len(fails)

    return {
        "name": name,
        "total_runs": total_runs,
        "avg_score": avg_score,
        "trend": trend,
        "fail_rate": fail_rate,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_and_compute_statistics(forge_path: str) -> dict[str, Any]:
    """
    Read forge.json and all run directories, return aggregated statistics.

    Parameters
    ----------
    forge_path : str
        Path to forge.json file.

    Returns
    -------
    dict with:
        - "blueprints": list of per-blueprint stats
        - "overall": dict with total_runs, avg_score, fail_rate
    """
    forge_path = Path(forge_path)
    if not forge_path.exists():
        raise FileNotFoundError(f"forge.json not found at {forge_path}")

    with open(forge_path, encoding="utf-8") as f:
        forge_data = json.load(f)

    forge_root = forge_path.parent

    # Group runs by blueprint
    blueprint_runs: dict[str, list[dict[str, Any]]] = {}
    for run in forge_data.get("runs", []):
        bp = run.get("blueprint")
        if not isinstance(bp, str):
            continue
        blueprint_runs.setdefault(bp, []).append(run)

    # Compute per-blueprint stats
    blueprints = []
    global_scores: list[float] = []
    global_fails: list[bool] = []
    global_total_runs = len(forge_data.get("runs", []))

    for bp_name, runs in blueprint_runs.items():
        bp_stats = _compute_blueprint_stats(bp_name, runs, forge_root)
        blueprints.append(bp_stats)

        # Aggregate for overall
        for run in runs:
            run_id = run.get("run_id")
            if not isinstance(run_id, str):
                continue
            run_dir = forge_root / "runs" / f"run_{run_id}"
            if not run_dir.is_dir():
                continue
            score, result = _read_eval(run_dir)
            if score is not None:
                global_scores.append(score)
            fail_flag = _is_fail(score, result)
            if fail_flag is not None:
                global_fails.append(fail_flag)

    # Overall statistics
    overall_avg: Optional[float] = None
    if global_scores:
        overall_avg = sum(global_scores) / len(global_scores)

    overall_fail_rate: Optional[float] = None
    if global_fails:
        overall_fail_rate = sum(1 for f in global_fails if f) / len(global_fails)

    return {
        "blueprints": blueprints,
        "overall": {
            "total_runs": global_total_runs,
            "avg_score": overall_avg,
            "fail_rate": overall_fail_rate,
        },
    }
```