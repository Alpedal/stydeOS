```python
"""
dashboard.py – Forge Command Center Dashboard Data Pipeline

Läser forge.json och alla run-mappar, beräknar statistik per blueprint och
returnerar en datastruktur redo att serveras som JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Hjälpfunktioner
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> Optional[Any]:
    """Läs JSON-fil, returnera None om filen saknas eller är korrupt."""
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _read_score(run_dir: Path) -> Optional[float]:
    """Läs score från eval.json i run-mappen. Returnera None om den saknas."""
    eval_path = run_dir / "eval.json"
    data = _read_json(eval_path)
    if data is None:
        return None
    score = data.get("score")
    if score is None or not isinstance(score, (int, float)):
        return None
    return float(score)


def _parse_run_id(run_id: str) -> int:
    """Extrahera numerisk del från run_id (t.ex. 'run_003' -> 3)."""
    parts = run_id.split("_")
    try:
        return int(parts[-1]) if len(parts) > 1 else 0
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Huvudfunktion
# ---------------------------------------------------------------------------

def build_dashboard(base_path: str | Path = ".") -> dict[str, Any]:
    """
    Bygg dashboard-data från en Forge v2-projektmapp.

    Parametrar
    ----------
    base_path : str eller Path
        Sökväg till mappen som innehåller forge.json och runs/.

    Returnerar
    -------
    dict med nycklarna:
        - blueprints : lista av dict med blueprint-statistik
        - meta       : info om datakälla och tidpunkt

    Statistik per blueprint:
        - id              : blueprint-id från forge.json
        - name            : blueprint-namn
        - total_runs      : antal runs (enligt forge.json)
        - avg_score       : medelvärde av alla scores (None om inga scores)
        - trend           : lista av scores för de senaste 5 runs (None om score saknas)
        - fail_rate       : andel runs med score < 0.5 (av de med score)
    """
    base = Path(base_path).resolve()
    forge_path = base / "forge.json"

    forge = _read_json(forge_path)
    if forge is None:
        raise FileNotFoundError(f"Saknad eller korrupt forge.json: {forge_path}")

    # Läs blueprints från forge.json
    blueprints_raw = forge.get("blueprints", [])
    runs_raw = forge.get("runs", [])

    # Skapa lookup för blueprint-namn
    bp_lookup: dict[str, str] = {}
    for bp in blueprints_raw:
        bp_id = bp.get("id")
        if bp_id:
            bp_lookup[bp_id] = bp.get("name", bp_id)

    # Gruppera runs per blueprint
    bp_runs: dict[str, list[dict]] = {}
    for run in runs_raw:
        run_id = run.get("id")
        bp_id = run.get("blueprint_id")
        if not run_id or not bp_id:
            continue

        # Hitta run-mapp
        run_dir = base / "runs" / run_id
        score = _read_score(run_dir) if run_dir.is_dir() else None

        entry = {
            "run_id": run_id,
            "score": score,
            "sort_key": _parse_run_id(run_id),
        }
        bp_runs.setdefault(bp_id, []).append(entry)

    # Bygg output för varje blueprint
    blueprints_output = []
    for bp_id, name in bp_lookup.items():
        runs = bp_runs.get(bp_id, [])
        total_runs = len(runs)

        # Sortera runs efter run_id numeriskt (äldst först)
        runs_sorted = sorted(runs, key=lambda r: r["sort_key"])

        # Scores (None om saknas)
        scores = [r["score"] for r in runs_sorted]

        # Genomsnitt
        valid_scores = [s for s in scores if s is not None]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else None

        # Trend – senaste 5 runs (senaste = högst sort_key)
        latest_5 = runs_sorted[-5:] if len(runs_sorted) >= 5 else runs_sorted
        trend = [r["score"] for r in latest_5]

        # Fail rate – andel runs med score < 0.5 av de som har en score
        if valid_scores:
            fails = sum(1 for s in valid_scores if s < 0.5)
            fail_rate = fails / len(valid_scores)
        else:
            fail_rate = 0.0

        blueprints_output.append({
            "id": bp_id,
            "name": name,
            "total_runs": total_runs,
            "avg_score": avg_score,
            "trend": trend,
            "fail_rate": round(fail_rate, 4),
        })

    # Sammanställning
    result = {
        "blueprints": blueprints_output,
        "meta": {
            "source": str(forge_path),
            "blueprint_count": len(blueprints_output),
            "total_runs": sum(bp["total_runs"] for bp in blueprints_output),
        },
    }
    return result


# ---------------------------------------------------------------------------
# CLI-test (körs direkt)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    try:
        data = build_dashboard(path)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Fel: {e}", file=sys.stderr)
        sys.exit(1)
```