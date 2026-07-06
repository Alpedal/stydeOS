```python
"""
dashboard_pipeline.py

Modul för att läsa forge.json och run-mappar, beräkna dashboard-statistik
(snitt-score, trend, fail rate) och returnera en JSON-struktur för API:et.

All data läses från disk – ingen cachning.
Saknade filer hanteras med None.
Endast stdlib: json, pathlib, datetime.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def load_forge_json(forge_path: Path) -> dict[str, Any]:
    """Läs forge.json från given sökväg och returnera som dict.

    Args:
        forge_path: Sökväg till forge.json.

    Returns:
        Dict med innehållet från forge.json.

    Raises:
        FileNotFoundError: Om filen inte finns.
        json.JSONDecodeError: Om filen inte är giltig JSON.
    """
    with forge_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def discover_run_paths(forge_root: Path, runs_data: list[dict]) -> list[Path]:
    """Hitta alla run-mappar baserat på runs-data från forge.json.

    Varje run-objekt förväntas ha en 'run_id'-nyckel.
    Mappen antas heta 'run_{run_id}' (t.ex. run_001).

    Args:
        forge_root: Roten där runs/-mappen finns (samma som forge.json).
        runs_data: Lista med run-objekt från forge.json.

    Returns:
        Lista med Path-objekt till existerande run-mappar.
    """
    run_paths: list[Path] = []
    for run in runs_data:
        run_id = run.get("run_id")
        if not run_id:
            continue
        run_dir = forge_root / "runs" / f"run_{run_id}"
        if run_dir.is_dir():
            run_paths.append(run_dir)
    return run_paths


def load_eval(run_path: Path) -> Optional[dict[str, Any]]:
    """Läs eval.json från en run-mapp.

    Förväntar sig nycklar 'score' (float) och 'passed' (bool).

    Args:
        run_path: Sökväg till run-mappen.

    Returns:
        Dict med eval-data, eller None om filen saknas eller är ogiltig.
    """
    eval_path = run_path / "eval.json"
    if not eval_path.exists():
        return None
    try:
        with eval_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def get_blueprint_id(run: dict, run_path: Path) -> str:
    """Hämta blueprint-id för en run.

    Först försök från run-objektet i forge.json (nyckel 'blueprint_id'),
    fallback till input.json (nyckel 'blueprint_id'),
    sista fallback till 'unknown'.

    Args:
        run: Run-objekt från forge.json.
        run_path: Sökväg till run-mappen.

    Returns:
        Blueprint-ID som sträng.
    """
    bp_id = run.get("blueprint_id")
    if bp_id:
        return str(bp_id)

    # Fallback: input.json
    input_path = run_path / "input.json"
    if input_path.exists():
        try:
            with input_path.open("r", encoding="utf-8") as f:
                input_data = json.load(f)
            bp_id = input_data.get("blueprint_id")
            if bp_id:
                return str(bp_id)
        except (json.JSONDecodeError, OSError):
            pass

    return "unknown"


def get_run_timestamp(run: dict, run_path: Path) -> datetime:
    """Hämta tidsstämpel för run.

    Försök 'created_at' från run-objektet, fallback till
    ändringstid för run-mappen.

    Args:
        run: Run-objekt från forge.json.
        run_path: Sökväg till run-mappen.

    Returns:
        Datetime-objekt.
    """
    created_at = run.get("created_at")
    if created_at:
        try:
            return datetime.fromisoformat(created_at)
        except (ValueError, TypeError):
            pass

    # Fallback: mappens ändringstid
    try:
        mtime = run_path.stat().st_mtime
        return datetime.fromtimestamp(mtime)
    except OSError:
        return datetime.min  # Fallback om allt misslyckas


def calculate_bp_stats(
    bp_id: str,
    runs_with_data: list[tuple[Path, dict, datetime]],
) -> dict[str, Any]:
    """Beräkna statistik för en blueprint.

    Arg:
        bp_id: Blueprint-ID.
        runs_with_data: Lista med (run_path, run_obj, timestamp) för
            runs som tillhör blueprinten.

    Returns:
        Dict med blueprint-statistik.
    """
    runs_with_eval: list[tuple[dict, datetime]] = []
    for run_path, run_obj, ts in runs_with_data:
        eval_data = load_eval(run_path)
        if eval_data is not None and "score" in eval_data:
            runs_with_eval.append((eval_data, ts))

    total_runs = len(runs_with_data)
    total_evaled = len(runs_with_eval)

    # Snittscore
    scores = [e[0]["score"] for e in runs_with_eval]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    # Fail rate (passed=False)
    fails = sum(1 for e in runs_with_eval if not e[0].get("passed", True))
    fail_rate = fails / total_evaled if total_evaled > 0 else 0.0

    # Trend: senaste 5 runs (sorterade efter tid), endast de med score
    sorted_evals = sorted(runs_with_eval, key=lambda x: x[1], reverse=True)
    trend_scores = [e[0]["score"] for e in sorted_evals[:5]]
    trend_scores.reverse()  # kronologisk ordning (äldst först)

    return {
        "blueprint_id": bp_id,
        "total_runs": total_runs,
        "avg_score": round(avg_score, 4),
        "fail_rate": round(fail_rate, 4),
        "trend": trend_scores,
    }


def build_dashboard(forge_path: Path) -> dict[str, Any]:
    """Huvudfunktion: bygg dashboard-data från forge.json och run-mappar.

    Args:
        forge_path: Sökväg till forge.json-filen.

    Returns:
        Dict med dashboard-struktur för API:et.
        Innehåller 'blueprints' (lista) och 'summary' (aggregerad statistik).
    """
    forge_root = forge_path.parent
    forge_data = load_forge_json(forge_path)

    blueprints_raw = forge_data.get("blueprints", [])
    runs_data = forge_data.get("runs", [])

    # Nyckel: blueprint_id -> lista med (run_path, run_obj, timestamp)
    bp_runs: dict[str, list[tuple[Path, dict, datetime]]] = {}
    bp_names: dict[str, str] = {}

    # Hämta namn från blueprints-listan
    for bp in blueprints_raw:
        bp_id = str(bp.get("id", ""))
        if bp_id:
            bp_names[bp_id] = bp.get("name", "")

    # Samla in alla run-mappar
    run_paths = discover_run_paths(forge_root, runs_data)

    # Matcha runs med run-objekt från forge.json (för att få blueprint_id mm)
    run_obj_map: dict[str, dict] = {}
    for run in runs_data:
        rid = run.get("run_id")
        if rid:
            run_obj_map[str(rid)] = run

    for run_path in run_paths:
        # Extrahera run_id från mappnamnet (run_XXX -> XXX)
        run_id = run_path.name[4:]  # ta bort "run_"
        run_obj = run_obj_map.get(run_id, {})
        bp_id = get_blueprint_id(run_obj, run_path)
        ts = get_run_timestamp(run_obj, run_path)
        bp_runs.setdefault(bp_id, []).append((run_path, run_obj, ts))

    # Beräkna statistik per blueprint
    blueprints_stats = []
    total_blueprints = len(bp_runs)
    total_runs_all = 0
    total_scores_sum = 0.0
    total_fails = 0
    total_evaled_all = 0

    for bp_id, runs_list in bp_runs.items():
        stats = calculate_bp_stats(bp_id, runs_list)
        name = bp_names.get(bp_id, "")
        blueprints_stats.append({
            "id": bp_id,
            "name": name,
            "total_runs": stats["total_runs"],
            "avg_score": stats["avg_score"],
            "fail_rate": stats["fail_rate"],
            "trend": stats["trend"],
        })
        total_runs_all += stats["total_runs"]
        # För overall – använd samma aggregering som i calculate_bp_stats
        # men vi måste räkna om över alla runs
        for run_path, run_obj, ts in runs_list:
            eval_data = load_eval(run_path)
            if eval_data is not None and "score" in eval_data:
                total_scores_sum += eval_data["score"]
                total_evaled_all += 1
                if not eval_data.get("passed", True):
                    total_fails += 1

    overall_avg = total_scores_sum / total_evaled_all if total_evaled_all > 0 else 0.0
    overall_fail_rate = total_fails / total_evaled_all if total_evaled_all > 0 else 0.0

    dashboard = {
        "blueprints": blueprints_stats,
        "summary": {
            "total_blueprints": total_blueprints,
            "total_runs": total_runs_all,
            "overall_avg_score": round(overall_avg, 4),
            "overall_fail_rate": round(overall_fail_rate, 4),
        },
    }
    return dashboard


# Exempelanvändning (kommenterad)
# if __name__ == "__main__":
#     import sys
#     forge_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("forge.json")
#     data = build_dashboard(forge_path)
#     print(json.dumps(data, indent=2, ensure_ascii=False))
```