"""Forge v2 — blueprint loading and validation.

Handles discovery, loading and schema validation of blueprint YAML definitions
under the blueprints/{internal,customer}/ directory tree.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("forge.core.blueprint")


def find_blueprint_dir(root: Path, blueprint_id: str) -> Optional[Path]:
    """Walk blueprints/{internal,customer}/ for a matching directory name."""
    bp_root = root / "blueprints"
    if not bp_root.exists():
        return None
    for sub in ["internal", "customer"]:  # ponytail: skip templates
        candidate = bp_root / sub / blueprint_id
        if candidate.is_dir():
            return candidate
    return None


def load_blueprint(root: Path, blueprint_id: str) -> dict:
    """Find and load a blueprint by ID. Raises ForgeError if not found."""
    import yaml
    from forge.core.engine import ForgeError

    bp_dir = find_blueprint_dir(root, blueprint_id)
    if not bp_dir:
        raise ForgeError(f"Blueprint '{blueprint_id}' not found under blueprints/")

    bp_yaml = bp_dir / "blueprint.yaml"
    if not bp_yaml.exists():
        raise ForgeError(f"{bp_yaml} missing for blueprint '{blueprint_id}'")

    with open(bp_yaml, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    data["_dir"] = str(bp_dir)
    return data


def validate_blueprint(root: Path, blueprint_id: str) -> list[str]:
    """Validate a blueprint and all referenced files. Returns list of error messages."""
    import yaml

    errors: list[str] = []

    bp_dir = find_blueprint_dir(root, blueprint_id)
    if not bp_dir:
        return [f"Blueprint '{blueprint_id}' directory not found under blueprints/"]

    bp_yaml = bp_dir / "blueprint.yaml"
    if not bp_yaml.exists():
        errors.append(f"Missing: {bp_yaml}")
        return errors

    try:
        with open(bp_yaml, "r", encoding="utf-8") as f:
            bp = yaml.safe_load(f)
    except Exception as e:
        return [f"blueprint.yaml parse error: {e}"]

    # Required top-level fields
    for field in ["id", "name", "version", "model", "evaluation"]:
        if field not in bp:
            errors.append(f"blueprint.yaml missing required field: '{field}'")

    model_cfg = bp.get("model", {})
    for field in ["provider", "model"]:
        if field not in model_cfg:
            errors.append(f"blueprint.yaml model section missing: '{field}'")

    # persona.md
    persona_md = bp_dir / "persona.md"
    if not persona_md.exists():
        errors.append("Missing: persona.md")
    elif persona_md.stat().st_size == 0:
        errors.append("persona.md exists but is empty")

    # tools.yaml
    tools_yaml = bp_dir / "tools.yaml"
    if not tools_yaml.exists():
        errors.append("Missing: tools.yaml (expected for tool-calling support)")

    # Benchmark cases
    eval_cfg = bp.get("evaluation", {})
    for case_file_rel in eval_cfg.get("benchmark_cases", []):
        case_path = root / case_file_rel
        if not case_path.exists():
            errors.append(f"Benchmark case file not found: {case_file_rel}")
            continue
        try:
            with open(case_path, "r", encoding="utf-8") as f:
                case_data = json.load(f)
        except Exception as e:
            errors.append(f"Benchmark case file parse error ({case_file_rel}): {e}")
            continue
        for case in case_data.get("cases", []):
            cid = case.get("id", "?")
            for req in ["id", "prompt", "expected_keywords"]:
                if req not in case:
                    errors.append(f"Case '{cid}' in {case_file_rel} missing required field: '{req}'")

    return errors
