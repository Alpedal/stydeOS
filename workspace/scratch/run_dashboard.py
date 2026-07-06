"""Forge v2 — run all dashboard blueprints with flash spawn + pro eval/improve."""
import json
import os
import sys
from pathlib import Path

# ponytail: skip dead local proxy
os.environ.pop("DEEPSEEK_API_BASE", None)

ROOT = Path(__file__).resolve().parent.parent.parent  # workspace/scratch/ → stydeOS/

# Import Forge internals
sys.path.insert(0, str(ROOT))
from forge.core.blueprint import load_blueprint
from forge.core.engine import create_run_dir, add_run_to_manifest, load_run_data
from forge.core.spawner import generate_output
from forge.core.evaluator import run_evaluation
from forge.core.teacher import propose_improvements

BLUEPRINTS = [
    "dashboard-architect",
    "dashboard-api",
    "dashboard-ui",
    "dashboard-data",
    "dashboard-tester",
]

PROMTS = {
    "dashboard-architect": "Planera arkitekturen för Forge Command Center - ett realtidsdashboard som visar alla Forge-runs, blueprint-status och statistik. Beskriv komponenterna: API, UI, datapipeline.",
    "dashboard-api": "Skriv en FastAPI-applikation som läser forge.json och alla run-mappar och servar JSON-endpoints för /api/runs, /api/blueprints, /api/stats och /api/status.",
    "dashboard-ui": "Bygg ett mörkt HTML/CSS/JS-dashboard som pollar API:et var 5:e sekund och visar: aktiva runs, score-historik per blueprint, och agent-status. Inga externa beroenden.",
    "dashboard-data": "Skriv en Python-modul som läser forge.json och alla run-mappar, beräknar statistik (snitt-score, trend, fail rate) och returnerar som JSON-struktur för API:et.",
    "dashboard-tester": "Skriv testfall för Forge Command Center: validera att alla API-endpoints returnerar korrekt JSON, att UI:n laddar utan JS-fel, och att datapipeline:n producerar korrekt statistik.",
}

PROVIDER = "deepseek"
FLASH_MODEL = "deepseek-v4-flash"
PRO_MODEL = "deepseek-v4-pro"


def update_blueprint_model(bp_id: str, model: str) -> None:
    import yaml
    bp = load_blueprint(ROOT, bp_id)
    bp_dir = Path(bp["_dir"])
    yaml_path = bp_dir / "blueprint.yaml"
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    data["model"]["provider"] = PROVIDER
    data["model"]["model"] = model
    yaml_path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")


def run_one(bp_id: str, max_iter: int = 3) -> dict:
    print(f"\n{'='*60}")
    print(f"  BLUEPRINT: {bp_id}")
    print(f"{'='*60}")

    for i in range(1, max_iter + 1):
        print(f"\n  --- Iteration {i}/{max_iter} ---")

        # 1. SPAWN with flash
        update_blueprint_model(bp_id, FLASH_MODEL)
        bp = load_blueprint(ROOT, bp_id)
        run_dir = create_run_dir(ROOT, bp_id)

        # Inject prompt into input.json
        input_path = run_dir / "input.json"
        input_data = json.loads(input_path.read_text())
        input_data["prompt"] = PROMTS.get(bp_id, f"Generate output for {bp_id}")
        input_path.write_text(json.dumps(input_data, indent=2))

        add_run_to_manifest(ROOT, run_dir.name, bp_id, status="running")
        print(f"    Spawn: {run_dir.name} (flash)")

        # Generate output
        try:
            output = generate_output(ROOT, run_dir.name, provider=PROVIDER, model=FLASH_MODEL)
            print(f"    Output: {len(output)} chars")
        except Exception as e:
            print(f"    Output failed: {e}")
            continue

        # 2. EVAL + IMPROVE with pro
        update_blueprint_model(bp_id, PRO_MODEL)
        print(f"    Eval + Improve: {PRO_MODEL}")

        try:
            eval_result = run_evaluation(ROOT, run_dir.name, provider=PROVIDER, model=PRO_MODEL)
        except Exception as e:
            print(f"    Eval failed: {e}")
            continue

        score = eval_result["final_score"]
        print(f"    Self: {eval_result['self_eval']}  Judge: {eval_result['judge_eval']}  Final: {score}/100")

        if score >= 85:
            # ponytail: push to production/
            import shutil
            dest = ROOT / "production" / bp_id
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(run_dir / "output.md", dest / "output.md")
            shutil.copy2(run_dir / "eval.json", dest / "eval.json")
            print(f"    ✓ PASSED ({score}/100) → production/{bp_id}/")
            return {"blueprint": bp_id, "iterations": i, "score": score, "status": "passed"}

        # Improve
        try:
            improve_result = propose_improvements(ROOT, run_dir.name, provider=PROVIDER, model=PRO_MODEL)
            print(f"    Teacher: {improve_result['status']}")
        except Exception as e:
            print(f"    Improve failed: {e}")

    print(f"    ✗ Max iterations ({max_iter}) — score didn't reach 85")
    return {"blueprint": bp_id, "iterations": max_iter, "score": 0, "status": "failed"}


def main():
    results = []
    for bp_id in BLUEPRINTS:
        result = run_one(bp_id)
        results.append(result)

    # Reset all to flash for consistency
    for bp_id in BLUEPRINTS:
        update_blueprint_model(bp_id, FLASH_MODEL)

    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    for r in results:
        icon = "✓" if r["status"] == "passed" else "✗"
        print(f"  {icon} {r['blueprint']:<25} {r['score']:5.1f}/100  ({r['iterations']} iter)")


if __name__ == "__main__":
    main()
