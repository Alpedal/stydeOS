```python
"""
Modul för att läsa Forge Command Centers datastruktur och beräkna dashboard-statistik.

Användning:
    from dashboard_data import read_forge_data
    stats = read_forge_data("path/to/forge.json")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
"""

import json
from pathlib import Path
from typing import Any, Optional


def _parse_run(run_dir: Path) -> dict[str, Any]:
    """
    Läs eval.json från en run-mapp och returnera score och pass-status.
    Hanterar saknad eller trasig fil med None-värden.
    """
    eval_file = run_dir / "eval.json"
    eval_data: Optional[dict] = None
    if eval_file.exists():
        try:
            eval_data = json.loads(eval_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            eval_data = None

    score = None
    passed = None
    if eval_data:
        score = eval_data.get("score")
        passed = eval_data.get("passed")
        # Om passed saknas, härled från score (tröskel 0.5)
        if passed is None and score is not None:
            passed = score >= 0.5

    return {
        "score": score,
        "passed": passed,
    }


def _compute_blueprint_stats(
    bp_id: str,
    bp_name: str,
    runs: list[dict],
) -> dict[str, Any]:
    """Beräkna statistik för en enskild blueprint."""
    runs_count = len(runs)
    scores = [r["score"] for r in runs if r["score"] is not None]
    avg_score = sum(scores) / len(scores) if scores else None

    # Trend: senaste 5 runs (sorterade efter run_id)
    trend = [
        {"run_id": r["run_id"], "score": r["score"], "passed": r["passed"]}
        for r in runs[-5:]
    ]

    # Fail: passed=False eller score under 0.5 (om passed saknas)
    fails = sum(
        1 for r in runs
        if r["passed"] is False
        or (r["passed"] is None and r["score"] is not None and r["score"] < 0.5)
    )
    fail_rate = fails / runs_count if runs_count > 0 else None

    return {
        "blueprint_id": bp_id,
        "name": bp_name,
        "runs_count": runs_count,
        "avg_score": avg_score,
        "trend": trend,
        "fail_rate": fail_rate,
    }


def read_forge_data(forge_path: str | Path = "forge.json") -> dict[str, Any]:
    """
    Läs forge.json och tillhörande run-mappar, beräkna statistik.

    Förväntad forge.json-struktur:
    {
        "blueprints": [{"id": "...", "name": "..."}],
        "runs": [{"run_id": "...", "blueprint_id": "..."}]
    }

    Returnerar dict med nycklarna 'blueprints' (lista per blueprint)
    och 'total' (sammanställning över alla runs).
    """
    forge_file = Path(forge_path)
    if not forge_file.exists():
        raise FileNotFoundError(f"forge.json saknas: {forge_file}")

    forge_data = json.loads(forge_file.read_text(encoding="utf-8"))
    blueprints = forge_data.get("blueprints", [])
    runs_meta = forge_data.get("runs", [])

    # Skapa uppslag blueprint_id -> namn
    bp_map: dict[str, str] = {bp["id"]: bp.get("name", bp["id"]) for bp in blueprints}

    # Samla runs per blueprint
    bp_runs: dict[str, list[dict]] = {}
    for run_meta in runs_meta:
        bp_id = run_meta.get("blueprint_id")
        run_id = run_meta.get("run_id")
        if not bp_id or not run_id:
            continue  # ogiltig run-rad

        run_dir = forge_file.parent / "runs" / f"run_{run_id}"
        eval_result = _parse_run(run_dir)

        bp_runs.setdefault(bp_id, []).append({
            "run_id": run_id,
            **eval_result,
        })

    # Sortera runs inom varje blueprint (numerisk sortering på run_id)
    for runs in bp_runs.values():
        runs.sort(key=lambda r: r["run_id"])

    # Beräkna statistik per blueprint
    blueprint_stats = []
    total_runs = 0
    all_scores = []
    total_fails = 0

    for bp_id, runs in bp_runs.items():
        bp_name = bp_map.get(bp_id, bp_id)
        stats = _compute_blueprint_stats(bp_id, bp_name, runs)
        blueprint_stats.append(stats)

        total_runs += stats["runs_count"]
        all_scores.extend(
            r["score"] for r in runs if r["score"] is not None
        )
        total_fails += int(stats["fail_rate"] * stats["runs_count"]) if stats["fail_rate"] else 0

    total_avg = sum(all_scores) / len(all_scores) if all_scores else None
    total_fail_rate = total_fails / total_runs if total_runs > 0 else None

    return {
        "blueprints": blueprint_stats,
        "total": {
            "runs_count": total_runs,
            "avg_score": total_avg,
            "fail_rate": total_fail_rate,
        },
    }
```