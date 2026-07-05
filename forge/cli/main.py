"""Forge v2 CLI — agent lifecycle commands.

Usage:
  python -m forge.cli.main init
  python -m forge.cli.main spawn <blueprint-id>
  python -m forge.cli.main eval <run-id>
  python -m forge.cli.main improve <run-id>
  python -m forge.cli.main loop <blueprint-id>
"""

import argparse
import json
import sys
from pathlib import Path

# ponytail: resolve root relative to this file's location
ROOT = Path(__file__).resolve().parent.parent.parent


def cmd_init():
    """Create or reset forge.json."""
    from forge.core.engine import init_manifest
    data = init_manifest(ROOT)
    print(f"Forge v{data['version']} ({data['codename']}) initialized.")
    print(f"  {ROOT / 'forge.json'}")


def cmd_spawn(blueprint_id: str):
    """Spawn a new agent run from a blueprint."""
    from forge.core.engine import load_blueprint, create_run_dir, add_run_to_manifest

    bp = load_blueprint(ROOT, blueprint_id)
    print(f"Blueprint: {bp.get('name', blueprint_id)} v{bp.get('version', '?')}")

    run_dir = create_run_dir(ROOT, blueprint_id)
    add_run_to_manifest(ROOT, run_dir.name, blueprint_id, status="spawned")

    print(f"Run created: {run_dir}")
    print(f"  input.json ready — add your prompt + output.md, then:")
    print(f"    forge eval {run_dir.name}")


def cmd_eval(run_id: str):
    """Evaluate a completed run."""
    from forge.core.evaluator import run_evaluation

    run_dir = ROOT / "runs" / run_id
    if not run_dir.exists():
        print(f"Run not found: {run_id}")
        sys.exit(1)

    result = run_evaluation(ROOT, run_id)
    print(f"Evaluation complete: {run_id}")
    print(f"  Self:  {result['self_eval']}")
    print(f"  Judge: {result['judge_eval']}")
    print(f"  Final: {result['final_score']}/100")
    if result["final_score"] >= 85:
        print(f"  Status: PASSED")
    else:
        print(f"  Status: needs_improvement — run: forge improve {run_id}")


def cmd_improve(run_id: str):
    """Run the Teacher agent on a failed run."""
    from forge.core.teacher import propose_improvements

    run_dir = ROOT / "runs" / run_id
    if not run_dir.exists():
        print(f"Run not found: {run_id}")
        sys.exit(1)

    result = propose_improvements(ROOT, run_id)
    print(f"Teacher analysis complete: {run_id}")
    print(f"  Score:    {result['score']}/100")
    print(f"  Status:   {result['status']}")
    if result.get("patches_applied"):
        for p in result["patches_applied"]:
            print(f"  Patched:  {p}")
    print(f"  Feedback: {run_dir / 'feedback.md'}")


def cmd_loop(blueprint_id: str):
    """Full auto-cycle: spawn -> eval -> improve until score >= threshold."""
    from forge.core.engine import (
        load_blueprint, create_run_dir, add_run_to_manifest, load_run_data,
    )
    from forge.core.evaluator import run_evaluation
    from forge.core.teacher import propose_improvements

    bp = load_blueprint(ROOT, blueprint_id)
    threshold = bp.get("threshold", 85)
    max_iter = bp.get("max_iterations", 5)

    print(f"Loop: '{blueprint_id}' (threshold={threshold}, max_iter={max_iter})")

    for i in range(1, max_iter + 1):
        print(f"\n--- Iteration {i}/{max_iter} ---")

        # Spawn
        run_dir = create_run_dir(ROOT, blueprint_id)
        add_run_to_manifest(ROOT, run_dir.name, blueprint_id, status="running")
        print(f"  Spawned: {run_dir.name}")

        # Generate output (ponytail: requires LLM call — skip for now, user adds output.md)
        data = load_run_data(run_dir)
        if not data.get("output"):
            print(f"  No output.md in {run_dir.name} — add one and re-run eval manually.")
            print(f"  (Auto-generation coming in forge/core/spawner.py)")
            break

        # Eval
        eval_result = run_evaluation(ROOT, run_dir.name)
        score = eval_result["final_score"]
        print(f"  Score: {score}/100")

        if score >= threshold:
            print(f"\n  PASSED! Score {score} >= {threshold}")
            break

        # Improve
        improve_result = propose_improvements(ROOT, run_dir.name)
        print(f"  Teacher: {improve_result['status']}")
    else:
        print(f"\n  Max iterations ({max_iter}) reached. Score didn't hit {threshold}.")

    print(f"\nDone. Check forge.json for run history.")


def main():
    parser = argparse.ArgumentParser(
        prog="forge",
        description="Forge v2 — agent training and deployment engine",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize or reset forge.json")

    p = sub.add_parser("spawn", help="Start a new agent run from a blueprint")
    p.add_argument("blueprint_id", help="Blueprint ID to spawn")

    p = sub.add_parser("eval", help="Evaluate a completed run")
    p.add_argument("run_id", help="Run ID (e.g. run_20260705-231500)")

    p = sub.add_parser("improve", help="Run Teacher agent on a failed run")
    p.add_argument("run_id", help="Run ID to improve")

    p = sub.add_parser("loop", help="Full auto-cycle: spawn -> eval -> improve")
    p.add_argument("blueprint_id", help="Blueprint ID to loop on")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "spawn": lambda: cmd_spawn(args.blueprint_id),
        "eval": lambda: cmd_eval(args.run_id),
        "improve": lambda: cmd_improve(args.run_id),
        "loop": lambda: cmd_loop(args.blueprint_id),
    }
    commands[args.command]()


if __name__ == "__main__":
    main()
