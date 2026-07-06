```python
# main.py — FastAPI-backend for Forge Command Center
# Läs miljövariabel FORGE_ROOT (default "."), alla sökvägar relativt till detta.
# Endpoints:
#   /api/runs       → lista alla run-mappar med innehåll
#   /api/blueprints → lista blueprint-filer (JSON) från blueprints/
#   /api/stats      → aggregerad statistik från runs
#   /api/status     → API-hälsokontroll

import os
import json
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# ---------- Konfiguration ----------
FORGE_ROOT = os.environ.get("FORGE_ROOT", ".")

# ---------- Pydantic-modeller ----------
class RunEval(BaseModel):
    """Utvärderingsdata för en run."""
    passed: bool
    score: Optional[float] = None
    feedback: Optional[str] = None

class Run(BaseModel):
    """En run med input, output och eval."""
    id: str
    blueprint: Optional[str] = None
    status: Optional[str] = None          # "passed"/"failed"/None
    input: Optional[str] = None           # JSON-sträng
    output: Optional[str] = None          # Markdown-sträng
    eval: Optional[RunEval] = None

class Blueprint(BaseModel):
    """En blueprint-fil."""
    name: str
    path: str

class Stats(BaseModel):
    """Aggregerad statistik över alla runs."""
    total_runs: int
    passed: int
    failed: int
    average_score: Optional[float] = None

class StatusResponse(BaseModel):
    """API-status."""
    status: str
    version: str = "1.0.0"
    forge_root: str

# ---------- FastAPI-app ----------
app = FastAPI(title="Forge Command Center API", version="1.0.0")

# ---------- Hjälpfunktioner ----------
def get_forge_data() -> dict:
    """Läs forge.json (om den finns)."""
    forge_path = Path(FORGE_ROOT) / "forge.json"
    if not forge_path.exists():
        return {}
    with open(forge_path, encoding="utf-8") as f:
        return json.load(f)

def get_runs_list() -> list[dict]:
    """Lista alla runs från runs/-mappen."""
    runs_dir = Path(FORGE_ROOT) / "runs"
    if not runs_dir.exists():
        return []

    runs = []
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        run_id = run_dir.name
        entry = {"id": run_id}

        # input.json
        input_path = run_dir / "input.json"
        if input_path.exists():
            with open(input_path, encoding="utf-8") as f:
                entry["input"] = json.load(f)

        # output.md
        output_path = run_dir / "output.md"
        if output_path.exists():
            entry["output"] = output_path.read_text(encoding="utf-8")

        # eval.json
        eval_path = run_dir / "eval.json"
        if eval_path.exists():
            with open(eval_path, encoding="utf-8") as f:
                entry["eval"] = json.load(f)

        runs.append(entry)
    return runs

def get_blueprints_list() -> list[dict]:
    """Lista alla JSON-filer i blueprints/-mappen."""
    bp_dir = Path(FORGE_ROOT) / "blueprints"
    if not bp_dir.exists():
        return []
    blueprints = []
    for bp_file in sorted(bp_dir.iterdir()):
        if bp_file.suffix == ".json" and bp_file.is_file():
            blueprints.append({"name": bp_file.stem, "path": str(bp_file)})
    return blueprints

def compute_stats(runs: list[dict]) -> dict:
    """Beräkna aggregerad statistik från runs."""
    total = len(runs)
    passed = 0
    failed = 0
    scores = []
    for r in runs:
        eval_data = r.get("eval")
        if eval_data:
            if eval_data.get("passed"):
                passed += 1
            else:
                failed += 1
            score = eval_data.get("score")
            if score is not None:
                scores.append(score)
    avg = sum(scores) / len(scores) if scores else None
    return {
        "total_runs": total,
        "passed": passed,
        "failed": failed,
        "average_score": avg,
    }

# ---------- Endpoints ----------
@app.get("/api/runs", response_model=List[Run])
def get_runs():
    """Returnera en lista med alla runs tillsammans med input, output och utvärdering."""
    raw = get_runs_list()
    result = []
    for r in raw:
        # Hämta blueprint-namn från input om möjligt
        bp = None
        inp = r.get("input")
        if isinstance(inp, dict):
            bp = inp.get("blueprint")

        # Bygg Run-modell
        run_model = Run(
            id=r["id"],
            blueprint=bp,
            # status baserat på eval (om eval saknas → None)
            status=("passed" if r.get("eval", {}).get("passed") else "failed") if r.get("eval") else None,
            input=json.dumps(inp) if inp else None,
            output=r.get("output"),
            eval=RunEval(**r["eval"]) if r.get("eval") else None,
        )
        result.append(run_model)
    return result

@app.get("/api/blueprints", response_model=List[Blueprint])
def get_blueprints():
    """Returnera en lista över alla blueprints som finns i blueprints/-mappen."""
    return [Blueprint(**bp) for bp in get_blueprints_list()]

@app.get("/api/stats", response_model=Stats)
def get_stats():
    """Returnera aggregerad statistik (totalt, godkända, misslyckade, medelpoäng) från alla runs."""
    runs = get_runs_list()
    stats = compute_stats(runs)
    return Stats(**stats)

@app.get("/api/status", response_model=StatusResponse)
def get_status():
    """Returnera API-status, version och aktuell sökväg för FORGE_ROOT."""
    return StatusResponse(
        status="ok",
        forge_root=str(Path(FORGE_ROOT).resolve()),
    )

# ---------- Start ----------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```