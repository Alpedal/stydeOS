"""Forge v2 core engine — manifest I/O and run directory management.

ponytail: this module is intentionally narrow. LLM logic lives in forge.core.llm,
blueprint logic lives in forge.core.blueprint. Re-exports are provided for
backwards compatibility so existing imports keep working.
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("forge.core.engine")


class ForgeError(Exception):
    pass


# --- Manifest ---

def load_manifest(root: Path) -> dict:
    """Read forge.json, return parsed dict. Dies if missing or invalid."""
    path = root / "forge.json"
    if not path.exists():
        raise ForgeError(f"forge.json not found at {root}. Run `forge init` first.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(root: Path, data: dict) -> None:
    """Atomic write to forge.json: write to temp, then rename."""
    path = root / "forge.json"
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp_path, path)


def init_manifest(root: Path) -> dict:
    """Create or reset forge.json. Returns the fresh manifest."""
    data = {
        "version": "2.0.0",
        "codename": "Crucible",
        "blueprints": [],
        "runs": [],
    }
    save_manifest(root, data)
    return data


# --- Runs ---

def create_run_dir(root: Path, blueprint_id: str) -> Path:
    """Create runs/run_{timestamp}/ with input.json skeleton. Returns the path."""
    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    run_dir = root / "runs" / f"run_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    git_info = _get_git_info(root)

    skeleton = {
        "run_id": run_id,
        "blueprint_id": blueprint_id,
        "started_at": datetime.utcnow().isoformat(),
        **git_info,
    }
    with open(run_dir / "input.json", "w", encoding="utf-8") as f:
        json.dump(skeleton, f, indent=2)

    return run_dir


def load_run_data(run_dir: Path) -> dict:
    """Load input.json, output.md, eval.json from a run dir. Missing files = None."""
    result = {}
    for key, filename in [
        ("input", "input.json"),
        ("output", "output.md"),
        ("eval", "eval.json"),
        ("feedback", "feedback.md"),
    ]:
        path = run_dir / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                result[key] = f.read()
        else:
            result[key] = None
    return result


def list_runs(root: Path) -> list[dict]:
    """Return all runs from forge.json, newest first."""
    manifest = load_manifest(root)
    runs = sorted(manifest.get("runs", []), key=lambda r: r["run_id"], reverse=True)
    return runs


def add_run_to_manifest(root: Path, run_id: str, blueprint_id: str,
                        score: Optional[float] = None,
                        status: str = "running",
                        git_commit: Optional[str] = None,
                        git_dirty: Optional[bool] = None) -> None:
    """Append or update a run entry in forge.json."""
    manifest = load_manifest(root)
    runs = manifest.setdefault("runs", [])

    entry: dict = {
        "run_id": run_id,
        "blueprint_id": blueprint_id,
        "score": score,
        "status": status,
    }
    if git_commit:
        entry["git_commit"] = git_commit
    if git_dirty is not None:
        entry["git_dirty"] = git_dirty

    for r in runs:
        if r["run_id"] == run_id:
            r.update(entry)
            break
    else:
        runs.append(entry)

    save_manifest(root, manifest)


# --- Git integration ---

def _get_git_info(root: Path) -> dict:
    """Return current git commit hash and dirty status. Returns empty dict on failure."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(root), stderr=subprocess.DEVNULL, text=True
        ).strip()
        dirty_out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=str(root), stderr=subprocess.DEVNULL, text=True
        ).strip()
        return {"git_commit": commit, "git_dirty": bool(dirty_out)}
    except Exception:
        return {}


# --- Backwards-compatibility re-exports ---
# Keep these so existing code that does `from forge.core.engine import call_llm`
# or `from forge.core.engine import load_blueprint` continues to work.

from forge.core.llm import call_llm                           # noqa: E402, F401
from forge.core.blueprint import load_blueprint, validate_blueprint  # noqa: E402, F401


def _find_blueprint_dir(root: Path, blueprint_id: str):  # noqa: F811
    """Backwards-compat shim — use forge.core.blueprint.find_blueprint_dir instead."""
    from forge.core.blueprint import find_blueprint_dir
    return find_blueprint_dir(root, blueprint_id)
