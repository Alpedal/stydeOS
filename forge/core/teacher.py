"""Forge v2 teacher — analyze failures and propose blueprint improvements.

ponytail: single-file teacher, split if >300 lines.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from forge.core.engine import load_run_data, call_llm, ForgeError


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

    # Generate feedback
    feedback = _generate_feedback(output, eval_data, persona, provider, model)
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
    for sub in ["internal", "customer"]:
        path = root / "blueprints" / sub / blueprint_id / "persona.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


def _generate_feedback(output: str, eval_data: dict, persona: str,
                       provider: str, model: str) -> str:
    """Ask Teacher LLM to analyze what went wrong and suggest concrete fixes."""
    system = f"""You are a Teacher agent for the Forge training system.
Your job: analyze failed agent outputs and propose concrete, actionable improvements.

Current persona rules:
{persona if persona else '(no persona rules defined)'}

Output format (markdown):

## What Went Wrong
- Specific issues found (be precise)

## Which Rules Were Broken
- Reference specific persona sections

## Proposed Fixes
- Concrete changes to persona.md, blueprint.yaml, or tools.yaml

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


def _apply_blueprint_patches(root: Path, blueprint_id: str, feedback: str) -> list[str]:
    """Attempt to extract and apply version bumps + content patches from feedback.
    ponytail: naive extraction — full auto-patch is dangerous, keep it simple.
    Returns list of what was changed.
    """
    import yaml
    import re

    patches = []

    for sub in ["internal", "customer"]:
        bp_yaml = root / "blueprints" / sub / blueprint_id / "blueprint.yaml"
        if not bp_yaml.exists():
            continue

        # Bump version
        with open(bp_yaml, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

        version = yaml_data.get("version", "0.1.0")
        parts = version.split(".")
        if len(parts) == 3:
            try:
                parts[2] = str(int(parts[2]) + 1)
                new_version = ".".join(parts)
                yaml_data["version"] = new_version
                with open(bp_yaml, "w", encoding="utf-8") as f:
                    yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
                patches.append(f"Bumped {blueprint_id} version: {version} -> {new_version}")
            except ValueError:
                pass

        # Append feedback reference to persona.md
        persona_md = bp_yaml.parent / "persona.md"
        if persona_md.exists() and feedback:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            note = f"\n\n<!-- Teacher feedback {timestamp} (run included in forge.json) -->\n"
            with open(persona_md, "a", encoding="utf-8") as f:
                f.write(note)
            patches.append(f"Annotated persona.md with feedback timestamp")

        break  # ponytail: first match only

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
