"""Forge v2 teacher — analyze failures and propose blueprint improvements.

ponytail: single-file teacher, split if >300 lines.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from forge.core.engine import load_run_data, call_llm, ForgeError
from forge.core.blueprint import find_blueprint_dir

logger = logging.getLogger("forge.core.teacher")


def propose_improvements(root: Path, run_id: str,
                         provider: str = "openai",
                         model: str = "gpt-4o") -> dict:
    """Analyze a failed run and generate feedback + blueprint patches.

    Returns dict with: run_id, current_score, feedback_text, patches_applied
    """
    run_dir = root / "runs" / run_id
    if not run_dir.exists():
        raise ForgeError(f"Run not found: {run_id}")

    data = load_run_data(run_dir)

    # Read eval
    eval_raw = data.get("eval")
    if not eval_raw:
        raise ForgeError(f"No eval.json in {run_id}")

    eval_data = json.loads(eval_raw)
    score = eval_data.get("final_score", 0)

    if score >= 85:
        # Already good enough
        feedback = f"Score {score} >= 85. No improvements needed.\n"
        (run_dir / "feedback.md").write_text(feedback, encoding="utf-8")
        return {
            "run_id": run_id,
            "score": score,
            "status": "passed",
            "feedback": feedback,
        }

    # Get blueprint info
    input_data = json.loads(data.get("input") or "{}")
    blueprint_id = input_data.get("blueprint_id", "unknown")

    output = data.get("output") or ""
    persona = _load_persona(root, blueprint_id)

    # Gather prior feedback history to give Teacher context
    prior_feedback = _load_prior_feedback(root, blueprint_id, exclude_run=run_id)

    # Generate feedback
    feedback = _generate_feedback(output, eval_data, persona, provider, model, prior_feedback)
    (run_dir / "feedback.md").write_text(feedback, encoding="utf-8")

    # Try to patch blueprint files
    patches = _apply_blueprint_patches(root, blueprint_id, feedback)

    return {
        "run_id": run_id,
        "blueprint_id": blueprint_id,
        "score": score,
        "status": "improved",
        "feedback": feedback,
        "patches_applied": patches,
    }


def _load_persona(root: Path, blueprint_id: str) -> str:
    bp_dir = find_blueprint_dir(root, blueprint_id)
    if bp_dir:
        path = bp_dir / "persona.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


def _load_prior_feedback(root: Path, blueprint_id: str, exclude_run: str) -> str:
    """Load the most recent feedback.md files from runs of this blueprint (last 3)."""
    runs_dir = root / "runs"
    if not runs_dir.exists():
        return ""

    prior: list[str] = []
    # Sort descending so we get newest first
    for run_folder in sorted(runs_dir.iterdir(), reverse=True):
        if not run_folder.is_dir() or run_folder.name == exclude_run:
            continue
        input_path = run_folder / "input.json"
        feedback_path = run_folder / "feedback.md"
        if not input_path.exists() or not feedback_path.exists():
            continue
        try:
            input_json = json.loads(input_path.read_text(encoding="utf-8"))
            if input_json.get("blueprint_id") != blueprint_id:
                continue
        except Exception:
            continue
        prior.append(f"### Run: {run_folder.name}\n{feedback_path.read_text(encoding='utf-8')}")
        if len(prior) >= 3:
            break

    return "\n\n---\n\n".join(reversed(prior))  # chronological order


def _generate_feedback(output: str, eval_data: dict, persona: str,
                       provider: str, model: str,
                       prior_feedback: str = "") -> str:
    """Ask Teacher LLM to analyze what went wrong and suggest concrete fixes."""
    prior_section = ""
    if prior_feedback:
        prior_section = f"""
## Prior Improvement Attempts (for context — do NOT repeat the same fixes)
{prior_feedback[:4000]}
"""

    system = f"""You are a Teacher agent for the Forge training system.
Your job: analyze failed agent outputs and benchmark results, and propose concrete, actionable improvements.

Current persona rules:
{persona if persona else '(no persona rules defined)'}
{prior_section}
If there is a 'benchmark' key in the evaluation results:
- Carefully inspect all benchmark case results.
- Focus heavily on failed cases, looking at 'expected_missing' keywords, 'forbidden_found' keywords, and the 'reason' from the judge.
- Propose specific updates to the persona.md behavior or output format rules to ensure future runs include expected keywords, avoid forbidden keywords, and satisfy all rules.
- If you suspect the failures are caused by hyperparameter issues (e.g., high temperature causing hallucinations/formatting errors, or low max_tokens causing truncations):
  Suggest new values in the format `[PARAM_UPDATE] parameter_name: value` under a "## Parameter Updates" section. Valid parameters: temperature, max_tokens, top_p.

Output format (markdown):

## What Went Wrong
- Specific issues found in the run output or benchmark cases (list the failing benchmark case IDs and exactly what went wrong, e.g. missing or forbidden words).

## Which Rules Were Broken
- Reference specific persona sections or rules from the benchmark (e.g. inga_emojis, tredje_person, etc.).

## Proposed Fixes
- Concrete changes to persona.md to fix these failures (e.g. 'Add a rule to section X to state...'). Propose the exact wording to append or modify.

## Parameter Updates
- Any hyperparameter suggestions (using `[PARAM_UPDATE] name: value` syntax).

## Version Bump
- Suggest new version number (patch bump: x.y.z -> x.y.z+1)"""

    eval_str = json.dumps(eval_data, indent=2)
    user = f"""Evaluation results:
```json
{eval_str}
```

Agent output:
```
{output[:3000]}
```

Analyze the failure and propose improvements."""

    try:
        return call_llm(system, user, provider, model)
    except Exception as e:
        return f"## Teacher Error\n\nFailed to generate feedback: {e}"


def _bump_version(version_str: str) -> str:
    """Bump the patch segment of a semantic version, preserving pre-release suffixes.
    
    Examples:
      '1.0.2'       -> '1.0.3'
      '1.0.2-beta'  -> '1.0.3-beta'
      '1.0.2-beta.1'-> '1.0.3-beta.1'
    """
    # Match: major.minor.patch with an optional pre-release suffix
    m = re.match(r'^(\d+\.\d+\.)(\d+)(.*)', version_str)
    if not m:
        raise ValueError(f"Cannot parse version: {version_str!r}")
    prefix, patch, suffix = m.group(1), m.group(2), m.group(3)
    return f"{prefix}{int(patch) + 1}{suffix}"


def _update_yaml_model_param(content: str, param: str, value_str: str) -> str:
    """Update or insert a parameter inside the model: block in a YAML-like string while preserving comments."""
    lines = content.splitlines()
    model_idx = -1
    for idx, line in enumerate(lines):
        if line.strip().startswith("model:"):
            model_idx = idx
            break
    if model_idx == -1:
        return content

    param_idx = -1
    for idx in range(model_idx + 1, len(lines)):
        line = lines[idx]
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            break
        if line.strip().startswith(f"{param}:"):
            param_idx = idx
            break

    if param_idx != -1:
        line = lines[param_idx]
        indent = len(line) - len(line.lstrip())
        comment = ""
        if "#" in line:
            comment = " " + line[line.find("#"):]
        lines[param_idx] = " " * indent + f"{param}: {value_str}{comment}"
    else:
        indent = 2
        for idx in range(model_idx + 1, len(lines)):
            line = lines[idx]
            if line.strip():
                indent = len(line) - len(line.lstrip())
                break
        lines.insert(model_idx + 1, " " * indent + f"{param}: {value_str}")

    return "\n".join(lines) + "\n"


def _apply_blueprint_patches(root: Path, blueprint_id: str, feedback: str) -> list[str]:
    """Attempt to extract and apply version bumps + content patches from feedback.
    ponytail: naive extraction — full auto-patch is dangerous, keep it simple.
    Returns list of what was changed.
    """
    patches = []

    bp_dir = find_blueprint_dir(root, blueprint_id)
    if bp_dir:
        bp_yaml = bp_dir / "blueprint.yaml"
        if bp_yaml.exists():
            # Bump version in a comment-preserving way using regex
            content = bp_yaml.read_text(encoding="utf-8")
            match = re.search(
                r'^(version:\s*["\']?)(\d+\.\d+\.\d+[^"\'\s]*?)(["\']?\s*)$',
                content,
                re.MULTILINE
            )
            if match:
                version = match.group(2)
                try:
                    new_version = _bump_version(version)
                    old_line = match.group(0)
                    new_line = match.group(1) + new_version + match.group(3)
                    content = content.replace(old_line, new_line, 1)
                    patches.append(f"Bumped {blueprint_id} version: {version} -> {new_version}")
                    logger.info("Bumped %s version: %s -> %s", blueprint_id, version, new_version)
                except ValueError as e:
                    logger.warning("Could not bump version for %s: %s", blueprint_id, e)

            # Look for [PARAM_UPDATE] in feedback
            param_matches = re.findall(
                r'\[PARAM_UPDATE\]\s*(temperature|max_tokens|top_p):\s*([0-9.]+)',
                feedback,
                re.IGNORECASE
            )
            for param, val in param_matches:
                param = param.lower()
                content = _update_yaml_model_param(content, param, val)
                patches.append(f"Updated {blueprint_id} parameter '{param}' to {val}")

            bp_yaml.write_text(content, encoding="utf-8")

            # Append feedback reference to persona.md
            persona_md = bp_dir / "persona.md"
            if persona_md.exists() and feedback:
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
                note = f"\n\n<!-- Teacher feedback {timestamp} (run included in forge.json) -->\n"
                with open(persona_md, "a", encoding="utf-8") as f:
                    f.write(note)
                patches.append("Annotated persona.md with feedback timestamp")

    return patches


# --- Self-test ---

def _demo():
    """Smoke test: teacher on a fake run."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        runs = root / "runs"
        runs.mkdir()
        run_dir = runs / "run_test"
        run_dir.mkdir()
        (run_dir / "output.md").write_text("Bad response.")
        (run_dir / "eval.json").write_text('{"final_score": 45, "self_eval": 40, "judge_eval": 47}')
        (run_dir / "input.json").write_text('{"blueprint_id": "dummy"}')

        try:
            result = propose_improvements(root, "run_test")
            assert (run_dir / "feedback.md").exists()
            print(f"Demo passed. Status: {result['status']}")
        except Exception as e:
            print(f"Demo skipped (no API key?): {e}")


if __name__ == "__main__":
    _demo()
