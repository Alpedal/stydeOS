"""Re-run failed dashboard blueprints only."""
import json, os, sys, shutil
from pathlib import Path

os.environ.pop("DEEPSEEK_API_BASE", None)
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from forge.core.blueprint import load_blueprint
from forge.core.engine import create_run_dir, add_run_to_manifest, load_run_data
from forge.core.spawner import generate_output
from forge.core.evaluator import run_evaluation
from forge.core.teacher import propose_improvements

BLUEPRINTS = ["dashboard-api", "dashboard-ui", "dashboard-data"]
PROMTS = {
    "dashboard-api": "Skriv en FastAPI-applikation som läser forge.json och alla run-mappar och servar JSON-endpoints för /api/runs, /api/blueprints, /api/stats och /api/status.",
    "dashboard-ui": "Bygg ett mörkt HTML/CSS/JS-dashboard som pollar API:et var 5:e sekund och visar: aktiva runs, score-historik per blueprint, och agent-status. Inga externa beroenden.",
    "dashboard-data": "Skriv en Python-modul som läser forge.json och alla run-mappar, beräknar statistik (snitt-score, trend, fail rate) och returnerar som JSON-struktur för API:et.",
}
PROVIDER, FLASH, PRO = "deepseek", "deepseek-v4-flash", "deepseek-v4-pro"


def update_model(bp_id, model):
    import yaml
    bp = load_blueprint(ROOT, bp_id)
    bp_dir = Path(bp["_dir"])
    yp = bp_dir / "blueprint.yaml"
    d = yaml.safe_load(yp.read_text(encoding="utf-8"))
    d["model"]["provider"] = PROVIDER
    d["model"]["model"] = model
    yp.write_text(yaml.dump(d, default_flow_style=False, allow_unicode=True), encoding="utf-8")


def run_one(bp_id):
    print(f"\n{'='*60}\n  {bp_id}\n{'='*60}")
    for i in range(1, 4):
        print(f"\n  --- Iteration {i}/3 ---")
        update_model(bp_id, FLASH)
        run_dir = create_run_dir(ROOT, bp_id)
        ip = run_dir / "input.json"
        idata = json.loads(ip.read_text())
        idata["prompt"] = PROMTS[bp_id]
        ip.write_text(json.dumps(idata, indent=2))
        add_run_to_manifest(ROOT, run_dir.name, bp_id, status="running")
        print(f"    Spawn: {run_dir.name}")

        try:
            out = generate_output(ROOT, run_dir.name, provider=PROVIDER, model=FLASH)
            print(f"    Output: {len(out)} chars")
        except Exception as e:
            print(f"    Output failed: {e}")
            continue

        update_model(bp_id, PRO)
        print(f"    Eval: {PRO}")
        try:
            er = run_evaluation(ROOT, run_dir.name, provider=PROVIDER, model=PRO)
        except Exception as e:
            print(f"    Eval failed: {e}")
            continue

        s = er["final_score"]
        print(f"    Self: {er['self_eval']}  Judge: {er['judge_eval']}  Final: {s}/100")

        if s >= 85:
            dest = ROOT / "production" / bp_id
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(run_dir / "output.md", dest / "output.md")
            shutil.copy2(run_dir / "eval.json", dest / "eval.json")
            print(f"    ✓ PASSED → production/{bp_id}/")
            return {"blueprint": bp_id, "score": s, "status": "passed"}
        try:
            ir = propose_improvements(ROOT, run_dir.name, provider=PROVIDER, model=PRO)
            print(f"    Teacher: {ir['status']}")
        except Exception as e:
            print(f"    Improve failed: {e}")
    return {"blueprint": bp_id, "score": 0, "status": "failed"}


for bp in BLUEPRINTS:
    r = run_one(bp)
    print(f"\n  {'✓' if r['status']=='passed' else '✗'} {r['blueprint']}: {r['score']}/100")

for bp in BLUEPRINTS:
    update_model(bp, FLASH)
