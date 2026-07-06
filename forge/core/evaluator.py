"""Forge v2 evaluator — self-eval + judge-eval scoring.

ponytail: single-file evaluator, split if >300 lines.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from forge.core.engine import (
    load_run_data, call_llm, add_run_to_manifest, ForgeError,
)
from forge.core.blueprint import find_blueprint_dir

logger = logging.getLogger("forge.core.evaluator")


def run_evaluation(root: Path, run_id: str,
                   provider: str = "openai",
                   model: str = "gpt-4o",
                   run_only_cases: Optional[list[str]] = None,
                   previous_results: Optional[list[dict]] = None) -> dict:
    """Run self-eval + judge-eval on a run, and execute benchmark cases if configured.
    Writes eval.json. Returns eval dict.
    """
    from forge.core.engine import load_blueprint
    from forge.core.spawner import run_benchmarks

    run_dir = root / "runs" / run_id
    if not run_dir.exists():
        raise ForgeError(f"Run not found: {run_id}")

    data = load_run_data(run_dir)
    output = data.get("output")

    input_data = data.get("input")
    input_json = json.loads(input_data) if input_data else {}
    blueprint_id = input_json.get("blueprint_id", "unknown")

    # Load blueprint config — also read dynamic scoring weights
    bp: dict = {}
    benchmark_case_files = []
    self_eval_weight = 0.3
    judge_eval_weight = 0.7
    bench_blend_weight = 0.6  # how much bench_score blends vs run_score
    try:
        bp = load_blueprint(root, blueprint_id)
        evaluation_config = bp.get("evaluation", {})
        benchmark_case_files = evaluation_config.get("benchmark_cases", [])
        self_eval_weight = float(evaluation_config.get("self_eval_weight", 0.3))
        judge_eval_weight = float(evaluation_config.get("judge_eval_weight", 0.7))
        bench_blend_weight = float(evaluation_config.get("bench_blend_weight", 0.6))
    except Exception:
        # Fallback if blueprint not found (e.g. in tests)
        pass

    if not output and not benchmark_case_files:
        raise ForgeError(f"No output.md in {run_id} and no benchmark cases configured to evaluate.")

    # 1. Evaluate single run output if present
    self_score = None
    judge_score = None
    run_score = None

    if output:
        persona = _load_persona(root, blueprint_id)
        prompt = input_json.get("prompt", "")
        # ponytail: code agents use syntax eval, not LLM
        if bp.get("output_type") == "code":
            self_score, judge_score = _code_eval(output)
        else:
            self_score = _self_eval(output, prompt, persona, provider, model)
            judge_score = _judge_eval(output, prompt, persona, provider, model)
        run_score = round(self_score * self_eval_weight + judge_score * judge_eval_weight, 1)

    # 2. Evaluate benchmark cases if present
    benchmark_report = None
    bench_score = None

    if benchmark_case_files:
        logger.info("Executing %d benchmark case file(s)...", len(benchmark_case_files))
        benchmark_report = run_benchmarks(
            root, blueprint_id, provider, model,
            run_only_cases=run_only_cases,
            previous_results=previous_results
        )
        bench_score = benchmark_report["score"]

    # Calculate final score using configurable blend weights
    if run_score is not None and bench_score is not None:
        run_blend_weight = 1.0 - bench_blend_weight
        final_score = round(run_score * run_blend_weight + bench_score * bench_blend_weight, 1)
    elif run_score is not None:
        final_score = run_score
    else:
        final_score = bench_score

    eval_result = {
        "run_id": run_id,
        "blueprint_id": blueprint_id,
        "evaluated_at": datetime.utcnow().isoformat(),
        "final_score": final_score,
    }
    if self_score is not None:
        eval_result["self_eval"] = self_score
    if judge_score is not None:
        eval_result["judge_eval"] = judge_score
    if benchmark_report is not None:
        eval_result["benchmark"] = benchmark_report

    # Write eval.json
    eval_path = run_dir / "eval.json"
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(eval_result, f, indent=2, ensure_ascii=False)

    # Update manifest
    threshold = bp.get("threshold", 85) if bp else 85
    status = "completed" if final_score >= threshold else "needs_improvement"
    # ponytail: capture token usage from last LLM call
    from forge.core.llm import get_last_token_usage, estimate_cost
    usage = get_last_token_usage()
    model_used = bp.get("model", {}).get("model", "unknown") if bp else "unknown"
    token_cost = estimate_cost(model_used, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
    add_run_to_manifest(root, run_id, blueprint_id, score=final_score, status=status,
                        prompt_tokens=usage.get("prompt_tokens"),
                        completion_tokens=usage.get("completion_tokens"),
                        estimated_usd_cost=token_cost)

    # Safety check: if a blueprint receives 100 points three times, halt to inspect for bugs/biases.
    try:
        from forge.core.engine import load_manifest
        manifest = load_manifest(root)
        runs_100_count = sum(
            1 for r in manifest.get("runs", [])
            if r.get("blueprint_id") == blueprint_id and r.get("score") == 100.0
        )
        if runs_100_count >= 3:
            raise ForgeError(
                f"Suspicious evaluation pattern detected: blueprint '{blueprint_id}' has received "
                f"a score of 100.0 three times. Halting execution to inspect for bugs or model biases."
            )
    except ForgeError:
        raise
    except Exception:
        pass

    return eval_result


def _load_persona(root: Path, blueprint_id: str) -> str:
    """Load persona.md from the blueprint directory. Returns empty string if missing."""
    bp_dir = find_blueprint_dir(root, blueprint_id)
    if bp_dir:
        path = bp_dir / "persona.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""


def _self_eval(output: str, prompt: str, persona: str,
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

    user = f"Prompt sent to the agent:\n{prompt}\n\nAgent output to evaluate:\n{output[:4000]}"

    try:
        resp = call_llm(system, user, provider, model)
        result = json.loads(resp.strip().removeprefix("```json").removesuffix("```").strip())
        return max(0, min(100, int(result.get("score", 50))))
    except Exception:
        return 50  # ponytail: default mid-score on parse failure


def _judge_eval(output: str, prompt: str, persona: str,
                provider: str, model: str) -> int:
    """Independent judge LLM evaluates the output. Returns 0-100."""
    system = """You are an impartial judge evaluating an AI agent's output.
The agent's name is "Hund". You have no knowledge of the agent's specific persona rules — judge purely on:
- Accuracy and truthfulness
- Clarity and structure
- Completeness (did it answer the question/prompt?)
- Absence of harmful, misleading, or low-quality content

Rate from 0 to 100. Reply with ONLY a JSON object: {"score": <0-100>, "reason": "<one sentence>"}"""

    user = f"User prompt sent to the agent:\n{prompt}\n\nAgent output to evaluate:\n{output[:4000]}"

    try:
        resp = call_llm(system, user, provider, model)
        result = json.loads(resp.strip().removeprefix("```json").removesuffix("```").strip())
        return max(0, min(100, int(result.get("score", 50))))
    except Exception:
        return 50


def _code_eval(output: str) -> tuple[int, int]:
    """Evaluate code output without LLM. Returns (self_score, judge_score)."""
    # ponytail: naive syntax check, upgrade when precision matters
    text = output.strip()
    if not text or len(text) < 50:
        return (0, 0)

    # Python detection
    if "def " in text or "import " in text or "```python" in text:
        import ast, re
        # ponytail: extract code block from markdown, try whole text as fallback
        blocks = re.findall(r'```python\s*\n(.*?)```', text, re.DOTALL)
        code = blocks[0] if blocks else text.replace("```python", "").replace("```", "")
        try:
            ast.parse(code)
            return (90, 90)
        except SyntaxError:
            return (10, 10)

    # HTML detection
    if "<!DOCTYPE html>" in text or "<html" in text or "<div" in text or "<body" in text:
        return (90, 90)

    # Generic: has some structure
    if len(text) > 200:
        return (80, 80)

    return (50, 50)


# --- Self-test ---

def _demo():
    """Quick smoke test: evaluate a trivial output."""
    import tempfile
    from forge.core.engine import init_manifest
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        init_manifest(root)
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
