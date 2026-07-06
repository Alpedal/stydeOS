```python
"""
dashboard.py - Datapipeline för Forge Command Center.

Läser forge.json och alla run-mappar, beräknar statistik (snitt-score, trend,
fail rate) och returnerar en JSON-struktur för API:et.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Hjälpfunktioner
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> Optional[Any]:
    """Läs JSON-fil. Returnera None om fil saknas eller är ogiltig."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        return None


def _read_text(path: Path) -> Optional[str]:
    """Läs textfil. Returnera None om fil saknas."""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError):
        return None


def _extract_run_number(run_dir: Path) -> int:
    """Extrahera numeriskt ID från mappnamn som 'run_3'."""
    match = re.search(r"(\d+)$", run_dir.name)
    return int(match.group(1)) if match else 0


# ---------------------------------------------------------------------------
# Ladda data
# ---------------------------------------------------------------------------

def load_forge_config(config_path: Path) -> dict[str, Any]:
    """Läs forge.json och returnera dess innehåll.

    Raises:
        FileNotFoundError: Om forge.json saknas.
        json.JSONDecodeError: Om forge.json har ogiltig JSON.
    """
    data = _read_json(config_path)
    if data is None:
        raise FileNotFoundError(f"forge.json hittades inte eller är ogiltig: {config_path}")
    return data


def load_run_data(run_dir: Path) -> dict[str, Any]:
    """Läs alla relevanta filer i en run-mapp.

    Returnerar dict med nycklar: input, output, eval, feedback.
    Saknade filer ger None.
    """
    return {
        "input": _read_json(run_dir / "input.json"),
        "output": _read_text(run_dir / "output.md"),
        "eval": _read_json(run_dir / "eval.json"),
        "feedback": _read_text(run_dir / "feedback.md"),
    }


# ---------------------------------------------------------------------------
# Statistikberäkning
# ---------------------------------------------------------------------------

def compute_blueprint_stats(
    blueprint_name: str,
    runs_data: list[tuple[str, dict[str, Any]]],
    fail_threshold: float = 0.5,
) -> dict[str, Any]:
    """Beräkna statistik för en blueprint givet en lista av (run_id, data).

    runs_data förväntas vara sorterad i kronologisk ordning (stigande run-nummer).
    fail_threshold: score under detta värde (eller None) räknas som fail.
    """
    scores: list[Optional[float]] = []
    run_details: list[dict[str, Any]] = []

    for run_id, data in runs_data:
        eval_data = data.get("eval")
        score: Optional[float] = None
        if eval_data is not None and isinstance(eval_data, dict):
            score = eval_data.get("score", None)
        scores.append(score)

        output_text = data.get("output")
        feedback_text = data.get("feedback")

        run_details.append({
            "run_id": run_id,
            "score": score,
            "has_output": output_text is not None,
            "feedback": feedback_text[:200] if feedback_text else None,
        })

    total = len(scores)
    valid_scores = [s for s in scores if s is not None]
    average_score = round(sum(valid_scores) / len(valid_scores), 4) if valid_scores else None

    # Fail count: None or score < threshold
    fail_count = sum(1 for s in scores if s is None or s < fail_threshold)
    fail_rate = round(fail_count / total, 4) if total > 0 else 0.0

    # Trend: scores för de senaste 5 runs (None blir null i JSON)
    trend = scores[-5:] if len(scores) >= 5 else scores[:]

    return {
        "name": blueprint_name,
        "runs_count": total,
        "average_score": average_score,
        "fail_rate": fail_rate,
        "trend": trend,
        "runs": run_details,
    }


# ---------------------------------------------------------------------------
# Huvudfunktion
# ---------------------------------------------------------------------------

def build_dashboard(config_path: Path, fail_threshold: float = 0.5) -> dict[str, Any]:
    """Bygg dashboard-objekt från forge.json och run-data.

    Args:
        config_path: Sökväg till forge.json.
        fail_threshold: Gräns under vilken score räknas som fail (default 0.5).

    Returns:
        Dict med nycklar:
            - generated_at: ISO 8601-tidstämpel
            - blueprints: lista av blueprint-statistik
    """
    config = load_forge_config(config_path)
    runs_config = config.get("runs", [])
    blueprints_config = config.get("blueprints", [])

    # Mappa blueprints efter namn
    blueprint_map = {bp["name"]: bp for bp in blueprints_config}

    # Lista alla run-mappar
    run_dirs: list[Path] = []
    base_dir = config_path.parent
    for entry in runs_config:
        run_path = base_dir / entry["dir"]
        if run_path.is_dir():
            run_dirs.append(run_path)

    # Sortera efter run-nummer
    run_dirs.sort(key=_extract_run_number)

    # Ladda alla runs och gruppera per blueprint
    runs_by_blueprint: dict[str, list[tuple[str, dict[str, Any]]]] = {}

    for run_dir in run_dirs:
        run_id = run_dir.name
        data = load_run_data(run_dir)
        # Avgör blueprint från input.json eller från forge.json? Använd input.json blueprint-fält
        input_data = data.get("input")
        if isinstance(input_data, dict):
            bp_name = input_data.get("blueprint")
        else:
            bp_name = None
        if bp_name is None:
            # Fallback: första blueprint om input saknas
            bp_name = blueprints_config[0]["name"] if blueprints_config else "unknown"
        runs_by_blueprint.setdefault(bp_name, []).append((run_id, data))

    # Beräkna statistik per blueprint
    blueprints_stats = []
    for bp_name, runs_list in runs_by_blueprint.items():
        stats = compute_blueprint_stats(bp_name, runs_list, fail_threshold)
        blueprints_stats.append(stats)

    # Sortera blueprints efter namn för konsekvens
    blueprints_stats.sort(key=lambda x: x["name"])

    dashboard = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "blueprints": blueprints_stats,
    }

    return dashboard


# ---------------------------------------------------------------------------
# Exempelanvändning (om modulen körs direkt)
# ---------------------------------------------------------------------------

def main() -> None:
    """Demo: skriv ut dashboard som JSON."""
    import sys

    if len(sys.argv) < 2:
        config_path = Path("forge.json")
    else:
        config_path = Path(sys.argv[1])

    if not config_path.exists():
        print(f"Ange sökväg till forge.json (nuvarande: {config_path})", file=sys.stderr)
        sys.exit(1)

    try:
        dashboard = build_dashboard(config_path)
        print(json.dumps(dashboard, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Fel: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```