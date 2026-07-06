"""Forge loop for code agents — 3 consecutive >=85 to pass. Syntax eval, no LLM."""
import json, os, sys, shutil
from pathlib import Path

os.environ.pop("DEEPSEEK_API_BASE", None)
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from forge.core.engine import create_run_dir, add_run_to_manifest
from forge.core.spawner import generate_output
from forge.core.evaluator import run_evaluation

AGENTS = {
    "dashboard-api": "Skriv en FastAPI-applikation för Forge Command Center som servar JSON-endpoints för /api/runs, /api/blueprints, /api/stats och /api/status.",
    "dashboard-ui": "Bygg ett mörkt HTML/CSS/JS-dashboard som pollar API:et var 5:e sekund. Visa aktiva runs, score-historik och agent-status.",
    "dashboard-data": "Skriv en Python-modul som läser forge.json och alla run-mappar, beräknar statistik (snitt-score, trend, fail rate) som JSON.",
}
PROVIDER = "deepseek"
MODEL = "deepseek-v4-flash"
CONSECUTIVE = 3
THRESHOLD = 85

for bp_id, prompt in AGENTS.items():
    print(f"\n{'='*60}\n  {bp_id} (need {CONSECUTIVE}x >={THRESHOLD})\n{'='*60}")
    streak = 0
    attempt = 0
    while streak < CONSECUTIVE:
        attempt += 1
        print(f"\n  --- Run {attempt} (streak {streak}/{CONSECUTIVE}) ---")

        run_dir = create_run_dir(ROOT, bp_id)
        ip = run_dir / "input.json"
        d = json.loads(ip.read_text())
        d["prompt"] = prompt
        ip.write_text(json.dumps(d, indent=2))
        add_run_to_manifest(ROOT, run_dir.name, bp_id, status="running")

        out = generate_output(ROOT, run_dir.name, provider=PROVIDER, model=MODEL)
        print(f"    Output: {len(out)} chars")

        er = run_evaluation(ROOT, run_dir.name, provider=PROVIDER, model=MODEL)
        score = er["final_score"]
        print(f"    Score: {score}/100  (self={er.get('self_eval','?')} judge={er.get('judge_eval','?')})")

        if score >= THRESHOLD:
            streak += 1
            print(f"    + streak → {streak}/{CONSECUTIVE}")
        else:
            streak = 0
            print(f"    ✗ streak reset")

    # All passed
    dest = ROOT / "production" / bp_id
    dest.mkdir(parents=True, exist_ok=True)
    # Copy last successful run
    last_run = sorted(ROOT.glob(f"runs/run_*"))[-1]
    shutil.copy2(last_run / "output.md", dest / "output.md")
    shutil.copy2(last_run / "eval.json", dest / "eval.json")
    print(f"  ✓ PASSED → production/{bp_id}/ (after {attempt} runs)")

print(f"\nDone. All 3 agents in production/.")
