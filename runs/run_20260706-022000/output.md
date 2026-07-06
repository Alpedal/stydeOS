```python
"""
Datapipeline för Forge Command Center.
Läser forge.json och run-mappar, beräknar statistik och returnerar som JSON-struktur för API:et.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

# --- Hjälpfunktioner ---

def _load_json(filepath: Path) -> Optional[dict]:
    """Läs och returnera JSON-data från en fil, eller None vid fel."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        return None

def _extract_run_number(run_dir_name: str) -> int:
    """Extrahera numeriskt run-id från mappnamn som 'run_1'."""
    match = re.search(r'run_(\d+)', run_dir_name)
    return int(match.group(1)) if match else 0

def _read_run_data(base_path: Path, run_dir_name: str) -> dict:
    """Läs data från en run-mapp och returnera en dictionary med relevant info."""
    run_path = base_path / 'runs' / run_dir_name
    run_number = _extract_run_number(run_dir_name)

    eval_data = _load_json(run_path / 'eval.json')
    score = eval_data.get('score') if eval_data else None  # score None om eval.json saknas eller har fel

    # Feedback och output läses inte för statistik, men kan användas framöver
    return {
        'run_id': run_number,
        'dir': run_dir_name,
        'score': score,
        'eval_present': eval_data is not None
    }

def _compute_trend(scores: list) -> list:
    """Returnera de senaste 5 score-värdena (senaste sist)."""
    # scores förväntas vara i kronologisk ordning (äldst först)
    # trend = senaste 5 (nyast sist)
    valid_scores = [s for s in scores if s is not None]
    return valid_scores[-5:] if len(valid_scores) >= 5 else valid_scores

def _average(values: list) -> Optional[float]:
    """Beräkna medelvärde för en lista med tal, None om tom."""
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return sum(clean) / len(clean)

# --- Huvudfunktioner ---

def load_forge_config(base_path: Path) -> dict:
    """Läs forge.json från basmappen."""
    config = _load_json(base_path / 'forge.json')
    if config is None:
        raise FileNotFoundError(f"forge.json saknas eller är ogiltig i {base_path}")
    return config

def collect_runs(base_path: Path) -> list[dict]:
    """Samla alla run-mappar, sorterade efter run-nummer."""
    runs_dir = base_path / 'runs'
    if not runs_dir.is_dir():
        return []

    run_dirs = sorted(
        [d.name for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith('run_')],
        key=_extract_run_number
    )

    runs = []
    for dir_name in run_dirs:
        run_data = _read_run_data(base_path, dir_name)
        runs.append(run_data)
    return runs

def compute_blueprint_stats(blueprint: dict, runs: list[dict]) -> dict:
    """
    Beräkna statistik för en specifik blueprint.
    blueprint: dict från forge.json blueprints-listan (minst 'id' och 'name').
    runs: lista med run-data (inkl. score) som tillhör denna blueprint.
    """
    bp_id = blueprint.get('id', 'unknown')
    bp_name = blueprint.get('name', 'Unknown')

    scores = [r['score'] for r in runs]
    total_runs = len(runs)

    # Average score (ignorera None)
    avg_score = _average(scores)

    # Trend: senaste 5 scores baserat på run-ordning (äldst först i listan)
    # Listan är redan sorterad på run_id (från collect_runs)
    trend = _compute_trend(scores)

    # Fail rate: andel runs där score < 0.5 eller saknas
    # Definition: fail om score är None eller < 0.5
    fails = sum(1 for s in scores if s is None or s < 0.5)
    fail_rate = fails / total_runs if total_runs > 0 else 0.0

    return {
        'id': bp_id,
        'name': bp_name,
        'total_runs': total_runs,
        'average_score': avg_score,
        'trend': trend,
        'fail_rate': round(fail_rate, 4)
    }

def generate_dashboard(base_path: str = '.') -> dict:
    """
    Huvudfunktion: läs forge.json, samla runs, beräkna statistik per blueprint
    och övergripande, returnera som dict (kan serialiseras till JSON).
    """
    bp = Path(base_path).resolve()
    config = load_forge_config(bp)

    # Hämta blueprints-listan från config
    blueprints_config = config.get('blueprints', [])
    # Hämta runs-listan (run_id) från config om den finns, men vi läser från disk ändå
    # Använd bara config-run för att matcha mot mappar? Nej, vi läser diskens run-mappar direkt.
    # Men vi behöver veta vilka runs som tillhör vilken blueprint.
    # Forge.json har 'runs' array med run_id (t.ex. "run_1").
    # Vi kan använda den för att hitta blueprint_id för varje run genom att matcha.
    # Men vi har redan läst runs från disk. Vi måste koppla dem till blueprint via config.
    # Antag: varje run i config.runs har fält som 'run_id' och 'blueprint_id'.
    # Om inte, anta att run_id är "run_1" och blueprint_id finns i input.json? För enkelhet,
    # vi använder config.runs för att matcha run_id med blueprint_id.
    # Detta är robustare.

    # Samla runs från disk
    disk_runs = collect_runs(bp)

    # Skapa en mapping run_id -> blueprint_id från config.runs
    config_runs = config.get('runs', [])
    run_to_bp = {}
    for cr in config_runs:
        rid = cr.get('run_id')
        bid = cr.get('blueprint_id')
        if rid and bid:
            run_to_bp[rid] = bid

    # Gruppera runs per blueprint
    bp_runs: dict[str, list[dict]] = {}  # blueprint_id -> lista med run-data
    for run_data in disk_runs:
        dir_name = run_data['dir']  # t.ex. "run_1"
        bp_id = run_to_bp.get(dir_name, 'orphan')  # om inte finns, lägg som 'orphan'
        bp_runs.setdefault(bp_id, []).append(run_data)

    # Bygg statistik för varje blueprint i config
    blueprints_stats = []
    for bp_cfg in blueprints_config:
        bid = bp_cfg.get('id', 'unknown')
        runs_for_bp = bp_runs.pop(bid, [])  # ta bort från gruppen när vi använder den
        stats = compute_blueprint_stats(bp_cfg, runs_for_bp)
        blueprints_stats.append(stats)

    # Hantera eventuella kvarvarande runs (orphan eller blueprints som saknas i config)
    for bid, runs_list in bp_runs.items():
        # Skapa en dummy blueprint för orphan eller okända
        dummy_bp = {'id': bid, 'name': f'Unknown ({bid})'}
        stats = compute_blueprint_stats(dummy_bp, runs_list)
        blueprints_stats.append(stats)

    # Sortera blueprints efter id för konsekvent output
    blueprints_stats.sort(key=lambda x: x['id'])

    # Övergripande statistik
    all_scores = []
    total_fails = 0
    total_runs_all = 0
    for bp_stat in blueprints_stats:
        total_runs_all += bp_stat['total_runs']
        # Räkna fails från fail_rate (approximativt, men exaktare: samla alla scores)
        # Bättre: gå tillbaka till disk runs. Men vi har redan fail_rate per blueprint.
        # För overall fail_rate, samla från disk runs direkt.
    # Använd disk_runs för overall
    all_scores = [r['score'] for r in disk_runs]
    total_runs_all = len(all_scores)
    avg_all = _average(all_scores)
    fails_all = sum(1 for s in all_scores if s is None or s < 0.5)
    fail_rate_all = fails_all / total_runs_all if total_runs_all > 0 else 0.0

    overall = {
        'total_blueprints': len(blueprints_stats),
        'total_runs': total_runs_all,
        'average_score': avg_all,
        'fail_rate': round(fail_rate_all, 4)
    }

    return {
        'blueprints': blueprints_stats,
        'overall': overall
    }


# --- Exempel på anrop (om kört som skript) ---
if __name__ == '__main__':
    import sys
    base = sys.argv[1] if len(sys.argv) > 1 else '.'
    try:
        dashboard = generate_dashboard(base)
        print(json.dumps(dashboard, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Fel: {e}", file=sys.stderr)
        sys.exit(1)
```