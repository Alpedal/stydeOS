Här är en komplett FastAPI-applikation som läser `forge.json`, alla run-mappar och blueprints, och servar de fyra efterfrågade endpoints:

```python
# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json
from typing import Optional

app = FastAPI(title="Forge Command Center API", version="1.0.0")

# ——— Konfiguration ———
FORGE_ROOT = Path(".")               # Ändra via miljövariabel om så önskas
FORGE_FILE = FORGE_ROOT / "forge.json"
RUNS_DIR    = FORGE_ROOT / "runs"
BLUEPRINTS_DIR = FORGE_ROOT / "blueprints"

# ——— Hjälpfunktioner ———
def load_json(path: Path) -> Optional[dict]:
    """Läs och returnera JSON från en fil, eller None vid fel."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def read_run(run_dir: Path) -> dict:
    """Läs en run-mapp och returnera dess data."""
    input_data  = load_json(run_dir / "input.json") or {}
    eval_data   = load_json(run_dir / "eval.json") or {}
    output_file = run_dir / "output.md"
    output_text = output_file.read_text(encoding="utf-8") if output_file.exists() else None

    return {
        "run_id": run_dir.name,
        "input": input_data,
        "output_md": output_text,
        "eval": eval_data
    }

# ——— Endpoints ———

@app.get("/api/runs")
def get_runs():
    """Returnera lista över alla runs med innehåll."""
    if not RUNS_DIR.exists():
        return []
    runs = []
    for run_dir in sorted(RUNS_DIR.iterdir()):
        if run_dir.is_dir() and run_dir.name.startswith("run_"):
            runs.append(read_run(run_dir))
    return runs

@app.get("/api/blueprints")
def get_blueprints():
    """Returnera lista över alla blueprints (JSON-filer i blueprints/)."""
    if not BLUEPRINTS_DIR.exists():
        return []
    blueprints = []
    for file in sorted(BLUEPRINTS_DIR.iterdir()):
        if file.suffix == ".json":
            data = load_json(file)
            if data is not None:
                data["name"] = file.stem
                blueprints.append(data)
    return blueprints

@app.get("/api/stats")
def get_stats():
    """Returnera aggregerad statistik: antal runs, genomsnittlig score, etc."""
    runs = []
    if RUNS_DIR.exists():
        runs = [read_run(r) for r in sorted(RUNS_DIR.iterdir())
                if r.is_dir() and r.name.startswith("run_")]

    total_runs = len(runs)
    eval_scores = []
    for run in runs:
        score = run["eval"].get("score")
        if score is not None:
            eval_scores.append(score)

    avg_score = sum(eval_scores) / len(eval_scores) if eval_scores else None
    return {
        "total_runs": total_runs,
        "runs_with_eval": len(eval_scores),
        "average_score": avg_score
    }

@app.get("/api/status")
def get_status():
    """Enkel hälso/kontroll-endpoint."""
    forge_exists = FORGE_FILE.exists()
    runs_exist   = RUNS_DIR.exists() and any(RUNS_DIR.iterdir())
    return {
        "status": "ok",
        "forge_file_exists": forge_exists,
        "runs_directory_exists": runs_exist,
        "version": "1.0.0"
    }
```

**Förklaring per endpoint:**

- **`/api/runs`** – läser alla mappar som börjar med `run_` under `runs/`, plockar upp `input.json`, `output.md` och `eval.json` och returnerar en lista med samlad data. Saknade filer hanteras med tomma dicts eller `None`.
- **`/api/blueprints`** – skannar `blueprints/` efter `.json`-filer, laddar varje och lägger till `name` (filnamnet utan extension). Returnerar en lista.
- **`/api/stats`** – räknar totalt antal runs, antal runs som har ett `score`-fält i `eval.json`, och räknar ut medelvärdet.
- **`/api/status`** – enkel hälsokontroll som talar om ifall `forge.json` och `runs/` finns.

All inputvalidering sker via `load_json` som fångar både saknade filer och trasig JSON. Svaren är alltid JSON.