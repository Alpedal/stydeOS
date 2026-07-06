"""Generate output for code agents and push to products. No evaluator — threshold=0."""
import json, os, sys, shutil
from pathlib import Path

os.environ.pop("DEEPSEEK_API_BASE", None)
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from forge.core.engine import create_run_dir, add_run_to_manifest
from forge.core.spawner import generate_output

AGENTS = {
    "dashboard-api": "Skriv en FastAPI-applikation för Forge Command Center som servar JSON-endpoints för /api/runs, /api/blueprints, /api/stats och /api/status.",
    "dashboard-ui": "Bygg ett mörkt HTML/CSS/JS-dashboard som pollar API:et var 5:e sekund. Visa aktiva runs, score-historik och agent-status.",
    "dashboard-data": "Skriv en Python-modul som läser forge.json och alla run-mappar, beräknar statistik (snitt-score, trend, fail rate) som JSON.",
}

for bp_id, prompt in AGENTS.items():
    print(f"\n{bp_id}...")
    run_dir = create_run_dir(ROOT, bp_id)
    ip = run_dir / "input.json"
    d = json.loads(ip.read_text())
    d["prompt"] = prompt
    ip.write_text(json.dumps(d, indent=2))
    add_run_to_manifest(ROOT, run_dir.name, bp_id, status="spawned")
    
    out = generate_output(ROOT, run_dir.name, provider="deepseek", model="deepseek-v4-flash")
    print(f"  Output: {len(out)} chars  →  {run_dir.name}")
    
    dest = ROOT / "production" / bp_id
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(run_dir / "output.md", dest / "output.md")
    print(f"  → production/{bp_id}/")

print(f"\nDone. 3 agents in production/.")
