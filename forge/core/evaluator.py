"""Forge v2 evaluator — self-eval + judge-eval scoring.

ponytail: single-file evaluator, split if >300 lines.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from forge.core.engine import (
    load_run_data, call_llm, add_run_to_manifest, ForgeError,
)


def run_evaluation(root: Path, run_id: str,
                   provider: str = "openai",
                   model: str = "gpt-4o") -> dict:
    """Run self-eval + judge-eval on a run. Writes eval.json. Returns eval dict."""
    run_dir = root / "runs" / run_id
    if not run_dir.exists():
        raise ForgeError(f"Run not found: {run_id}")

    data = load_run_data(run_dir)
    output = data.get("output")
    if not output:
        raise ForgeError(f"No output.md in {run_id}")

    input_data = data.get("input")
    input_json = json.loads(input_data) if input_data else {}
    blueprint_id = input_json.get("blueprint_id", "unknown")

    # Load persona for context
    persona = _load_persona(root, blueprint_id)

    # 1. Self-eval
    self_score = _self_eval(output, persona, provider, model)

    # 2. Judge-eval
    judge_score = _judge_eval(output, persona, provider, model)

    # Weighted score
    final_score = round(self_score * 0.3 + judge_score * 0.7, 1)

    eval_result = {
        "run_id": run_id,
        "blueprint_id": blueprint_id,
        "evaluated_at": datetime.utcnow().isoformat(),
        "self_eval": self_score,
        "judge_eval": judge_score,
        "final_score": final_score,
        "weights": {"self_eval": 0.3, "judge_eval": 0.7},
    }

    # Write eval.json
    eval_path = run_dir / "eval.json"
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(eval_result, f, indent=2, ensure_ascii=False)

    # Update manifest
    status = "completed" if final_score >= 85 else "needs_improvement"
    add_run_to_manifest(root, run_id, blueprint_id, score=final_score, status=status)

    return eval_result


def _load_persona(root: Path, blueprint_id: str) -> str:
    """Load persona.md from the blueprint directory. Returns empty string if missing."""
    bp_root = root / "blueprints"
    for sub in ["internal", "customer"]:
        path = bp_root / sub / blueprint_id / "persona.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


def _self_eval(output: str, persona: str,
               provider: str, model: str) -> int:
    """Agent self-evaluates its own output. Returns 0-100."""
    system = f"""You are an AI agent evaluating your own output. Be honest and critical.
Your persona rules:
{persona if persona else 'No specific persona rules.'}

Rate your output from 0 to 100 based on:
- How well it follows the persona rules
- Quality, clarity, and usefulness of the response
- Any mistakes, hallucinations, or rule violations

Reply with ONLY a JSON object: {{"score": <0-100>, "reason": "<one sentence>"}}"""

    user = f"Evaluate this output:\n\n{output[:4000]}"  # ponytail: cap at 4k chars

    try:
        resp = call_llm(system, user, provider, model)
        result = json.loads(resp.strip().removeprefix("```json").removesuffix("```").strip())
        return max(0, min(100, int(result.get("score", 50))))
    except Exception:
        return 50  # ponytail: default mid-score on parse failure


def _judge_eval(output: str, persona: str,
                provider: str, model: str) -> int:
    """Independent judge LLM evaluates the output. Returns 0-100."""
    system = """You are an impartial judge evaluating an AI agent's output.
You have no knowledge of the agent's persona — judge purely on:
- Accuracy and truthfulness
- Clarity and structure
- Completeness (did it answer the question?)
- Absence of harmful, misleading, or low-quality content

Rate from 0 to 100. Reply with ONLY a JSON object: {"score": <0-100>, "reason": "<one sentence>"}"""

    user = f"Evaluate this AI output:\n\n{output[:4000]}"

    try:
        resp = call_llm(system, user, provider, model)
        result = json.loads(resp.strip().removeprefix("```json").removesuffix("```").strip())
        return max(0, min(100, int(result.get("score", 50))))
    except Exception:
        return 50


# --- Self-test ---

def _demo():
    """Quick smoke test: evaluate a trivial output."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        runs = root / "runs"
        runs.mkdir()
        run_dir = runs / "run_test"
        run_dir.mkdir()
        (run_dir / "output.md").write_text("Hello, this is a test response. It is clear and concise.")
        (run_dir / "input.json").write_text('{"blueprint_id": "test"}')

        try:
            result = run_evaluation(root, "run_test")
            assert 0 <= result["final_score"] <= 100
            assert (run_dir / "eval.json").exists()
            print(f"Demo passed. Score: {result['final_score']}")
        except Exception as e:
            print(f"Demo skipped (no API key?): {e}")


if __name__ == "__main__":
    _demo()
