```python
# main.py
import json
import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ---------- Config ----------
BASE_DIR = Path(__file__).resolve().parent
FORGE_JSON_PATH = BASE_DIR / "forge.json"
RUNS_DIR = BASE_DIR / "runs"

# ---------- Pydantic Models ----------
class Blueprint(BaseModel):
    id: str
    name: str
    version: str
    path: Optional[str] = None

class Input(BaseModel):
    prompt: str
    parameters: dict = {}

class Output(BaseModel):
    file: str
    content: str = ""

class Eval(BaseModel):
    score: Optional[float] = None
    passed: Optional[bool] = None

class Run(BaseModel):
    run_id: str
    blueprint_id: str
    input: Input
    output: Output
    eval: Eval
    timestamp: str = ""

class RunShort(BaseModel):
    run_id: str
    blueprint_id: str
    status: str = "ok"
    score: Optional[float] = None

class Stats(BaseModel):
    total_runs: int
    successful_runs: int
    failed_runs: int
    average_score: Optional[float] = None
    top_blueprints: list[str] = []

class Status(BaseModel):
    api_version: str = "1.0.0"
    status: str = "online"
    forge_version: Optional[str] = None
    total_runs: int = 0

# ---------- Application ----------
app = FastAPI(title="Forge Command Center API", version="1.0.0")

# ---------- Data Loading Helpers ----------
def load_forge_json() -> dict:
    if not FORGE_JSON_PATH.exists():
        raise FileNotFoundError(f"forge.json not found at {FORGE_JSON_PATH}")
    with open(FORGE_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_json_safe(filepath: Path) -> dict:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def load_run(run_dir: Path, forge_data: dict) -> Optional[Run]:
    """Ladda en run från en run-mapp. Returnera None om input saknas."""
    run_id = run_dir.name
    input_data = load_json_safe(run_dir / "input.json")
    output_data = {"file": "output.md", "content": ""}
    output_file = run_dir / "output.md"
    if output_file.exists():
        output_data["content"] = output_file.read_text(encoding="utf-8")
    eval_data = load_json_safe(run_dir / "eval.json")
    
    # Hitta blueprint_id från input eller forge.json (om möjligt)
    blueprint_id = input_data.get("blueprint_id", "")
    # Om blueprint_id saknas, försök härleda från forge.json (t.ex. första)
    if not blueprint_id and "blueprints" in forge_data:
        blueprint_id = forge_data["blueprints"][0].get("id", "unknown")
    
    return Run(
        run_id=run_id,
        blueprint_id=blueprint_id,
        input=Input(**input_data.get("input", {})),
        output=Output(file=output_data["file"], content=output_data["content"]),
        eval=Eval(**eval_data),
        timestamp=input_data.get("timestamp", ""),
    )

def load_all_runs(forge_data: dict) -> list[Run]:
    """Ladda alla runs från runs/ katalogen."""
    if not RUNS_DIR.exists():
        return []
    runs = []
    for entry in sorted(RUNS_DIR.iterdir()):
        if entry.is_dir() and entry.name.startswith("run_"):
            run = load_run(entry, forge_data)
            if run:
                runs.append(run)
    return runs

# ---------- Endpoints ----------

@app.get("/api/runs", response_model=list[RunShort])
async def get_runs():
    """Returnera en lista över alla runs, utan full output för prestanda."""
    try:
        forge = load_forge_json()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="forge.json saknas")
    runs = load_all_runs(forge)
    return [
        RunShort(
            run_id=r.run_id,
            blueprint_id=r.blueprint_id,
            status="ok" if r.eval.passed else "fail",
            score=r.eval.score
        )
        for r in runs
    ]

@app.get("/api/blueprints", response_model=list[Blueprint])
async def get_blueprints():
    """Returnera alla blueprints från forge.json."""
    try:
        forge = load_forge_json()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="forge.json saknas")
    return [
        Blueprint(**bp) for bp in forge.get("blueprints", [])
    ]

@app.get("/api/stats", response_model=Stats)
async def get_stats():
    """Returnera sammanställd statistik över alla runs."""
    try:
        forge = load_forge_json()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="forge.json saknas")
    runs = load_all_runs(forge)
    
    total = len(runs)
    successful = sum(1 for r in runs if r.eval.passed is True)
    failed = sum(1 for r in runs if r.eval.passed is False)
    scores = [r.eval.score for r in runs if r.eval.score is not None]
    avg_score = sum(scores) / len(scores) if scores else None
    
    # Räkna topp blueprints per förekomst
    bp_count = {}
    for r in runs:
        bp = r.blueprint_id
        bp_count[bp] = bp_count.get(bp, 0) + 1
    top_blueprints = sorted(bp_count, key=bp_count.get, reverse=True)[:5]
    
    return Stats(
        total_runs=total,
        successful_runs=successful,
        failed_runs=failed,
        average_score=avg_score,
        top_blueprints=top_blueprints
    )

@app.get("/api/status", response_model=Status)
async def get_status():
    """Returnera API-status och basinformation."""
    try:
        forge = load_forge_json()
        forge_version = forge.get("version", None)
    except FileNotFoundError:
        forge_version = None
    
    # Räkna antal runs (snabbt, utan att ladda all data)
    run_count = 0
    if RUNS_DIR.exists():
        run_count = sum(1 for d in RUNS_DIR.iterdir() if d.is_dir() and d.name.startswith("run_"))
    
    return Status(
        forge_version=forge_version,
        total_runs=run_count
    )

# ---------- Startup ----------
@app.on_event("startup")
def verify_structure():
    """Kontrollera att forge.json existerar vid uppstart."""
    if not FORGE_JSON_PATH.exists():
        print(f"Varning: {FORGE_JSON_PATH} saknas. API:et startar ändå men kan vara begränsat.")
    if not RUNS_DIR.exists():
        print(f"Varning: {RUNS_DIR} saknas. Inga runs att serva.")
```