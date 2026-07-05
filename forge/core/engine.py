"""Forge v2 core engine — manifest I/O, LLM calls, run directory management.

ponytail: single-file core, split if >500 lines.
"""

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional


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


# --- Blueprints ---

def load_blueprint(root: Path, blueprint_id: str) -> dict:
    """Find and load a blueprint by ID from blueprints/ tree."""
    import yaml  # ponytail: lazy import, only needed for blueprints

    bp_dir = _find_blueprint_dir(root, blueprint_id)
    if not bp_dir:
        raise ForgeError(f"Blueprint '{blueprint_id}' not found under blueprints/")

    bp_yaml = bp_dir / "blueprint.yaml"
    if not bp_yaml.exists():
        raise ForgeError(f"{bp_yaml} missing for blueprint '{blueprint_id}'")

    with open(bp_yaml, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    data["_dir"] = str(bp_dir)
    return data


def _find_blueprint_dir(root: Path, blueprint_id: str) -> Optional[Path]:
    """Walk blueprints/{templates,internal,customer}/ for matching dir name."""
    bp_root = root / "blueprints"
    if not bp_root.exists():
        return None
    for sub in ["internal", "customer"]:  # ponytail: skip templates
        for entry in (bp_root / sub).iterdir():
            if entry.is_dir() and entry.name == blueprint_id:
                return entry
    return None


# --- Runs ---

def create_run_dir(root: Path, blueprint_id: str) -> Path:
    """Create runs/run_{timestamp}/ with input.json skeleton. Returns the path."""
    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    run_dir = root / "runs" / f"run_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    skeleton = {
        "run_id": run_id,
        "blueprint_id": blueprint_id,
        "started_at": datetime.utcnow().isoformat(),
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
                        status: str = "running") -> None:
    """Append or update a run entry in forge.json."""
    manifest = load_manifest(root)
    runs = manifest.setdefault("runs", [])

    # Update existing or append
    for r in runs:
        if r["run_id"] == run_id:
            r["score"] = score
            r["status"] = status
            break
    else:
        runs.append({
            "run_id": run_id,
            "blueprint_id": blueprint_id,
            "score": score,
            "status": status,
        })

    save_manifest(root, manifest)


# --- LLM ---

def call_llm(system_prompt: str, user_prompt: str,
             provider: str = "openai", model: str = "gpt-4o",
             api_key: Optional[str] = None) -> str:
    """Call an LLM and return the response text.

    Provider: 'openai' or 'anthropic'. API key from env if not passed:
      OPENAI_API_KEY / ANTHROPIC_API_KEY.
    """
    if provider == "openai":
        return _call_openai(system_prompt, user_prompt, model, api_key)
    elif provider == "anthropic":
        return _call_anthropic(system_prompt, user_prompt, model, api_key)
    else:
        raise ForgeError(f"Unknown provider: {provider}")


def _call_openai(system: str, user: str, model: str, api_key: Optional[str]) -> str:
    import openai

    client = openai.OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
    )
    return resp.choices[0].message.content


def _call_anthropic(system: str, user: str, model: str, api_key: Optional[str]) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text
