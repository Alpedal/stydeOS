"""Forge v2 CLI — agent lifecycle commands.

Usage:
  python -m forge.cli.main init
  python -m forge.cli.main spawn <blueprint-id>
  python -m forge.cli.main eval <run-id>
  python -m forge.cli.main improve <run-id>
  python -m forge.cli.main loop <blueprint-id>
  python -m forge.cli.main validate <blueprint-id>
  python -m forge.cli.main clean [--days N]
"""

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Configure forge root logger: INFO to stderr, terse format matching legacy print style
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("forge.cli")

# ponytail: resolve root relative to this file's location
ROOT = Path(__file__).resolve().parent.parent.parent


# --- Per-run file logging ---

def _add_run_file_handler(run_dir: Path) -> logging.FileHandler:
    """Attach a FileHandler writing to runs/<run_id>/forge.log. Returns handler for later removal."""
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "forge.log"
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s — %(message)s"))
    logging.getLogger("forge").addHandler(fh)
    return fh


def _remove_run_file_handler(fh: logging.FileHandler) -> None:
    fh.flush()
    fh.close()
    logging.getLogger("forge").removeHandler(fh)


# --- ASCII score chart helper ---

def _render_score_chart(scores: list[tuple[int, float, str]]) -> str:
    """Render a compact ASCII score chart.

    Args:
        scores: list of (iteration, score, run_id) tuples
    """
    bar_width = 30
    lines = ["\n  ╔══════════════════════════════════════════════════╗",
             "  ║         Forge Training Progress                  ║",
             "  ╚══════════════════════════════════════════════════╝"]
    for i, (iteration, score, run_id) in enumerate(scores):
        filled = int((score / 100.0) * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        status = " ✓ PASSED" if score >= 85 else ""
        lines.append(f"  Iter {iteration:2d} │{bar}│ {score:5.1f}/100{status}")
    lines.append("")
    return "\n".join(lines)


# --- Commands ---

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
    fh = _add_run_file_handler(run_dir)
    try:
        add_run_to_manifest(ROOT, run_dir.name, blueprint_id, status="spawned")
        print(f"Run created: {run_dir}")
        print(f"  input.json ready — add your prompt + output.md, then:")
        print(f"    forge eval {run_dir.name}")
    finally:
        _remove_run_file_handler(fh)


def cmd_eval(run_id: str):
    """Evaluate a completed run."""
    from forge.core.evaluator import run_evaluation
    from forge.core.spawner import generate_output
    from forge.core.engine import load_run_data, load_blueprint

    run_dir = ROOT / "runs" / run_id
    if not run_dir.exists():
        print(f"Run not found: {run_id}")
        sys.exit(1)

    fh = _add_run_file_handler(run_dir)
    try:
        data = load_run_data(run_dir)
        input_data = data.get("input")
        input_json = json.loads(input_data) if input_data else {}
        blueprint_id = input_json.get("blueprint_id", "unknown")

        provider = "openai"
        model = "gpt-4o"
        try:
            bp = load_blueprint(ROOT, blueprint_id)
            provider = bp.get("model", {}).get("provider", "openai")
            model = bp.get("model", {}).get("model", "gpt-4o")
        except Exception:
            pass

        try:
            generate_output(ROOT, run_id, provider=provider, model=model)
        except Exception:
            pass

        result = run_evaluation(ROOT, run_id, provider=provider, model=model)
        print(f"Evaluation complete: {run_id}")
        if result.get("self_eval") is not None:
            print(f"  Self:  {result['self_eval']}")
        if result.get("judge_eval") is not None:
            print(f"  Judge: {result['judge_eval']}")
        if result.get("benchmark") is not None:
            print(f"  Bench: {result['benchmark']['score']}/100 ({result['benchmark']['cases_run']} cases)")
        print(f"  Final: {result['final_score']}/100")
        if result["final_score"] >= 85:
            print(f"  Status: PASSED")
        else:
            print(f"  Status: needs_improvement — run: forge improve {run_id}")
        print(f"  Log: {run_dir / 'forge.log'}")
    finally:
        _remove_run_file_handler(fh)


def cmd_improve(run_id: str):
    """Run the Teacher agent on a failed run."""
    from forge.core.teacher import propose_improvements
    from forge.core.engine import load_run_data, load_blueprint

    run_dir = ROOT / "runs" / run_id
    if not run_dir.exists():
        print(f"Run not found: {run_id}")
        sys.exit(1)

    fh = _add_run_file_handler(run_dir)
    try:
        data = load_run_data(run_dir)
        input_data = data.get("input")
        input_json = json.loads(input_data) if input_data else {}
        blueprint_id = input_json.get("blueprint_id", "unknown")

        provider = "openai"
        model = "gpt-4o"
        try:
            bp = load_blueprint(ROOT, blueprint_id)
            provider = bp.get("model", {}).get("provider", "openai")
            model = bp.get("model", {}).get("model", "gpt-4o")
        except Exception:
            pass

        result = propose_improvements(ROOT, run_id, provider=provider, model=model)
        print(f"Teacher analysis complete: {run_id}")
        print(f"  Score:    {result['score']}/100")
        print(f"  Status:   {result['status']}")
        if result.get("patches_applied"):
            for p in result["patches_applied"]:
                print(f"  Patched:  {p}")
        print(f"  Feedback: {run_dir / 'feedback.md'}")
        print(f"  Log:      {run_dir / 'forge.log'}")
    finally:
        _remove_run_file_handler(fh)


def cmd_loop(blueprint_id: str):
    """Full auto-cycle: spawn -> eval -> improve until score >= threshold."""
    from forge.core.engine import (
        load_blueprint, create_run_dir, add_run_to_manifest, load_run_data,
    )
    from forge.core.evaluator import run_evaluation
    from forge.core.teacher import propose_improvements
    from forge.core.spawner import generate_output

    bp = load_blueprint(ROOT, blueprint_id)
    threshold = bp.get("threshold", 85)
    max_iter = bp.get("max_iterations", 5)

    print(f"Loop: '{blueprint_id}' (threshold={threshold}, max_iter={max_iter})")

    scores: list[tuple[int, float, str]] = []
    passed = False

    for i in range(1, max_iter + 1):
        print(f"\n--- Iteration {i}/{max_iter} ---")

        run_dir = create_run_dir(ROOT, blueprint_id)
        add_run_to_manifest(ROOT, run_dir.name, blueprint_id, status="running")
        print(f"  Spawned: {run_dir.name}")

        fh = _add_run_file_handler(run_dir)
        try:
            provider = bp.get("model", {}).get("provider", "openai")
            model = bp.get("model", {}).get("model", "gpt-4o")
            try:
                generate_output(ROOT, run_dir.name, provider=provider, model=model)
            except Exception:
                pass

            data = load_run_data(run_dir)
            evaluation_config = bp.get("evaluation", {})
            has_benchmarks = bool(evaluation_config.get("benchmark_cases"))

            if not data.get("output") and not has_benchmarks:
                print(f"  No output.md in {run_dir.name} and no benchmark cases configured — break.")
                break

            eval_result = run_evaluation(ROOT, run_dir.name, provider=provider, model=model)
            score = eval_result["final_score"]
            scores.append((i, score, run_dir.name))
            print(f"  Score: {score}/100")
            print(_render_score_chart(scores))

            if score >= threshold:
                print(f"  PASSED! Score {score} >= {threshold}")
                passed = True
                break

            improve_result = propose_improvements(ROOT, run_dir.name, provider=provider, model=model)
            print(f"  Teacher: {improve_result['status']}")
            print(f"  Log: {run_dir / 'forge.log'}")
        finally:
            _remove_run_file_handler(fh)

    if not passed and scores:
        print(f"\n  Max iterations ({max_iter}) reached. Score didn't hit {threshold}.")

    print(f"\nDone. Check forge.json for run history.")


def cmd_validate(blueprint_id: str):
    """Validate a blueprint and all referenced files."""
    from forge.core.blueprint import validate_blueprint

    print(f"Validating blueprint: '{blueprint_id}'...")
    errors = validate_blueprint(ROOT, blueprint_id)
    if not errors:
        print(f"  [OK] Blueprint '{blueprint_id}' is valid. No issues found.")
    else:
        print(f"  [FAIL] Found {len(errors)} issue(s):")
        for err in errors:
            print(f"    - {err}")
        sys.exit(1)


def cmd_clean(days: int):
    """Delete runs older than N days that are failed/incomplete, clean forge.json."""
    from forge.core.engine import load_manifest, save_manifest

    runs_dir = ROOT / "runs"
    if not runs_dir.exists():
        print("No runs/ directory found.")
        return

    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    removed = []
    kept = []

    for run_folder in sorted(runs_dir.iterdir()):
        if not run_folder.is_dir():
            continue

        # Parse timestamp from run_YYYYMMDD-HHMMSS name
        try:
            ts_str = run_folder.name.removeprefix("run_")
            ts = datetime.strptime(ts_str, "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            kept.append(run_folder.name)
            continue

        if ts >= cutoff:
            kept.append(run_folder.name)
            continue

        # Only prune if not "completed"
        eval_path = run_folder / "eval.json"
        if eval_path.exists():
            try:
                eval_data = json.loads(eval_path.read_text(encoding="utf-8"))
                # Keep completed (passed) runs even if old
                manifest = load_manifest(ROOT)
                run_entries = {r["run_id"]: r for r in manifest.get("runs", [])}
                entry = run_entries.get(run_folder.name, {})
                if entry.get("status") == "completed":
                    kept.append(run_folder.name)
                    continue
            except Exception:
                pass

        print(f"  Removing {run_folder.name}...")
        shutil.rmtree(run_folder)
        removed.append(run_folder.name)

    # Clean up forge.json
    if removed:
        manifest = load_manifest(ROOT)
        manifest["runs"] = [r for r in manifest.get("runs", []) if r["run_id"] not in removed]
        save_manifest(ROOT, manifest)

    print(f"\nClean complete: {len(removed)} run(s) removed, {len(kept)} kept.")
    if removed:
        for r in removed:
            print(f"  - removed: {r}")


def cmd_history():
    """Display a colorized table of all runs from forge.json."""
    from forge.core.engine import load_manifest

    # ANSI color codes (gracefully degraded on non-color terminals)
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    DIM    = "\033[2m"

    manifest = load_manifest(ROOT)
    runs = sorted(manifest.get("runs", []), key=lambda r: r["run_id"], reverse=True)

    if not runs:
        print("No runs recorded in forge.json.")
        return

    # Header
    print(f"\n{BOLD}{CYAN}  Forge Run History{RESET}")
    print(f"  {'Run ID':<26} {'Blueprint':<20} {'Score':>7}  {'Status':<18} {'Git':<10}")
    print(f"  {'-'*26} {'-'*20} {'-'*7}  {'-'*18} {'-'*10}")

    for r in runs:
        run_id      = r.get("run_id", "?")
        blueprint   = r.get("blueprint_id", "-")
        score       = r.get("score")
        status      = r.get("status", "unknown")
        git_commit  = r.get("git_commit", "-")
        git_dirty   = r.get("git_dirty")

        score_str = f"{score:6.1f}/100" if score is not None else "     -/100"

        if status == "completed":
            status_col = f"{GREEN}{status:<18}{RESET}"
            score_col  = f"{GREEN}{score_str}{RESET}"
        elif status in ("needs_improvement", "improved"):
            status_col = f"{YELLOW}{status:<18}{RESET}"
            score_col  = f"{YELLOW}{score_str}{RESET}"
        elif status == "running":
            status_col = f"{CYAN}{status:<18}{RESET}"
            score_col  = score_str
        else:
            status_col = f"{DIM}{status:<18}{RESET}"
            score_col  = score_str

        dirty_marker = f"{RED}*{RESET}" if git_dirty else " "
        git_str = f"{git_commit}{dirty_marker}" if git_commit != "-" else DIM + "-" + RESET

        print(f"  {run_id:<26} {blueprint:<20} {score_col}  {status_col} {git_str}")

    print(f"  {DIM}(* = uncommitted changes at run time){RESET}\n")


# --- Main parser ---

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

    p = sub.add_parser("validate", help="Validate a blueprint and its referenced files")
    p.add_argument("blueprint_id", help="Blueprint ID to validate")

    p = sub.add_parser("clean", help="Remove old failed/incomplete runs")
    p.add_argument("--days", type=int, default=7, help="Remove runs older than N days (default: 7)")

    sub.add_parser("history", help="Show colorized run history table")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "spawn": lambda: cmd_spawn(args.blueprint_id),
        "eval": lambda: cmd_eval(args.run_id),
        "improve": lambda: cmd_improve(args.run_id),
        "loop": lambda: cmd_loop(args.blueprint_id),
        "validate": lambda: cmd_validate(args.blueprint_id),
        "clean": lambda: cmd_clean(args.days),
        "history": cmd_history,
    }
    commands[args.command]()


if __name__ == "__main__":
    main()
