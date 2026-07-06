```python
import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Konfiguration – använd miljövariabel FORGE_ROOT, annars aktuell katalog
# ---------------------------------------------------------------------------
FORGE_ROOT = os.getenv("FORGE_ROOT", os.getcwd())
FORGE_PATH = Path(FORGE_ROOT)
RUNS_DIR = FORGE_PATH / "runs"
FORGE_JSON = FORGE_PATH / "forge.json"

# ---------------------------------------------------------------------------
# Pydantic-modeller – så specifik som möjligt, men äger fälten som dict/accepterar allt
# ---------------------------------------------------------------------------
class RunInput(BaseModel):
    """Innehållet i input.json – kan utökas vid behov."""
    prompt: Optional[str] = None
    extra: Optional[dict] = None

    class Config:
        extra = "allow"  # accepterar okända fält

class RunEval(BaseModel):
    """Innehållet i eval.json."""
    score: Optional[float] = None
    passed: Optional[bool] = None
    extra: Optional[dict] = None

    class Config:
        extra = "allow"

class Run(BaseModel):
    """En fullständig run, sammansatt av filerna i run-mappen."""
    id: str
    input: Optional[RunInput] = None
    output: Optional[str] = None          # output.md som ren text
    eval: Optional[RunEval] = None

class Blueprint(BaseModel):
    """Blueprint från forge.json – anpassa efter verklig struktur."""
    id: str
    name: Optional[str] = None
    version: Optional[str] = None
    extra: Optional[dict] = None

    class Config:
        extra = "allow"

class Stats(BaseModel):
    """Aggregerad statistik över runs och blueprints."""
    total_runs: int
    total_blueprints: int
    run_status_counts: dict[str, int]     # t.ex. {"passed": 5, "failed": 2}
    blueprint_names: list[str]

class Health(BaseModel):
    """Enkel status över att nödvändiga filer finns."""
    forge_json_exists: bool
    runs_dir_exists: bool
    run_count: int

# ---------------------------------------------------------------------------
# Hjälpfunktioner – läser filer och hanterar fel
# ---------------------------------------------------------------------------
def safe_read_json(path: Path) -> Optional[dict]:
    """Läs JSON-fil, returnera None om den saknas eller är ogiltig."""
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

def safe_read_text(path: Path) -> Optional[str]:
    """Läs textfil (output.md), returnera None om den saknas."""
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None

def discover_runs() -> list[Run]:
    """Skanna runs/run_* och bygg Run-objekt."""
    if not RUNS_DIR.is_dir():
        return []
    runs: list[Run] = []
    for entry in sorted(RUNS_DIR.iterdir()):
        if not entry.is_dir() or not entry.name.startswith("run_"):
            continue
        run_id = entry.name
        run_input = safe_read_json(entry / "input.json")
        run_output = safe_read_text(entry / "output.md")
        run_eval = safe_read_json(entry / "eval.json")
        runs.append(
            Run(
                id=run_id,
                input=RunInput(**run_input) if run_input else None,
                output=run_output,
                eval=RunEval(**run_eval) if run_eval else None,
            )
        )
    return runs

def load_blueprints() -> list[Blueprint]:
    """Läs blueprints från forge.json."""
    data = safe_read_json(FORGE_JSON)
    if data is None:
        return []
    bp_list = data.get("blueprints", [])
    return [Blueprint(**bp) for bp in bp_list]

def compute_stats() -> Stats:
    """Beräkna statistik baserat på nuvarande data."""
    runs = discover_runs()
    bps = load_blueprints()
    # statusfördelning – antag att eval.json innehåller 'passed'
    status_counts: dict[str, int] = {}
    for run in runs:
        if run.eval and run.eval.passed is not None:
            key = "passed" if run.eval.passed else "failed"
        else:
            key = "unknown"
        status_counts[key] = status_counts.get(key, 0) + 1
    return Stats(
        total_runs=len(runs),
        total_blueprints=len(bps),
        run_status_counts=status_counts,
        blueprint_names=[bp.name or bp.id for bp in bps],
    )

# ---------------------------------------------------------------------------
# FastAPI-applikation med endpoints
# ---------------------------------------------------------------------------
app = FastAPI(title="Forge Command Center API", version="1.0.0")

@app.get("/api/runs", response_model=list[Run])
def get_runs():
    """Returnera alla runs sorterade efter mappnamn."""
    return discover_runs()

@app.get("/api/blueprints", response_model=list[Blueprint])
def get_blueprints():
    """Returnera alla blueprints från forge.json."""
    bps = load_blueprints()
    if not bps:
        # Om forge.json saknas, returnera tom lista (inga fel)
        pass
    return bps

@app.get("/api/stats", response_model=Stats)
def get_stats():
    """Returnera aggregerad statistik över runs och blueprints."""
    return compute_stats()

@app.get("/api/status", response_model=Health)
def get_status():
    """Hälsokontroll – kolla att forge.json och runs-katalogen finns."""
    runs = discover_runs()
    return Health(
        forge_json_exists=FORGE_JSON.is_file(),
        runs_dir_exists=RUNS_DIR.is_dir(),
        run_count=len(runs),
    )

# ---------------------------------------------------------------------------
# Starta direkt om scriptet körs
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```