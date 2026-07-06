"""Tests for forge.core.spawner — output generation and benchmark execution.

All LLM calls are mocked so no API keys are needed.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from forge.core.engine import init_manifest, create_run_dir, ForgeError


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_blueprint(tmp_path: Path, blueprint_id: str = "test-bp",
                    provider: str = "openai", model: str = "gpt-4o") -> Path:
    bp_dir = tmp_path / "blueprints" / "internal" / blueprint_id
    bp_dir.mkdir(parents=True)
    (bp_dir / "blueprint.yaml").write_text(
        f"id: {blueprint_id}\nname: Test\nversion: 1.0.0\n"
        f"model:\n  provider: {provider}\n  model: {model}\n"
        "evaluation:\n  benchmark_cases: []\n",
        encoding="utf-8"
    )
    (bp_dir / "persona.md").write_text("You are a test agent.", encoding="utf-8")
    return bp_dir


def _make_benchmark_case_file(tmp_path: Path) -> str:
    """Create a benchmark case file and return its relative path."""
    cases_dir = tmp_path / "benchmarks" / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    case_file = cases_dir / "test-cases.json"
    case_file.write_text(json.dumps({
        "cases": [
            {
                "id": "case_001",
                "prompt": "Say hello",
                "expected_keywords": ["Hund"],
                "forbidden_keywords": ["sorry"],
                "rules_to_check": [],
            },
            {
                "id": "case_002",
                "prompt": "Who are you?",
                "expected_keywords": ["Hund", "AI"],
                "forbidden_keywords": [],
                "rules_to_check": [],
            },
        ]
    }), encoding="utf-8")
    return "benchmarks/cases/test-cases.json"


# ── tests ─────────────────────────────────────────────────────────────────────

class TestGenerateOutput:
    def test_raises_if_run_dir_missing(self, tmp_path):
        from forge.core.spawner import generate_output
        init_manifest(tmp_path)
        with pytest.raises(ForgeError, match="Run directory not found"):
            generate_output(tmp_path, "run_nonexistent")

    def test_raises_if_no_prompt(self, tmp_path):
        from forge.core.spawner import generate_output
        init_manifest(tmp_path)
        _make_blueprint(tmp_path)
        run_dir = create_run_dir(tmp_path, "test-bp")
        # Remove prompt from input.json
        input_path = run_dir / "input.json"
        data = json.loads(input_path.read_text(encoding="utf-8"))
        if "prompt" in data:
            del data["prompt"]
        input_path.write_text(json.dumps(data), encoding="utf-8")

        # input.json exists but has no 'prompt' key — should raise
        with pytest.raises(ForgeError, match="No prompt field"):
            generate_output(tmp_path, run_dir.name)

    def test_returns_existing_output(self, tmp_path):
        from forge.core.spawner import generate_output
        init_manifest(tmp_path)
        _make_blueprint(tmp_path)
        run_dir = create_run_dir(tmp_path, "test-bp")
        (run_dir / "output.md").write_text("cached output", encoding="utf-8")
        result = generate_output(tmp_path, run_dir.name)
        assert result == "cached output"

    @patch("forge.core.spawner.call_llm", return_value="Hej, jag ar Hund AI!")
    def test_generates_and_saves_output(self, mock_llm, tmp_path):
        from forge.core.spawner import generate_output
        init_manifest(tmp_path)
        _make_blueprint(tmp_path)
        run_dir = create_run_dir(tmp_path, "test-bp")
        # Add a prompt to input.json
        input_data = json.loads((run_dir / "input.json").read_text())
        input_data["prompt"] = "Hej!"
        (run_dir / "input.json").write_text(json.dumps(input_data), encoding="utf-8")

        result = generate_output(tmp_path, run_dir.name)
        assert "Hund" in result
        assert (run_dir / "output.md").exists()


class TestRunBenchmarks:
    @patch("forge.core.spawner.call_llm", return_value="Jag ar Hund AI, din assistent!")
    def test_runs_all_cases(self, mock_llm, tmp_path):
        from forge.core.spawner import run_benchmarks
        init_manifest(tmp_path)
        case_rel = _make_benchmark_case_file(tmp_path)

        bp_dir = _make_blueprint(tmp_path)
        # Update blueprint to reference the case file
        bp_yaml = bp_dir / "blueprint.yaml"
        content = bp_yaml.read_text(encoding="utf-8").replace(
            "benchmark_cases: []",
            f"benchmark_cases:\n  - {case_rel}"
        )
        bp_yaml.write_text(content, encoding="utf-8")

        report = run_benchmarks(tmp_path, "test-bp")
        assert report["cases_run"] == 2
        assert 0.0 <= report["score"] <= 100.0
        assert len(report["results"]) == 2

    def test_returns_zero_for_empty_suite(self, tmp_path):
        from forge.core.spawner import run_benchmarks
        init_manifest(tmp_path)
        _make_blueprint(tmp_path)
        report = run_benchmarks(tmp_path, "test-bp")
        assert report["cases_run"] == 0
        assert report["score"] == 0.0

    @patch("forge.core.spawner.call_llm", return_value="Hund AI rapporterar: allt ar bra!")
    def test_keyword_scoring(self, mock_llm, tmp_path):
        from forge.core.spawner import run_benchmarks
        init_manifest(tmp_path)
        case_rel = _make_benchmark_case_file(tmp_path)
        bp_dir = _make_blueprint(tmp_path)
        bp_yaml = bp_dir / "blueprint.yaml"
        content = bp_yaml.read_text(encoding="utf-8").replace(
            "benchmark_cases: []",
            f"benchmark_cases:\n  - {case_rel}"
        )
        bp_yaml.write_text(content, encoding="utf-8")

        report = run_benchmarks(tmp_path, "test-bp")
        # "Hund" is in expected_keywords for case_001 and mock response contains it
        case_001 = next(r for r in report["results"] if r["id"] == "case_001")
        assert case_001["score"] > 0.0, f"Expected score > 0, got: {case_001}"

    @patch("forge.core.spawner.call_llm", return_value="Hund AI.")
    def test_incremental_execution(self, mock_llm, tmp_path):
        from forge.core.spawner import run_benchmarks
        init_manifest(tmp_path)
        case_rel = _make_benchmark_case_file(tmp_path)
        bp_dir = _make_blueprint(tmp_path)
        bp_yaml = bp_dir / "blueprint.yaml"
        content = bp_yaml.read_text(encoding="utf-8").replace(
            "benchmark_cases: []",
            f"benchmark_cases:\n  - {case_rel}"
        )
        bp_yaml.write_text(content, encoding="utf-8")

        # Mock previous results
        previous_results = [
            {"id": "case_001", "score": 90.0, "output": "Old output"},
            {"id": "case_002", "score": 40.0, "output": "Old failed output"}
        ]

        # Only run case_002, reuse case_001
        report = run_benchmarks(
            tmp_path, "test-bp",
            run_only_cases=["case_002"],
            previous_results=previous_results
        )

        assert report["cases_run"] == 2
        # case_001 was reused
        c1 = next(r for r in report["results"] if r["id"] == "case_001")
        assert c1["score"] == 90.0
        assert c1["output"] == "Old output"

        # case_002 was run (mock returned "Hund AI." -> expected keywords matched -> score changed)
        c2 = next(r for r in report["results"] if r["id"] == "case_002")
        assert c2["score"] > 40.0
