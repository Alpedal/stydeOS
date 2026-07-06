**Fil: app.py**  
FastAPI-applikation som läser `forge.json`, `runs/` och `blueprints/` från `FORGE_ROOT` (miljövariabel, standard `"."`) och servar fyra JSON-endpoints.

```python
# app.py
import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Forge Command Center API")

# CORS för frontend (valfritt men rekommenderas)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Konfiguration via miljövariabel
FORGE_ROOT = Path(os.getenv("FORGE_ROOT", "."))


@app.get("/api/status")
async def get_status():
    """Returnerar API-status som en JSON-objekt med status och version."""
    return {"status": "ok", "version": "1.0"}


@app.get("/api/runs")
async def get_runs():
    """Returnerar en lista med alla körningar (runs) inklusive input, output-preview och eval-data."""
    runs_dir = FORGE_ROOT / "runs"
    if not runs_dir.exists():
        return []

    runs = []
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir() or not run_dir.name.startswith("run_"):
            continue

        run_data = {"id": run_dir.name}

        # input.json
        input_path = run_dir / "input.json"
        if input_path.exists():
            try:
                with open(input_path) as f:
                    run_data["input"] = json.load(f)
            except (json.JSONDecodeError, OSError):
                run_data["input"] = None

        # output.md (första 500 tecken)
        output_path = run_dir / "output.md"
        if output_path.exists():
            try:
                with open(output_path) as f:
                    run_data["output_preview"] = f.read(500)
            except OSError:
                run_data["output_preview"] = None

        # eval.json
        eval_path = run_dir / "eval.json"
        if eval_path.exists():
            try:
                with open(eval_path) as f:
                    run_data["eval"] = json.load(f)
            except (json.JSONDecodeError, OSError):
                run_data["eval"] = None

        runs.append(run_data)

    return runs


@app.get("/api/blueprints")
async def get_blueprints():
    """Returnerar en lista med alla blueprints (varje .json-fil i blueprints-mappen) med namn och innehåll."""
    blueprints_dir = FORGE_ROOT / "blueprints"
    if not blueprints_dir.exists():
        return []

    blueprints = []
    for file in sorted(blueprints_dir.iterdir()):
        if file.suffix != ".json":
            continue
        try:
            with open(file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        blueprints.append({"name": file.stem, "data": data})

    return blueprints


@app.get("/api/stats")
async def get_stats():
    """Returnerar aggregerad statistik: antal runs, antal blueprints och senaste run-namn."""
    stats = {
        "total_runs": 0,
        "total_blueprints": 0,
        "latest_run": None,
    }

    runs_dir = FORGE_ROOT / "runs"
    if runs_dir.exists():
        run_dirs = [
            d for d in runs_dir.iterdir()
            if d.is_dir() and d.name.startswith("run_")
        ]
        stats["total_runs"] = len(run_dirs)
        if run_dirs:
            latest = max(run_dirs, key=lambda d: d.stat().st_mtime)
            stats["latest_run"] = latest.name

    blueprints_dir = FORGE_ROOT / "blueprints"
    if blueprints_dir.exists():
        bp_files = [f for f in blueprints_dir.iterdir() if f.suffix == ".json"]
        stats["total_blueprints"] = len(bp_files)

    return stats
```

**Körning:**  
```bash
pip install fastapi uvicorn
uvicorn app:app --reload
```

**Endpoints-förklaringar:**  
- `GET /api/status` – Enkel hälsokontroll.  
- `GET /api/runs` – Listar alla runs med inläst data från `input.json`, `output.md` och `eval.json`.  
- `GET /api/blueprints` – Listar alla blueprints från `blueprints/`-mappen.  
- `GET /api/stats` – Summerar antal runs, antal blueprints och identifierar senaste run.  

Alla svar är JSON. Felaktig eller saknad data hanteras med `try/except` så att APIet alltid returnerar ett svar.