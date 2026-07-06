```python
# main.py
import os
import json
import glob
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path

# Konfiguration via miljövariabel, fallback till nuvarande mapp
FORGE_ROOT = os.getenv("FORGE_ROOT", os.getcwd())
FORGE_ROOT_PATH = Path(FORGE_ROOT)

app = FastAPI(title="Forge Command Center API", version="1.0.0")

# ─── Pydantic-modeller ───────────────────────────────────────────────
class RunInput(BaseModel):
    prompt: str = ""
    model: str = ""
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    extra: Optional[dict] = None

class RunEval(BaseModel):
    score: Optional[float] = None
    feedback: Optional[str] = None
    passed: Optional[bool] = None
    extra: Optional[dict] = None

class Run(BaseModel):
    run_id: str
    name: Optional[str] = None
    created: Optional[str] = None
    input: RunInput = RunInput()
    output_path: Optional[str] = None
    output_text: Optional[str] = None
    eval: Optional[RunEval] = None
    status: str = "unknown"

class Blueprint(BaseModel):
    blueprint_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None

class Stats(BaseModel):
    total_runs: int
    evaluated_runs: int
    avg_score: Optional[float] = None
    passed_runs: int
    failed_runs: int
    models_used: list[str] = []

class Status(BaseModel):
    status: str = "ok"
    forge_root: str = FORGE_ROOT
    forge_version: Optional[str] = None
    run_count: int = 0
    blueprint_count: int = 0

# ─── Hjälpfunktioner ─────────────────────────────────────────────────

def read_json(path: Path) -> Optional[dict]:
    """Läs en JSON-fil och returnera dict, eller None om filen saknas."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

def read_text(path: Path) -> Optional[str]:
    """Läs en textfil och returnera sträng, eller None om filen saknas."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except IOError:
        return None

def load_forge_config() -> Optional[dict]:
    """Läs forge.json från roten."""
    forge_path = FORGE_ROOT_PATH / "forge.json"
    return read_json(forge_path)

def load_runs() -> list[Run]:
    """Skanna runs/run_*-mappar och läs data."""
    runs_path = FORGE_ROOT_PATH / "runs"
    if not runs_path.exists() or not runs_path.is_dir():
        return []

    runs = []
    # matcha mappar som heter run_* (exakt eller med suffix)
    for run_dir in sorted(runs_path.glob("run_*")):
        if not run_dir.is_dir():
            continue
        run_id = run_dir.name
        input_data = read_json(run_dir / "input.json")
        eval_data = read_json(run_dir / "eval.json")
        output_text = read_text(run_dir / "output.md")

        # Bygg Run-objekt
        run_input = RunInput(
            prompt=(input_data or {}).get("prompt", ""),
            model=(input_data or {}).get("model", ""),
            temperature=(input_data or {}).get("temperature"),
            max_tokens=(input_data or {}).get("max_tokens"),
            extra={k: v for k, v in (input_data or {}).items()
                   if k not in ("prompt", "model", "temperature", "max_tokens")}
        )
        run_eval = None
        if eval_data is not None:
            run_eval = RunEval(
                score=eval_data.get("score"),
                feedback=eval_data.get("feedback"),
                passed=eval_data.get("passed"),
                extra={k: v for k, v in eval_data.items()
                       if k not in ("score", "feedback", "passed")}
            )

        status = "unevaluated"
        if run_eval is not None:
            status = "evaluated"
        if output_text is not None:
            status = "completed" if status == "unevaluated" else status

        run = Run(
            run_id=run_id,
            name=(input_data or {}).get("name"),
            created=(input_data or {}).get("created"),
            input=run_input,
            output_path=str(run_dir / "output.md") if (run_dir / "output.md").exists() else None,
            output_text=output_text,
            eval=run_eval,
            status=status
        )
        runs.append(run)
    return runs

def load_blueprints() -> list[Blueprint]:
    """Skanna blueprints-mappen."""
    blueprints_path = FORGE_ROOT_PATH / "blueprints"
    if not blueprints_path.exists() or not blueprints_path.is_dir():
        return []
    blueprints = []
    for bp_dir in sorted(blueprints_path.iterdir()):
        if not bp_dir.is_dir():
            continue
        blueprint_id = bp_dir.name
        # Om det finns en blueprint.json, läs metadata, annars använd mappnamnet
        meta = read_json(bp_dir / "blueprint.json") or {}
        bp = Blueprint(
            blueprint_id=blueprint_id,
            name=meta.get("name", blueprint_id),
            description=meta.get("description"),
            path=str(bp_dir)
        )
        blueprints.append(bp)
    return blueprints

# ─── Endpoints ──────────────────────────────────────────────────────

@app.get("/api/runs", response_model=list[Run])
async def get_runs():
    """
    Returnera alla runs med input, output och evalueringsdata.
    """
    return load_runs()

@app.get("/api/blueprints", response_model=list[Blueprint])
async def get_blueprints():
    """
    Returnera alla blueprints från blueprints-mappen.
    """
    return load_blueprints()

@app.get("/api/stats", response_model=Stats)
async def get_stats():
    """
    Aggregerad statistik: totalt antal runs, evaluerade runs, genomsnittligt score,
    godkända/misslyckade, använda modeller.
    """
    runs = load_runs()
    evaluated = [r for r in runs if r.eval is not None]
    passed = [r for r in evaluated if r.eval and r.eval.passed is True]
    failed = [r for r in evaluated if r.eval and r.eval.passed is False]

    scores = [r.eval.score for r in evaluated if r.eval and r.eval.score is not None]
    avg_score = sum(scores)/len(scores) if scores else None

    models = list(set(r.input.model for r in runs if r.input.model))

    return Stats(
        total_runs=len(runs),
        evaluated_runs=len(evaluated),
        avg_score=avg_score,
        passed_runs=len(passed),
        failed_runs=len(failed),
        models_used=models
    )

@app.get("/api/status", response_model=Status)
async def get_status():
    """
    Hälsokontroll: returnerar status, forge-version (om i forge.json),
    antal runs och blueprints.
    """
    config = load_forge_config()
    forge_version = (config or {}).get("version") or (config or {}).get("forge_version")
    runs_count = len(load_runs())
    blueprints_count = len(load_blueprints())
    return Status(
        status="ok",
        forge_root=FORGE_ROOT,
        forge_version=forge_version,
        run_count=runs_count,
        blueprint_count=blueprints_count
    )

# ─── Startpunkt ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Förklaring**  
Applikationen läser `forge.json` från den rot som anges i miljövariabeln `FORGE_ROOT` (fallback: aktuell arbetskatalog). Den skannar `runs/run_*`-mappar för input, output och eval-filer, samt `blueprints/`-mappen för undermappar. Alla fyra endpoints returnerar strukturerad JSON enligt specifikationen, med Pydantic-validering och robust felhantering.