```python
# app.py
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ------------------------------------------------------------------
# Configuration (use environment variable FORGE_ROOT or default to current directory)
# ------------------------------------------------------------------
FORGE_ROOT = Path(os.environ.get("FORGE_ROOT", "."))

# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------
def read_json(path: Path) -> dict:
    """Read and parse a JSON file, returning empty dict on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def read_text(path: Path) -> str:
    """Read a text file, returning empty string on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def get_run_dirs() -> List[Path]:
    """Return sorted list of run_* directories under runs/."""
    runs_dir = FORGE_ROOT / "runs"
    if not runs_dir.exists():
        return []
    return sorted(
        [d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("run_")],
        key=lambda p: p.name
    )

def load_blueprints() -> List[Dict[str, Any]]:
    """Load all blueprint files from blueprints/ folder (JSON format expected)."""
    blueprints_dir = FORGE_ROOT / "blueprints"
    if not blueprints_dir.exists():
        return []
    blueprints = []
    for f in sorted(blueprints_dir.iterdir()):
        if f.suffix.lower() == ".json":
            data = read_json(f)
            data["filename"] = f.name
            blueprints.append(data)
    return blueprints

# ------------------------------------------------------------------
# Pydantic models (for response validation / documentation)
# ------------------------------------------------------------------
class RunInfo(BaseModel):
    run_id: str
    input_data: dict = {}
    eval_data: dict = {}
    output_markdown: str = ""

class BlueprintInfo(BaseModel):
    filename: str
    data: dict = {}

class Stats(BaseModel):
    total_runs: int
    successful_count: int
    failed_count: int
    latest_run_id: Optional[str] = None

class StatusResponse(BaseModel):
    status: str = "ok"
    version: str = "unknown"
    forge_root: str = "."

# ------------------------------------------------------------------
# FastAPI application
# ------------------------------------------------------------------
app = FastAPI(title="Forge Command Center API", version="0.1.0")

# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@app.get("/api/runs", response_model=List[RunInfo])
async def list_runs():
    """Return a list of all runs with their input, eval and output data."""
    runs = []
    for run_dir in get_run_dirs():
        run_id = run_dir.name
        input_data = read_json(run_dir / "input.json")
        eval_data = read_json(run_dir / "eval.json")
        output_md = read_text(run_dir / "output.md")
        runs.append(RunInfo(
            run_id=run_id,
            input_data=input_data,
            eval_data=eval_data,
            output_markdown=output_md
        ))
    return runs

@app.get("/api/blueprints", response_model=List[BlueprintInfo])
async def list_blueprints():
    """Return a list of all blueprints found in blueprints/ directory."""
    bp_list = []
    for bp in load_blueprints():
        bp_list.append(BlueprintInfo(filename=bp.pop("filename"), data=bp))
    return bp_list

@app.get("/api/stats", response_model=Stats)
async def get_stats():
    """Return aggregated statistics about runs."""
    run_dirs = get_run_dirs()
    total = len(run_dirs)
    success = 0
    fail = 0
    latest = None
    if run_dirs:
        latest = run_dirs[-1].name
    for run_dir in run_dirs:
        eval_data = read_json(run_dir / "eval.json")
        # Assume eval.json contains a "status" field (e.g., "success" or "failed")
        status = eval_data.get("status", "unknown")
        if status == "success":
            success += 1
        elif status == "failed":
            fail += 1
    return Stats(
        total_runs=total,
        successful_count=success,
        failed_count=fail,
        latest_run_id=latest
    )

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Return API health status and version from forge.json."""
    forge_config = read_json(FORGE_ROOT / "forge.json")
    version = forge_config.get("version", "unknown")
    return StatusResponse(version=version, forge_root=str(FORGE_ROOT.resolve()))

# ------------------------------------------------------------------
# Run the application (only when executed directly)
# ------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```