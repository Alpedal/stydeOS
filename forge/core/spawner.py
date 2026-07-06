"""Forge v2 spawner — generate run output and execute benchmark cases.
"""

import importlib.util
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from forge.core.engine import (
    load_run_data, load_blueprint, ForgeError,
)
from forge.core.blueprint import find_blueprint_dir
from forge.core.llm import call_llm

logger = logging.getLogger("forge.core.spawner")

MAX_TOOL_TURNS = 5  # ponytail: prevent infinite tool-call loops


def _load_tools(root: Path, blueprint_id: str) -> list:
    """Load tools.yaml from the blueprint directory and return a list of tool dicts."""
    try:
        import yaml
    except ImportError:
        return []
    bp_dir = find_blueprint_dir(root, blueprint_id)
    if bp_dir:
        path = bp_dir / "tools.yaml"
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            return data.get("tools", []) if isinstance(data, dict) else []
    return []


def _load_mock_responses(root: Path, blueprint_id: str) -> dict:
    """Load mock_responses.yaml from the blueprint directory."""
    try:
        import yaml
    except ImportError:
        return {}
    bp_dir = find_blueprint_dir(root, blueprint_id)
    if bp_dir:
        path = bp_dir / "mock_responses.yaml"
        if path.exists():
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    return {}


def _lookup_mock_response(mocks: dict, tool_name: str, arguments: dict) -> str:
    """Look up a mock response. Returns tool invocation stub if no match."""
    tool_mocks = mocks.get(tool_name, {})
    if tool_mocks:
        # Try to match a key from arguments (e.g. agent_id value), fall back to "default"
        for arg_val in arguments.values():
            if isinstance(arg_val, str) and arg_val in tool_mocks:
                return tool_mocks[arg_val]
        if "default" in tool_mocks:
            return tool_mocks["default"]
    return json.dumps({"tool": tool_name, "args": arguments, "status": "ok"})


def _load_tools_impl(root: Path, blueprint_id: str):
    """Dynamically load tools_impl.py from a blueprint directory.
    Returns the loaded module, or None if the file does not exist."""
    bp_dir = find_blueprint_dir(root, blueprint_id)
    if bp_dir:
        impl_path = bp_dir / "tools_impl.py"
        if impl_path.exists():
            spec = importlib.util.spec_from_file_location(f"forge.tools.{blueprint_id}", impl_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            logger.info("Loaded tools_impl.py for blueprint '%s'", blueprint_id)
            return mod
    return None


def _execute_tool(tool_name: str, arguments: dict,
                  impl_module, mocks: dict) -> str:
    """Execute a tool call: prefer tools_impl.py function, fall back to mock_responses.yaml."""
    if impl_module is not None:
        fn = getattr(impl_module, tool_name, None)
        if fn is not None:
            try:
                result = fn(**arguments)
                logger.info("Tool '%s' executed via tools_impl.py", tool_name)
                return str(result)
            except Exception as e:
                logger.warning("tools_impl.%s raised %s — falling back to mock", tool_name, e)

    # Fallback: mock_responses.yaml
    return _lookup_mock_response(mocks, tool_name, arguments)


def _call_with_tools(persona: str, prompt: str, provider: str, model: str,
                     tools: list, mocks: dict,
                     impl_module=None,
                     temperature: Optional[float] = None,
                     max_tokens: Optional[int] = None,
                     top_p: Optional[float] = None) -> str:
    """Run a multi-turn conversation loop that executes tool calls until text is returned.

    Prefers tools_impl.py for execution; falls back to mock_responses.yaml.
    """
    messages = [{"role": "user", "content": prompt}]
    system = persona

    for _ in range(MAX_TOOL_TURNS):
        result = call_llm(
            system,
            messages[-1]["content"],
            provider,
            model,
            tools=tools if tools else None,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )

        if isinstance(result, dict) and "tool_call" in result:
            tc = result["tool_call"]
            tool_name = tc["name"]
            arguments = tc.get("arguments", {})
            tool_response = _execute_tool(tool_name, arguments, impl_module, mocks)
            logger.info("Tool call: %s(%s) -> dispatched", tool_name, arguments)
            messages.append({"role": "assistant", "content": f"[Tool call: {tool_name}]"})
            messages.append({"role": "user", "content": f"Tool result for {tool_name}:\n{tool_response}"})
        else:
            return result if isinstance(result, str) else str(result)

    logger.warning("MAX_TOOL_TURNS (%d) reached without a final text response.", MAX_TOOL_TURNS)
    return "(Error: max tool turns reached without final text response)"


def generate_output(root: Path, run_id: str,
                    provider: Optional[str] = None,
                    model: Optional[str] = None) -> str:
    """Generate output.md for a run if input.json has a prompt and output.md is missing.
    
    If output.md already exists, returns its content.
    """
    run_dir = root / "runs" / run_id
    if not run_dir.exists():
        raise ForgeError(f"Run directory not found: {run_id}")

    data = load_run_data(run_dir)
    output = data.get("output")
    if output:
        return output

    # Check input.json
    input_raw = data.get("input")
    if not input_raw:
        raise ForgeError(f"input.json missing in run {run_id}")

    input_data = json.loads(input_raw)
    prompt = input_data.get("prompt")
    if not prompt:
        raise ForgeError(f"No prompt field found in runs/{run_id}/input.json to spawn output.")

    blueprint_id = input_data.get("blueprint_id")
    if not blueprint_id:
        raise ForgeError(f"No blueprint_id field found in runs/{run_id}/input.json")

    # Load blueprint configuration
    bp = load_blueprint(root, blueprint_id)
    bp_model_config = bp.get("model", {})
    
    final_provider = provider or bp_model_config.get("provider", "openai")
    final_model = model or bp_model_config.get("model", "gpt-4o")

    # Load persona, tools, mock responses and dynamic impl
    persona = _load_persona(root, blueprint_id)
    tools = _load_tools(root, blueprint_id)
    mocks = _load_mock_responses(root, blueprint_id)
    impl_module = _load_tools_impl(root, blueprint_id)

    # Extract model configurations
    temperature = bp_model_config.get("temperature")
    max_tokens = bp_model_config.get("max_tokens")
    top_p = bp_model_config.get("top_p")

    logger.info("Generating output for %s using %s/%s...", run_id, final_provider, final_model)
    output_text = _call_with_tools(
        persona, prompt, final_provider, final_model, tools, mocks, impl_module,
        temperature=temperature, max_tokens=max_tokens, top_p=top_p
    )

    # Save to output.md
    with open(run_dir / "output.md", "w", encoding="utf-8") as f:
        f.write(output_text)

    return output_text


def _run_single_case(case: dict, persona: str, final_provider: str, final_model: str,
                     tools: Optional[list] = None, mocks: Optional[dict] = None,
                     impl_module=None,
                     temperature: Optional[float] = None,
                     max_tokens: Optional[int] = None,
                     top_p: Optional[float] = None,
                     delay: float = 0.0) -> dict:
    """Execute and grade a single benchmark case. Designed to be called in a thread."""
    case_id = case.get("id", "unknown")
    prompt = case.get("prompt", "")
    expected_keywords = case.get("expected_keywords", [])
    forbidden_keywords = case.get("forbidden_keywords", [])
    rules_to_check = case.get("rules_to_check", [])
    tools = tools or []
    mocks = mocks or {}

    if delay > 0.0:
        logger.info("Staggering case '%s' start: sleeping for %.2fs", case_id, delay)
        time.sleep(delay)

    logger.info("Running benchmark case '%s'...", case_id)
    try:
        output = _call_with_tools(
            persona, prompt, final_provider, final_model, tools, mocks, impl_module,
            temperature=temperature, max_tokens=max_tokens, top_p=top_p
        )
    except Exception as e:
        logger.error("Error executing case '%s': %s", case_id, e)
        return {
            "id": case_id,
            "score": 0.0,
            "error": str(e),
            "output": ""
        }

    # Grade expected keywords
    expected_found = [kw for kw in expected_keywords if kw in output]
    expected_missing = [kw for kw in expected_keywords if kw not in output]
    expected_score = (len(expected_found) / len(expected_keywords)) * 100.0 if expected_keywords else 100.0

    # Grade forbidden keywords (penalty: -25 pts per keyword)
    forbidden_found = [kw for kw in forbidden_keywords if kw in output]
    keyword_score = max(0.0, expected_score - len(forbidden_found) * 25.0)

    # Grade rules via LLM Judge (parallel with agent call above)
    llm_rules_score = 50.0
    reason = "No rules specified or LLM judge skipped."
    if rules_to_check:
        rules_str = ", ".join(rules_to_check)
        judge_system = (
            "You are a strict evaluation judge. "
            "Grade the AI response based on how well it follows these specific persona rules:\n"
            f"Rules: {rules_str}\n\n"
            "Refer to the original persona definitions if helpful:\n"
            f"{persona}\n\n"
            "Answer with ONLY a JSON object: {\"score\": <0-100>, \"reason\": \"<one sentence>\"}"
        )
        judge_user = (
            f"Prompt sent to the agent:\n{prompt}\n\n"
            f"Agent response:\n{output}"
        )
        try:
            judge_resp = call_llm(judge_system, judge_user, final_provider, final_model)
            res = json.loads(judge_resp.strip().removeprefix("```json").removesuffix("```").strip())
            llm_rules_score = max(0.0, min(100.0, float(res.get("score", 50.0))))
            reason = res.get("reason", "Graded by judge.")
        except Exception as e:
            reason = f"Judge parsing failed: {e}"

    case_score = round(0.5 * keyword_score + 0.5 * llm_rules_score, 1)

    return {
        "id": case_id,
        "score": case_score,
        "keyword_score": keyword_score,
        "llm_rules_score": llm_rules_score,
        "expected_found": expected_found,
        "expected_missing": expected_missing,
        "forbidden_found": forbidden_found,
        "reason": reason,
        "output": output
    }


def run_benchmarks(root: Path, blueprint_id: str,
                   provider: Optional[str] = None,
                   model: Optional[str] = None,
                   run_only_cases: Optional[list[str]] = None,
                   previous_results: Optional[list[dict]] = None) -> dict:
    """Run benchmark cases in parallel (or incrementally) and return the aggregated report."""
    bp = load_blueprint(root, blueprint_id)
    bp_model_config = bp.get("model", {})
    final_provider = provider or bp_model_config.get("provider", "openai")
    final_model = model or bp_model_config.get("model", "gpt-4o")
    
    evaluation_config = bp.get("evaluation", {})
    benchmark_case_files = evaluation_config.get("benchmark_cases", [])
    
    persona = _load_persona(root, blueprint_id)
    tools = _load_tools(root, blueprint_id)
    mocks = _load_mock_responses(root, blueprint_id)
    impl_module = _load_tools_impl(root, blueprint_id)

    # Collect all cases from all case files
    all_cases: list[dict] = []
    for case_file_rel in benchmark_case_files:
        case_file = root / case_file_rel
        if not case_file.exists():
            logger.warning("Benchmark case file not found at %s", case_file)
            continue
        with open(case_file, "r", encoding="utf-8") as f:
            case_data = json.load(f)
        all_cases.extend(case_data.get("cases", []))

    if not all_cases:
        return {"blueprint_id": blueprint_id, "cases_run": 0, "score": 0.0, "results": []}

    # Extract model configurations
    temperature = bp_model_config.get("temperature")
    max_tokens = bp_model_config.get("max_tokens")
    top_p = bp_model_config.get("top_p")
    rate_limit_delay = float(evaluation_config.get("rate_limit_delay", 0.0))

    # Filter cases to run incrementally
    cases_to_run = all_cases
    if run_only_cases is not None:
        cases_to_run = [c for c in all_cases if c.get("id") in run_only_cases]

    case_results: list[dict] = [{}] * len(all_cases)
    case_id_to_idx = {c.get("id"): idx for idx, c in enumerate(all_cases)}

    # Pre-populate with previous results for skipped cases
    if previous_results:
        prev_map = {r.get("id"): r for r in previous_results}
        for c in all_cases:
            cid = c.get("id")
            if run_only_cases is not None and cid not in run_only_cases:
                idx = case_id_to_idx[cid]
                case_results[idx] = prev_map.get(cid, {"id": cid, "score": 0.0, "error": "Skipped (incremental run)"})

    # Run remaining cases in parallel (max_workers capped at number of cases to avoid waste)
    max_workers = min(5, len(cases_to_run)) if cases_to_run else 1

    if cases_to_run:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(
                    _run_single_case, case, persona, final_provider, final_model, tools, mocks, impl_module,
                    temperature=temperature, max_tokens=max_tokens, top_p=top_p,
                    delay=idx * rate_limit_delay
                ): case_id_to_idx[case.get("id")]
                for idx, case in enumerate(cases_to_run)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    case_results[idx] = future.result()
                except Exception as exc:
                    case_id = all_cases[idx].get("id", f"case_{idx}")
                    logger.error("Case '%s' raised an exception: %s", case_id, exc)
                    case_results[idx] = {"id": case_id, "score": 0.0, "error": str(exc), "output": ""}

    total_score = sum(r.get("score", 0.0) for r in case_results)
    avg_score = round(total_score / len(case_results), 1) if case_results else 0.0

    return {
        "blueprint_id": blueprint_id,
        "cases_run": len(case_results),
        "score": avg_score,
        "results": case_results
    }



def _load_persona(root: Path, blueprint_id: str) -> str:
    bp_dir = find_blueprint_dir(root, blueprint_id)
    if bp_dir:
        path = bp_dir / "persona.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
    return ""
