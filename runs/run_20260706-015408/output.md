## Filstruktur

```
app/
├── config.py      # Läs miljövariabel FORGE_ROOT
├── models.py      # Pydantic-modeller
├── services.py    # Dataladdning från disk
└── main.py        # FastAPI-applikation + endpoints
```

---

## config.py

```python
from pathlib import Path
import os

class Settings:
    """Läs FORGE_ROOT från miljövariabel, default till aktuell katalog."""
    forge_root: Path = Path(os.getenv("FORGE_ROOT", "."))

    @property
    def forge_json_path(self) -> Path:
        return self.forge_root / "forge.json"

    @property
    def runs_dir(self) -> Path:
        return self.forge_root / "runs"

    @property
    def blueprints_dir(self) -> Path:
        return self.forge_root / "blueprints"

settings = Settings()
```

---

## models.py

```python
from pydantic import BaseModel
from typing import Any, Optional

class Run(BaseModel):
    id: str
    input: Optional[dict] = None
    output: Optional[str] = None
    eval: Optional[dict] = None

class Blueprint(BaseModel):
    name: str
    path: str
    config: Optional[dict] = None

class Stats(BaseModel):
    total_runs: int
    completed: int
    failed: int
    unknown: int
    total_blueprints: int

class StatusResponse(BaseModel):
    status: str = "ok"
    forge_version: Optional[str] = None
    runs_count: int
    blueprints_count: int
```

---

## services.py

```python
import json
from pathlib import Path
from typing import List
from config import settings
from models import Run, Blueprint

def load_forge_json() -> dict:
    """Läs forge.json och returnera som dict."""
    path = settings.forge_json_path
    if not path.exists():
        return {"runs": [], "blueprints": [], "version": None}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_run(run_id: str) -> Run:
    """Läs en run-mapp och returnera Run-objekt."""
    run_dir = settings.runs_dir / run_id
    run = Run(id=run_id)

    input_path = run_dir / "input.json"
    if input_path.exists():
        with open(input_path, "r", encoding="utf-8") as f:
            run.input = json.load(f)

    output_path = run_dir / "output.md"
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            run.output = f.read()

    eval_path = run_dir / "eval.json"
    if eval_path.exists():
        with open(eval_path, "r", encoding="utf-8") as f:
            run.eval = json.load(f)

    return run

def load_all_runs() -> List[Run]:
    """Hämta lista med runs från forge.json och läs varje run."""
    forge_data = load_forge_json()
    run_ids = forge_data.get("runs", [])
    # Fallback: scanna runs-katalogen om forge.json inte har lista
    if not run_ids and settings.runs_dir.exists():
        run_ids = sorted([d.name for d in settings.runs_dir.iterdir() if d.is_dir()])
    runs = [load_run(rid) for rid in run_ids]
    return runs

def load_all_blueprints() -> List[Blueprint]:
    """Hämta lista med blueprints från forge.json och ev. config från disk."""
    forge_data = load_forge_json()
    blueprint_names = forge_data.get("blueprints", [])
    blueprints = []
    for name in blueprint_names:
        bp_path = settings.blueprints_dir / name
        config = None
        if bp_path.exists() and (bp_path / "blueprint.json").exists():
            with open(bp_path / "blueprint.json", "r") as f:
                config = json.load(f)
        blueprints.append(Blueprint(name=name, path=str(bp_path), config=config))
    return blueprints
```

---

## main.py

```python
from fastapi import FastAPI
from models import Run, Blueprint, Stats, StatusResponse
from services import load_all_runs, load_all_blueprints, load_forge_json
from config import settings

app = FastAPI(title="Forge Command Center API", version="1.0.0")

@app.get("/api/runs", response_model=list[Run])
async def get_runs():
    """Returnera alla runs med input, output och eval-data."""
    return load_all_runs()

@app.get("/api/blueprints", response_model=list[Blueprint])
async def get_blueprints():
    """Returnera alla blueprints från forge.json och eventuell config."""
    return load_all_blueprints()

@app.get("/api/stats", response_model=Stats)
async def get_stats():
    """Aggregera statistik över runs (status från eval.json)."""
    runs = load_all_runs()
    total = len(runs)
    completed = sum(1 for r in runs if r.eval and r.eval.get("status") == "completed")
    failed = sum(1 for r in runs if r.eval and r.eval.get("status") == "failed")
    unknown = total - completed - failed
    blueprints = load_all_blueprints()
    return Stats(
        total_runs=total,
        completed=completed,
        failed=failed,
        unknown=unknown,
        total_blueprints=len(blueprints)
    )

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Hälsokontroll – returnerar API-status och räknevariabler."""
    forge_data = load_forge_json()
    runs = load_all_runs()
    blueprints = load_all_blueprints()
    return StatusResponse(
        forge_version=forge_data.get("version"),
        runs_count=len(runs),
        blueprints_count=len(blueprints)
    )
```

---

## Starta API:et

```bash
# Sätt FORGE_ROOT om din forge-mapp inte är aktuell katalog
export FORGE_ROOT=/path/to/forge
uvicorn app.main:app --reload --port 8080
```

Alla endpoints returnerar ren JSON. Inga hårdkodade sökvägar – rotkatalogen styrs av miljövariabeln `FORGE_ROOT`. Vid saknad `forge.json` returneras tomma listor och `version: null`.