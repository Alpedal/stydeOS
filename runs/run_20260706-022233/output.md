```python
"""
datapipeline.py

Läser forge.json och tillhörande run-mappar från en Forge v2-struktur,
beräknar statistik per blueprint (snitt-score, trend, fail rate) och
returnerar en JSON-vänlig datamodell för API:et.

Alla filer läses från disk – ingen cachning.
Saknade filer hanteras med None, inte undantag.
Endast stdlib: json, pathlib, datetime.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

# Standardgräns för vad som räknas som "fail"
FAIL_THRESHOLD = 0.5


# ---------------------------------------------------------------------------
# Hjälpfunktioner
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> Optional[dict]:
    """Läs en JSON-fil. Returnera dict eller None om filen saknas."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _read_text(path: Path) -> Optional[str]:
    """Läs en textfil. Returnera str eller None om filen saknas."""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return None


def _load_run_input(run_path: Path) -> dict:
    """Läs input.json från en run‑mapp. Returnera tom dict om filen saknas."""
    data = _read_json(run_path / "input.json")
    return data if isinstance(data, dict) else {}


def _load_run_eval(run_path: Path) -> Optional[dict]:
    """Läs eval.json – returnera dict eller None."""
    return _read_json(run_path / "eval.json")


def _determine_fail(eval_data: Optional[dict]) -> Optional[bool]:
    """
    Avgör om en run har failat baserat på eval.json.

    Prioriteringsordning:
      1. 'passed' (bool) – om finns
      2. 'score' (float) – jämför med FAIL_THRESHOLD
      3. Inget data → None
    """
    if eval_data is None:
        return None

    passed = eval_data.get("passed")
    if passed is not None:
        return not bool(passed)          # True → fail

    score = eval_data.get("score")
    if score is not None:
        return score < FAIL_THRESHOLD

    return None


# ---------------------------------------------------------------------------
# Huvudfunktion
# ---------------------------------------------------------------------------

def build_dashboard_data(root_path: str) -> Dict[str, Any]:
    """
    Bygg dashboard‑data från en Forge v2‑rotkatalog.

    Förväntad struktur:
      {root_path}/
          forge.json               – blueprint- och run‑lista
          runs/
              run_YYYYMMDD_HHMM/   – per run‑mapp
                  input.json
                  output.md
                  eval.json
                  feedback.md

    Returnerar en dict med nycklarna:
      - "blueprints": lista per blueprint med statistik
      - "summary": aggregerad statistik över alla blueprints
    """
    root = Path(root_path).resolve()
    forge_path = root / "forge.json"
    forge_data = _read_json(forge_path)

    if forge_data is None:
        return {"error": f"forge.json saknas i {root_path}"}

    # Hämta alla blueprints och run‑ID:n från forge.json
    blueprints: List[dict] = forge_data.get("blueprints", [])
    run_ids: List[str] = forge_data.get("runs", [])

    # Skapa uppslag blueprint_id → blueprint_info
    blueprint_map = {bp["id"]: bp for bp in blueprints}

    # Gruppera run‑data per blueprint
    runs_by_blueprint: Dict[str, list] = {bp["id"]: [] for bp in blueprints}

    for rid in run_ids:
        run_path = root / "runs" / rid
        if not run_path.is_dir():
            continue

        input_data = _load_run_input(run_path)
        eval_data = _load_run_eval(run_path)

        # Hämta blueprint_id från input (antar att input.json har "blueprint_id")
        bp_id = input_data.get("blueprint_id", "")

        # Om blueprint_id saknas hoppar vi över run (den kan inte knytas till blueprint)
        if bp_id not in blueprint_map:
            continue

        # Hämta score ur eval
        score = None
        if eval_data is not None:
            score = eval_data.get("score")

        fail = _determine_fail(eval_data)

        # Bygg run‑objekt med nödvändig info för statistiken
        run_info = {
            "run_id": rid,
            "input": input_data,
            "output": _read_text(run_path / "output.md"),
            "eval": eval_data,
            "feedback": _read_text(run_path / "feedback.md"),
            "score": score,
            "fail": fail,
        }
        runs_by_blueprint[bp_id].append(run_info)

    # Beräkna statistik per blueprint
    blueprint_stats = []
    total_runs = 0
    all_scores = []

    for bp in blueprints:
        bp_id = bp["id"]
        runs = runs_by_blueprint.get(bp_id, [])

        # Sortera runs efter run_id (lexikografiskt – fungerar för tidsstämplar)
        runs.sort(key=lambda r: r["run_id"])

        # Antal runs
        count = len(runs)

        # Scores (non‑None)
        scores = [r["score"] for r in runs if r["score"] is not None]
        avg_score = (sum(scores) / len(scores)) if scores else None

        # Trend – de 5 senaste run:ens scores (None om score saknas)
        trend = [r["score"] for r in runs[-5:]]

        # Fail rate – endast runs där fail kunde bestämmas
        fails = [r["fail"] for r in runs if r["fail"] is not None]
        fail_count = sum(fails) if fails else 0
        fail_rate = (fail_count / len(fails)) if fails else None

        bp_stat = {
            "id": bp_id,
            "name": bp.get("name", bp_id),
            "runs_count": count,
            "average_score": avg_score,
            "trend": trend,
            "fail_rate": fail_rate,
            "runs": runs,     # fullständig run‑information
        }
        blueprint_stats.append(bp_stat)

        total_runs += count
        all_scores.extend(scores)

    # Aggregerad statistik
    overall_avg = (sum(all_scores) / len(all_scores)) if all_scores else None

    all_fails = [r["fail"] for bp in blueprint_stats for r in bp["runs"] if r["fail"] is not None]
    overall_fail_count = sum(all_fails)
    overall_fail_rate = (overall_fail_count / len(all_fails)) if all_fails else None

    summary = {
        "total_blueprints": len(blueprints),
        "total_runs": total_runs,
        "overall_average_score": overall_avg,
        "overall_fail_rate": overall_fail_rate,
    }

    return {
        "blueprints": blueprint_stats,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Exempelanvändning
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Test med en sökväg – anpassa efter dina behov
    data = build_dashboard_data(".")
    print(json.dumps(data, indent=2, ensure_ascii=False))
```