```python
# app.py
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json
import time
import os

# ----------------------------------------------------------------------
# Configuration via environment or default
# ----------------------------------------------------------------------
FORGE_ROOT = Path(os.environ.get("FORGE_ROOT", "."))

# ----------------------------------------------------------------------
# Pydantic models for responses (optional but clean)
# ----------------------------------------------------------------------
class StatusResponse(BaseModel):
    status: str
    version: str = "1.0"
    uptime_seconds: float

class StatsResponse(BaseModel):
    total_runs: int
    total_blueprints: int
    total_input_tokens: int = 0      # från input.json om de finns
    total_output_chars: int = 0      # från output.md
    avg_eval_score: float = 0.0      # genomsnitt ur eval.json

# ----------------------------------------------------------------------
# Helper functions (synchronous, stdlib only)
# ----------------------------------------------------------------------
def load_forge_json() -> dict:
    """Läser forge.json och returnerar som dict."""
    path = FORGE_ROOT / "forge.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}

def list_runs() -> list[dict]:
    """Går igenom runs/run_*/ och samlar data."""
    runs_dir = FORGE_ROOT / "runs"
    if not runs_dir.is_dir():
        return []
    runs = []
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.name.startswith("run_"):
            continue
        run_id = run_dir.name.replace("run_", "")
        run_data = {"run_id": run_id}

        # input.json
        input_path = run_dir / "input.json"
        if input_path.is_file():
            run_data["input"] = json.loads(input_path.read_text(encoding="utf-8"))
        else:
            run_data["input"] = {}

        # output.md
        output_path = run_dir / "output.md"
        if output_path.is_file():
            run_data["output"] = output_path.read_text(encoding="utf-8")
        else:
            run_data["output"] = ""

        # eval.json
        eval_path = run_dir / "eval.json"
        if eval_path.is_file():
            run_data["eval"] = json.loads(eval_path.read_text(encoding="utf-8"))
        else:
            run_data["eval"] = {}

        runs.append(run_data)
    return runs

def list_blueprints() -> list[dict]:
    """Läser alla .json-filer i blueprints/ och returnerar innehållet."""
    bp_dir = FORGE_ROOT / "blueprints"
    if not bp_dir.is_dir():
        return []
    blueprints = []
    for f in sorted(bp_dir.iterdir()):
        if f.suffix == ".json":
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                data["filename"] = f.name
                blueprints.append(data)
            except json.JSONDecodeError:
                # Hoppa över felaktiga filer
                pass
    return blueprints

def calculate_stats() -> dict:
    """Beräknar aggregerad statistik från runs och blueprints."""
    runs = list_runs()
    blueprints = list_blueprints()

    total_runs = len(runs)
    total_blueprints = len(blueprints)

    total_input_tokens = 0
    total_output_chars = 0
    eval_scores = []

    for run in runs:
        # tokens från input (om nyckeln 'tokens' finns i input)
        inp = run.get("input", {})
        if isinstance(inp, dict):
            total_input_tokens += inp.get("tokens", 0)
        elif isinstance(inp, str):
            total_input_tokens += len(inp.split())  # uppskattning

        # output-teckenlängd
        out = run.get("output", "")
        total_output_chars += len(out)

        # eval-score
        ev = run.get("eval", {})
        if isinstance(ev, dict) and "score" in ev:
            try:
                eval_scores.append(float(ev["score"]))
            except (ValueError, TypeError):
                pass

    avg_score = round(sum(eval_scores) / len(eval_scores), 2) if eval_scores else 0.0

    return {
        "total_runs": total_runs,
        "total_blueprints": total_blueprints,
        "total_input_tokens": total_input_tokens,
        "total_output_chars": total_output_chars,
        "avg_eval_score": avg_score,
    }

# ----------------------------------------------------------------------
# FastAPI app
# ----------------------------------------------------------------------
app = FastAPI(title="Forge Command Center API", version="1.0")
app_start_time = time.time()

@app.get("/api/runs", summary="Lista alla runs")
def get_runs():
    """
    Returnerar en lista med alla runs från runs/-katalogen.
    Varje run innehåller run_id, input, output och eval.
    """
    return list_runs()

@app.get("/api/blueprints", summary="Lista alla blueprints")
def get_blueprints():
    """
    Returnerar en lista med alla blueprints från blueprints/-katalogen.
    Varje blueprint innehåller JSON-datan samt filnamnet.
    """
    return list_blueprints()

@app.get("/api/stats", summary="Aggregerad statistik")
def get_stats():
    """
    Returnerar antal runs, blueprints, totalt antal tokens/tecken
    och genomsnittlig eval-score.
    """
    stats = calculate_stats()
    return StatsResponse(**stats)

@app.get("/api/status", summary="API-status")
def get_status():
    """
    Returnerar status "ok" samt version och upptid.
    """
    uptime = time.time() - app_start_time
    return StatusResponse(status="ok", uptime_seconds=round(uptime, 2))

# ----------------------------------------------------------------------
# För direktkörning
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Förklaring av varje endpoint:**

- `/api/runs` – läser alla `run_*`-mappar i `runs/` och returnerar en lista med dess `input.json`, `output.md` och `eval.json`.  
- `/api/blueprints` – returnerar alla JSON-filer som finns i `blueprints/`.  
- `/api/stats` – sammanställer totalt antal körningar, blueprints, tokens från input, tecken från output och genomsnittlig eval-poäng.  
- `/api/status` – svarar med `status: "ok"`, API-version och upptid i sekunder.

Alla sökvägar styrs via miljövariabeln `FORGE_ROOT` (standard är aktuell katalog). Inga externa bibliotek används för filläsning.