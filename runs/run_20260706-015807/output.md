```python
# main.py — FastAPI backend för Forge Command Center

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Forge Command Center API")


def get_forge_root() -> Path:
    """Returnera projektroten via miljövariabeln FORGE_ROOT, annars aktuell katalog."""
    env = os.environ.get("FORGE_ROOT")
    return Path(env).resolve() if env else Path.cwd()


def load_json(path: Path) -> Optional[dict]:
    """Läs JSON-fil, returnera None om filen saknas.”
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


# ---------- Modeller ----------

class RunEval(BaseModel):
    score: Optional[float] = None
    passed: Optional[bool] = None
    # ytterligare fält från eval.json läggs till vid behov


class Run(BaseModel):
    run_id: str
    input: Optional[dict] = None
    output: Optional[str] = None
    eval: Optional[RunEval] = None


class Blueprint(BaseModel):
    name: str
    path: str


class Stats(BaseModel):
    total_runs: int
    avg_eval_score: Optional[float] = None
    total_blueprints: int


class Status(BaseModel):
    status: str = "ok"
    timestamp: str = datetime.now(timezone.utc).isoformat()


# ---------- Datakällfunktioner ----------

def get_runs_data() -> list[Run]:
    root = get_forge_root()
    runs_dir = root / "runs"
    if not runs_dir.is_dir():
        return []

    runs = []
    for entry in sorted(runs_dir.iterdir()):
        if not entry.is_dir() or not entry.name.startswith("run_"):
            continue
        run_id = entry.name
        inp = load_json(entry / "input.json")
        out_path = entry / "output.md"
        output = out_path.read_text(encoding="utf-8") if out_path.is_file() else None
        eval_data = load_json(entry / "eval.json")
        run_eval = RunEval(**eval_data) if eval_data else None

        runs.append(Run(run_id=run_id, input=inp, output=output, eval=run_eval))
    return runs


def get_blueprints_data() -> list[Blueprint]:
    root = get_forge_root()
    blueprints_dir = root / "blueprints"
    if not blueprints_dir.is_dir():
        return []

    blueprints = []
    for entry in sorted(blueprints_dir.iterdir()):
        # acceptera alla filer och mappar
        blueprints.append(Blueprint(name=entry.name, path=str(entry.relative_to(root))))
    return blueprints


def compute_stats() -> Stats:
    runs = get_runs_data()
    scores = [r.eval.score for r in runs if r.eval and r.eval.score is not None]
    avg_score = sum(scores) / len(scores) if scores else None
    blueprints = get_blueprints_data()
    return Stats(total_runs=len(runs), avg_eval_score=avg_score, total_blueprints=len(blueprints))


# ---------- Endpoints ----------

@app.get("/api/runs", response_model=list[Run])
def api_runs():
    """Returnera alla körningar med deras indata, utdata och utvärdering."""
    return get_runs_data()


@app.get("/api/blueprints", response_model=list[Blueprint])
def api_blueprints():
    """Returnera en lista över alla blueprints i projektet."""
    return get_blueprints_data()


@app.get("/api/stats", response_model=Stats)
def api_stats():
    """Returnera aggregerad statistik om körningar och blueprints."""
    return compute_stats()


@app.get("/api/status", response_model=Status)
def api_status():
    """Returnera API-status och tidsstämpel."""
    return Status()
```

**Starta servern:**
```bash
FORGE_ROOT=/sökväg/till/forge uv run uvicorn main:app --reload
```
Utan `FORGE_ROOT` används arbetskatalogen.