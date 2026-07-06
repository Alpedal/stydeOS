# FastAPI Dashboard API Builder

Skapar en FastAPI-app som läser `forge.json`, `runs/` och `blueprints/` och servar fyra JSON-endpoints.

```python
# app.py
import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ---- Config ----
BASE_DIR = Path(__file__).resolve().parent
FORGE_JSON = BASE_DIR / "forge.json"
RUNS_DIR = BASE_DIR / "runs"
BLUEPRINTS_DIR = BASE_DIR / "blueprints"

# ---- App ----
app = FastAPI(title="Forge Command Center API", version="2.0.0")

# ---- Pydantic modeller för svar ----
class RunModel(BaseModel):
    run_id: str
    input: Optional[dict] = None
    output: Optional[str] = None
    eval: Optional[dict] = None

class BlueprintModel(BaseModel):
    name: str
    data: dict

class StatsModel(BaseModel):
    total_runs: int
    total_blueprints: int
    avg_eval_score: Optional[float] = None
    latest_run: Optional[str] = None

class StatusModel(BaseModel):
    status: str = "ok"
    version: str = "2.0.0"

# ---- Hjälpfunktioner ----
def load_json(path: Path):
    """Läs och returnera JSON från en fil, eller None om filen saknas eller är ogiltig."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

def read_text(path: Path):
    """Läs och returnera text från en fil, eller None om filen saknas."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None

def get_all_runs() -> list[RunModel]:
    """Skanna runs/run_* och returnera lista med RunModel."""
    runs = []
    if not RUNS_DIR.exists():
        return runs

    for run_dir in sorted(RUNS_DIR.iterdir()):
        if not run_dir.is_dir():
            continue
        run_id = run_dir.name

        input_data = load_json(run_dir / "input.json")
        output_text = read_text(run_dir / "output.md")
        eval_data = load_json(run_dir / "eval.json")

        runs.append(RunModel(
            run_id=run_id,
            input=input_data,
            output=output_text,
            eval=eval_data
        ))
    return runs

def get_all_blueprints() -> list[BlueprintModel]:
    """Skanna blueprints/ och returnera lista med BlueprintModel."""
    blueprints = []
    if not BLUEPRINTS_DIR.exists():
        return blueprints

    for file in sorted(BLUEPRINTS_DIR.iterdir()):
        if file.suffix.lower() in (".json", ".yaml", ".yml"):
            data = load_json(file)
            if data is not None:
                blueprints.append(BlueprintModel(name=file.stem, data=data))
    return blueprints

def compute_stats(runs: list[RunModel]) -> StatsModel:
    """Beräkna statistik över runs."""
    total = len(runs)
    total_blue = len(get_all_blueprints())

    scores = []
    for run in runs:
        if run.eval and isinstance(run.eval, dict):
            # Anta att det finns en key 'score' eller 'accuracy'
            sc = run.eval.get("score") or run.eval.get("accuracy")
            if sc is not None and isinstance(sc, (int, float)):
                scores.append(sc)

    avg = round(sum(scores) / len(scores), 2) if scores else None
    latest = runs[-1].run_id if runs else None

    return StatsModel(
        total_runs=total,
        total_blueprints=total_blue,
        avg_eval_score=avg,
        latest_run=latest
    )

# ---- Endpoints ----
@app.get("/api/runs", response_model=list[RunModel])
async def get_runs():
    """Returnera alla runs med input, output och eval."""
    return get_all_runs()

@app.get("/api/blueprints", response_model=list[BlueprintModel])
async def get_blueprints():
    """Returnera alla blueprints som JSON-objekt."""
    return get_all_blueprints()

@app.get("/api/stats", response_model=StatsModel)
async def get_stats():
    """Returnera sammanställd statistik över runs och blueprints."""
    runs = get_all_runs()
    return compute_stats(runs)

@app.get("/api/status", response_model=StatusModel)
async def get_status():
    """Returnera enkel serverstatus."""
    return StatusModel()
```

## Förklaring av endpoints

- **`/api/runs`** – läser alla `runs/run_*/`-mappar och returnerar varje runs `input.json`, `output.md` och `eval.json`. Hanterar saknade filer graciöst.
- **`/api/blueprints`** – läser alla `.json`-filer i `blueprints/` och returnerar deras innehåll med filnamn som ID.
- **`/api/stats`** – beräknar antal runs, antal blueprints, genomsnittligt eval-score (om fältet `score` eller `accuracy` finns) och senaste run-id.
- **`/api/status`** – returnerar `{"status":"ok","version":"2.0.0"}` för hälsoövervakning.

## Starta servern

```bash
pip install fastapi uvicorn
uvicorn app:app --reload --port 8000
```

Alla endpoints returnerar JSON med korrekta Pydantic-modeller. Inga hårdkodade sökvägar – allt styrs via `BASE_DIR` och förväntad mappstruktur.