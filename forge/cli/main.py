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
    """Render a compact ASCII score chart (fully CP1252 encoding safe).

    Args:
        scores: list of (iteration, score, run_id) tuples
    """
    bar_width = 30
    lines = ["\n  +--------------------------------------------------+",
             "  |         Forge Training Progress                  |",
             "  +--------------------------------------------------+"]
    for i, (iteration, score, run_id) in enumerate(scores):
        filled = int((score / 100.0) * bar_width)
        bar = "#" * filled + "-" * (bar_width - filled)
        status = " [OK] PASSED" if score >= 85 else ""
        lines.append(f"  Iter {iteration:2d} |{bar}| {score:5.1f}/100{status}")
    lines.append("")
    lines.append("")
    return "\n".join(lines)


# --- Staging & Done Archiving Helpers ---

def _stage_blueprint_to_refinery(blueprint_id: str) -> None:
    """Move blueprint to refinery/ staging directory when training begins, if not already there."""
    from forge.core.blueprint import find_blueprint_dir
    import shutil
    
    bp_dir = find_blueprint_dir(ROOT, blueprint_id)
    if not bp_dir:
        return
        
    if bp_dir.parent.name == "refinery":
        return
        
    refinery_dir = ROOT / "refinery" / blueprint_id
    refinery_dir.parent.mkdir(parents=True, exist_ok=True)
    
    if refinery_dir.exists():
        shutil.rmtree(refinery_dir)
        
    shutil.move(str(bp_dir), str(refinery_dir))
    print(f"  [Refinery] Moved blueprint '{blueprint_id}' from {bp_dir.parent.name}/ to refinery/ staging area.")


def _push_to_production_and_archive(blueprint_id: str, run_id: str) -> None:
    """Copy successful run artifacts to production/ and move the blueprint to done-blueprints/."""
    from forge.core.blueprint import find_blueprint_dir
    import shutil
    
    run_dir = ROOT / "runs" / run_id
    bp_dir = find_blueprint_dir(ROOT, blueprint_id)
    
    # 1. Deploy outputs to production/
    prod_dir = ROOT / "production" / blueprint_id
    prod_dir.mkdir(parents=True, exist_ok=True)
    
    output_md = run_dir / "output.md"
    eval_json = run_dir / "eval.json"
    
    if output_md.exists():
        shutil.copy2(output_md, prod_dir / "output.md")
    if eval_json.exists():
        shutil.copy2(eval_json, prod_dir / "eval.json")
    print(f"  [Production] Deployed {blueprint_id} outputs to production/{blueprint_id}/")
    
    # 2. Archive blueprint folder to done-blueprints/
    if bp_dir:
        if bp_dir.parent.name == "done-blueprints":
            return
            
        done_dir = ROOT / "done-blueprints" / blueprint_id
        done_dir.parent.mkdir(parents=True, exist_ok=True)
        
        if done_dir.exists():
            shutil.rmtree(done_dir)
            
        shutil.move(str(bp_dir), str(done_dir))
        print(f"  [Archive] Archived blueprint '{blueprint_id}' to done-blueprints/{blueprint_id}/")


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

    _stage_blueprint_to_refinery(blueprint_id)

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
            _push_to_production_and_archive(blueprint_id, run_id)
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

        _stage_blueprint_to_refinery(blueprint_id)

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

    _stage_blueprint_to_refinery(blueprint_id)

    bp = load_blueprint(ROOT, blueprint_id)
    threshold = bp.get("threshold", 85)
    max_iter = bp.get("max_iterations", 5)

    print(f"Loop: '{blueprint_id}' (threshold={threshold}, max_iter={max_iter})")

    scores: list[tuple[int, float, str]] = []
    passed = False

    run_only_cases = None
    previous_results = None
    prev_run_name = None

    for i in range(1, max_iter + 1):
        print(f"\n--- Iteration {i}/{max_iter} ---")

        # Load incremental setup from previous run
        if i > 1 and prev_run_name:
            try:
                prev_eval_path = ROOT / "runs" / prev_run_name / "eval.json"
                if prev_eval_path.exists():
                    prev_eval = json.loads(prev_eval_path.read_text(encoding="utf-8"))
                    prev_results = prev_eval.get("benchmark", {}).get("results", [])
                    failed_cases = [r.get("id") for r in prev_results if r.get("score", 0.0) < threshold]
                    if failed_cases:
                        run_only_cases = failed_cases
                        previous_results = prev_results
                        print(f"  [Incremental] Running ONLY {len(failed_cases)} previously failed benchmark case(s).")
                    else:
                        run_only_cases = None
                        previous_results = None
            except Exception:
                run_only_cases = None
                previous_results = None

        run_dir = create_run_dir(ROOT, blueprint_id)
        add_run_to_manifest(ROOT, run_dir.name, blueprint_id, status="running")
        print(f"  Spawned: {run_dir.name}")

        prev_run_name = run_dir.name

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

            # Evaluate with incremental filters
            eval_result = run_evaluation(
                ROOT, run_dir.name, provider=provider, model=model,
                run_only_cases=run_only_cases,
                previous_results=previous_results
            )
            score = eval_result["final_score"]
            scores.append((i, score, run_dir.name))
            print(f"  Score: {score}/100")

            # Final verification check if incremental run passed
            if score >= threshold and run_only_cases is not None:
                print(f"  [Incremental] All target cases passed (combined score {score} >= {threshold}).")
                print("  Running final full sweep of all benchmark cases to verify no regressions...")
                eval_result = run_evaluation(ROOT, run_dir.name, provider=provider, model=model)
                score = eval_result["final_score"]
                print(f"  Final verified score: {score}/100")
                scores[-1] = (i, score, run_dir.name)

            print(_render_score_chart(scores))

            if score >= threshold:
                print(f"  PASSED! Score {score} >= {threshold}")
                passed = True
                _push_to_production_and_archive(blueprint_id, run_dir.name)
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
    print(f"  {'Run ID':<26} {'Blueprint':<20} {'Score':>7}  {'Status':<18} {'Tokens':>12} {'Cost':>10}")
    print(f"  {'-'*26} {'-'*20} {'-'*7}  {'-'*18} {'-'*12} {'-'*10}")

    for r in runs:
        run_id      = r.get("run_id", "?")
        blueprint   = r.get("blueprint_id", "-")
        score       = r.get("score")
        status      = r.get("status", "unknown")
        git_commit  = r.get("git_commit", "-")
        git_dirty   = r.get("git_dirty")
        pt          = r.get("prompt_tokens", 0) or 0
        ct          = r.get("completion_tokens", 0) or 0
        cost        = r.get("estimated_usd_cost")

        score_str = f"{score:6.1f}/100" if score is not None else "     -/100"
        tokens_str = f"{pt + ct:>6}" if (pt or ct) else "     -"
        cost_str = f"${cost:>8.4f}" if cost is not None else "        -"

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


def cmd_play(blueprint_id: str):
    """Start an interactive playground console with an agent blueprint."""
    from forge.core.blueprint import load_blueprint
    from forge.core.llm import call_llm
    from forge.core.spawner import (
        _load_persona, _load_tools, _load_mock_responses,
        _load_tools_impl, _execute_tool, MAX_TOOL_TURNS
    )

    try:
        bp = load_blueprint(ROOT, blueprint_id)
    except Exception as e:
        print(f"Error loading blueprint: {e}")
        sys.exit(1)

    persona = _load_persona(ROOT, blueprint_id)
    tools = _load_tools(ROOT, blueprint_id)
    mocks = _load_mock_responses(ROOT, blueprint_id)
    impl = _load_tools_impl(ROOT, blueprint_id)

    provider = bp.get("model", {}).get("provider", "openai")
    model = bp.get("model", {}).get("model", "gpt-4o")
    temperature = bp.get("model", {}).get("temperature")
    max_tokens = bp.get("model", {}).get("max_tokens")
    top_p = bp.get("model", {}).get("top_p")

    print("\n=========================================")
    print(f"  Forge Playground — Blueprint: '{blueprint_id}'")
    print(f"  Model: {provider}/{model}")
    print(f"  Tools loaded: {', '.join([t['name'] for t in tools]) if tools else 'None'}")
    print("  Type 'exit' or 'quit' to end session.")
    print("=========================================\n")

    while True:
        try:
            user_prompt = input("\nYou > ")
            if not user_prompt.strip():
                continue
            if user_prompt.strip().lower() in ("exit", "quit"):
                print("Exiting playground.")
                break

            current_input = user_prompt
            for turn in range(MAX_TOOL_TURNS):
                res = call_llm(
                    system_prompt=persona,
                    user_prompt=current_input,
                    provider=provider,
                    model=model,
                    tools=tools if tools else None,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p
                )

                if isinstance(res, dict) and "tool_call" in res:
                    tc = res["tool_call"]
                    t_name = tc["name"]
                    t_args = tc.get("arguments", {})

                    print(f"\n⚙️  Tool call: {t_name}({t_args})")
                    t_resp = _execute_tool(t_name, t_args, impl, mocks)
                    print(f"📥 Response: {t_resp}\n")

                    current_input = f"Tool result for {t_name}:\n{t_resp}"
                else:
                    print(f"\nAgent > {res}")
                    break
            else:
                print("\n[Playground Error: Max tool turns reached]")
        except KeyboardInterrupt:
            print("\nExiting playground.")
            break
        except Exception as e:
            print(f"\nError: {e}")


def cmd_status():
    """Show all blueprints, their directory locations, and latest training score/status."""
    from forge.core.engine import load_manifest, load_blueprint
    
    # 1. Load manifest runs
    latest_runs = {}
    try:
        manifest = load_manifest(ROOT)
        for run in manifest.get("runs", []):
            bp_id = run["blueprint_id"]
            # Save the latest run info (relying on chronological order in forge.json)
            latest_runs[bp_id] = {
                "score": run.get("score"),
                "status": run.get("status"),
                "run_id": run.get("run_id")
            }
    except Exception:
        pass

    # 2. Walk directories
    refinery_bps = []
    done_bps = []
    original_bps = []

    # refinery/
    refinery_dir = ROOT / "refinery"
    if refinery_dir.is_dir():
        for item in refinery_dir.iterdir():
            if item.is_dir() and (item / "blueprint.yaml").exists():
                refinery_bps.append(item.name)

    # done-blueprints/
    done_dir = ROOT / "done-blueprints"
    if done_dir.is_dir():
        for item in done_dir.iterdir():
            if item.is_dir() and (item / "blueprint.yaml").exists():
                done_bps.append(item.name)

    # blueprints/internal & customer
    bp_root = ROOT / "blueprints"
    if bp_root.is_dir():
        for sub in ["internal", "customer"]:
            sub_dir = bp_root / sub
            if sub_dir.is_dir():
                for item in sub_dir.iterdir():
                    if item.is_dir() and (item / "blueprint.yaml").exists():
                        name = item.name
                        # Only count as original if not active in refinery or done
                        if name not in refinery_bps and name not in done_bps and name not in original_bps:
                            original_bps.append(name)

    # Print output
    print("\n  +--------------------------------------------------+")
    print("  |         Forge Blueprint Lifecycle Status         |")
    print("  +--------------------------------------------------+")

    # Print Refinery Section
    print("\n  [ Refinery (Active Training) ]")
    if not refinery_bps:
        print("    (no active blueprints in refinery)")
    else:
        for bp_id in sorted(refinery_bps):
            version = "-"
            try:
                bp = load_blueprint(ROOT, bp_id)
                version = bp.get("version", "-")
            except Exception:
                pass
            run_info = latest_runs.get(bp_id)
            if run_info:
                score_str = f"{run_info['score']}/100" if run_info['score'] is not None else "-"
                status_str = f"({run_info['status']})"
            else:
                score_str = "-"
                status_str = "(unstarted)"
            print(f"    - {bp_id} (v{version})")
            print(f"      Latest: {score_str} {status_str}")

    # Print Done Section
    print("\n  [ Done (Production Ready Archived) ]")
    if not done_bps:
        print("    (no blueprints archived as done)")
    else:
        for bp_id in sorted(done_bps):
            version = "-"
            try:
                bp = load_blueprint(ROOT, bp_id)
                version = bp.get("version", "-")
            except Exception:
                pass
            run_info = latest_runs.get(bp_id)
            if run_info:
                score_str = f"{run_info['score']}/100" if run_info['score'] is not None else "-"
                status_str = f"({run_info['status']})"
            else:
                score_str = "-"
                status_str = "(passed)"
            print(f"    - {bp_id} (v{version})")
            print(f"      Latest: {score_str} {status_str}")

    # Print Originals Section
    print("\n  [ Original Blueprints ]")
    if not original_bps:
        print("    (no original blueprints left)")
    else:
        for bp_id in sorted(original_bps):
            version = "-"
            try:
                bp = load_blueprint(ROOT, bp_id)
                version = bp.get("version", "-")
            except Exception:
                pass
            print(f"    - {bp_id} (v{version})")
            print("      Status: unstarted")
    print("\n  +--------------------------------------------------+\n")


def cmd_stage(blueprint_id: str):
    """Manually stage a blueprint to the refinery/ folder."""
    from forge.core.blueprint import find_blueprint_dir
    bp_dir = find_blueprint_dir(ROOT, blueprint_id)
    if not bp_dir:
        print(f"Error: Blueprint '{blueprint_id}' not found in any staging/blueprint folder.")
        sys.exit(1)
    
    if bp_dir.parent.name == "refinery":
        print(f"Blueprint '{blueprint_id}' is already in refinery/ staging directory.")
        return

    _stage_blueprint_to_refinery(blueprint_id)
    print(f"Successfully staged '{blueprint_id}' to refinery/.")


def cmd_archive(blueprint_id: str, run_id: str):
    """Manually deploy outputs and archive blueprint to done-blueprints/."""
    from forge.core.blueprint import find_blueprint_dir
    bp_dir = find_blueprint_dir(ROOT, blueprint_id)
    if not bp_dir:
        print(f"Error: Blueprint '{blueprint_id}' not found.")
        sys.exit(1)

    run_dir = ROOT / "runs" / run_id
    if not run_dir.exists():
        print(f"Error: Run directory not found: {run_id}")
        sys.exit(1)

    _push_to_production_and_archive(blueprint_id, run_id)
    print(f"Successfully archived '{blueprint_id}' using run outputs from {run_id}.")


def cmd_cache_stats():
    """Show analytics and disk usage for cached LLM queries."""
    cache_dir = ROOT / ".forge_cache"
    if not cache_dir.exists():
        print("Cache stats: .forge_cache directory does not exist yet.")
        return
    files = list(cache_dir.glob("*.json"))
    total_size = sum(f.stat().st_size for f in files)
    print("\n  +--------------------------------------------------+")
    print("  |         Forge Cache Analytics                    |")
    print("  +--------------------------------------------------+")
    print(f"    Total Cached Queries:  {len(files)}")
    print(f"    Total Cache Size:      {total_size / 1024:.1f} KB ({total_size / 1024 / 1024:.2f} MB)")
    print(f"    Cache Directory:       {cache_dir}")
    print("    To clear all cached items, run: forge cache clean")
    print("  +--------------------------------------------------+\n")


def cmd_cache(action: str):
    """Dispatch cache actions (stats or clean)."""
    if action == "stats":
        cmd_cache_stats()
    elif action == "clean":
        cmd_cache_clean()


def cmd_report(run_id: str):
    """Generate a standalone HTML report for a run."""
    from forge.core.report import generate_report
    try:
        generate_report(ROOT, run_id)
    except Exception as e:
        print(f"Error generating report: {e}")
        sys.exit(1)


def cmd_cache_clean():
    """Clear all cached LLM API responses."""
    from forge.core.llm_cache import clear_cache
    count = clear_cache(ROOT)
    print(f"Cache cleared: {count} entry/entries removed.")


# --- Doctor ---

def cmd_doctor():
    """Scan all blueprints for health issues."""
    from datetime import datetime, timezone
    import yaml
    
    issues_critical = []
    issues_warning = []
    healthy = []
    
    # Collect all blueprint dirs
    bp_dirs = []
    for search in ["refinery", "done-blueprints", "blueprints/internal", "blueprints/customer"]:
        d = ROOT / search
        if d.is_dir():
            for item in d.iterdir():
                if item.is_dir() and (item / "blueprint.yaml").exists():
                    bp_dirs.append(item)
    
    if not bp_dirs:
        print("No blueprints found.")
        return
    
    # Load run history for stale checks
    run_bp_ids = set()
    try:
        manifest = load_manifest(ROOT)
        cutoff = datetime.now(timezone.utc).timestamp() - 7 * 86400
        for r in manifest.get("runs", []):
            try:
                ts = datetime.strptime(r["run_id"].removeprefix("run_"), "%Y%m%d-%H%M%S")
                ts = ts.replace(tzinfo=timezone.utc).timestamp()
                if ts >= cutoff:
                    run_bp_ids.add(r.get("blueprint_id", ""))
            except Exception:
                run_bp_ids.add(r.get("blueprint_id", ""))
    except Exception:
        pass
    
    for bp_dir in bp_dirs:
        bp_id = bp_dir.name
        bp_yaml = bp_dir / "blueprint.yaml"
        persona_md = bp_dir / "persona.md"
        
        # Check persona.md
        if not persona_md.exists():
            issues_critical.append(f"{bp_id}: missing persona.md")
            continue
        ps = persona_md.stat().st_size
        if ps == 0:
            issues_critical.append(f"{bp_id}: persona.md is empty")
        elif ps < 50:
            issues_warning.append(f"{bp_id}: persona.md is very short ({ps} bytes)")
        
        # Check blueprint.yaml
        if not bp_yaml.exists():
            issues_critical.append(f"{bp_id}: missing blueprint.yaml")
            continue
        
        try:
            bp = yaml.safe_load(bp_yaml.read_text())
        except Exception as e:
            issues_critical.append(f"{bp_id}: blueprint.yaml YAML error: {e}")
            continue
        
        if not isinstance(bp, dict):
            issues_critical.append(f"{bp_id}: blueprint.yaml is not a dict")
            continue
        
        for field in ["id", "name", "threshold", "model"]:
            if field not in bp:
                issues_warning.append(f"{bp_id}: missing field '{field}' in blueprint.yaml")
        
        # Stale check
        if bp_id not in run_bp_ids:
            issues_warning.append(f"{bp_id}: no runs in last 7 days (stale)")
        
        if bp_id not in [c.split(":")[0] for c in issues_critical + issues_warning]:
            healthy.append(bp_id)
    
    # Print report
    print()
    print("  +--------------------------------------------------+")
    print("  |              Forge Blueprint Doctor              |")
    print("  +--------------------------------------------------+")
    
    if healthy:
        print(f"\n  Healthy ({len(healthy)}):")
        for h in sorted(healthy):
            print(f"    [OK] {h}")
    
    if issues_warning:
        print(f"\n  Warnings ({len(issues_warning)}):")
        for w in sorted(issues_warning):
            print(f"    [!]  {w}")
    
    if issues_critical:
        print(f"\n  Critical ({len(issues_critical)}):")
        for c in sorted(issues_critical):
            print(f"    [X]  {c}")
    
    total = len(healthy) + len(issues_warning) + len(issues_critical)
    print(f"\n  Total: {total} blueprints scanned.")
    print("  +--------------------------------------------------+\n")


# --- Checkpoint ---

def cmd_checkpoint(name: str, list_flag: bool):
    """Save or list forge.json checkpoints."""
    ckpt_dir = ROOT / ".forge_checkpoints"
    
    if list_flag:
        if not ckpt_dir.is_dir():
            print("No checkpoints found.")
            return
        files = sorted(ckpt_dir.glob("checkpoint_*.json"))
        if not files:
            print("No checkpoints found.")
            return
        print(f"\n  Checkpoints ({len(files)}):")
        for f in files:
            s = f.stat()
            cname = f.stem.removeprefix("checkpoint_")
            print(f"    {cname}  |  {s.st_size:>6} bytes  |  {datetime.fromtimestamp(s.st_mtime).strftime('%Y-%m-%d %H:%M')}")
        print()
        return
    
    if not name:
        print("Usage: forge checkpoint <name>  or  forge checkpoint --list")
        return
    
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    forge_path = ROOT / "forge.json"
    if not forge_path.exists():
        print("No forge.json to checkpoint.")
        return
    
    import shutil
    dest = ckpt_dir / f"checkpoint_{name}.json"
    shutil.copy2(forge_path, dest)
    print(f"Checkpoint saved: {dest}")


def cmd_recover(name: str):
    """Restore forge.json from a checkpoint."""
    ckpt_dir = ROOT / ".forge_checkpoints"
    src = ckpt_dir / f"checkpoint_{name}.json"
    if not src.exists():
        print(f"Checkpoint '{name}' not found. Use --list to see available checkpoints.")
        return
    
    forge_path = ROOT / "forge.json"
    import shutil
    # Backup current
    if forge_path.exists():
        bak = ROOT / "forge.json.bak"
        shutil.copy2(forge_path, bak)
        print(f"Backup saved: {bak}")
    
    shutil.copy2(src, forge_path)
    print(f"Restored forge.json from checkpoint '{name}'.")


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

    p = sub.add_parser("play", help="Start interactive playground REPL console")
    p.add_argument("blueprint_id", help="Blueprint ID to play with")

    p = sub.add_parser("report", help="Generate standalone HTML report for a run")
    p.add_argument("run_id", help="Run ID to generate report for")

    sub.add_parser("cache-clean", help="Clear all disk-cached LLM responses")

    # refinery status
    sub.add_parser("status", help="Show all blueprints, refinery, done, and original list")

    # manual stage
    p = sub.add_parser("stage", help="Stage a blueprint manually to refinery/")
    p.add_argument("blueprint_id", help="Blueprint ID to stage")

    # manual archive
    p = sub.add_parser("archive", help="Manually deploy output and archive blueprint to done-blueprints/")
    p.add_argument("blueprint_id", help="Blueprint ID to archive")
    p.add_argument("run_id", help="Run ID to pull output from")

    # cache commands
    p = sub.add_parser("cache", help="Manage LLM cache")
    cache_sub = p.add_subparsers(dest="cache_command", required=True)
    cache_sub.add_parser("stats", help="Show cache disk size and query count stats")
    cache_sub.add_parser("clean", help="Clear all disk-cached LLM responses")

    # doctor
    sub.add_parser("doctor", help="Scan all blueprints for health issues")

    # checkpoint
    p = sub.add_parser("checkpoint", help="Save/restore forge.json checkpoints")
    p.add_argument("name", nargs="?", help="Checkpoint name (or --list)")
    p.add_argument("--list", action="store_true", help="List all checkpoints")

    # recover
    p = sub.add_parser("recover", help="Restore forge.json from a checkpoint")
    p.add_argument("name", help="Checkpoint name to restore")

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
        "play": lambda: cmd_play(args.blueprint_id),
        "report": lambda: cmd_report(args.run_id),
        "cache-clean": cmd_cache_clean,
        "status": cmd_status,
        "stage": lambda: cmd_stage(args.blueprint_id),
        "archive": lambda: cmd_archive(args.blueprint_id, args.run_id),
        "cache": lambda: cmd_cache(args.cache_command),
        "doctor": cmd_doctor,
        "checkpoint": lambda: cmd_checkpoint(args.name, args.list),
        "recover": lambda: cmd_recover(args.name),
    }
    commands[args.command]()


if __name__ == "__main__":
    main()
