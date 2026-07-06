"""Tests for forge.core.teacher — version bumping and feedback generation.

All LLM calls are mocked so no API keys are needed.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from forge.core.engine import init_manifest, create_run_dir
from forge.core.teacher import _bump_version, _apply_blueprint_patches


class TestBumpVersion:
    def test_patch_bump(self):
        assert _bump_version("1.0.2") == "1.0.3"

    def test_bump_from_zero(self):
        assert _bump_version("1.0.0") == "1.0.1"

    def test_bump_with_pre_release(self):
        assert _bump_version("1.0.2-beta") == "1.0.3-beta"

    def test_bump_with_build_metadata(self):
        assert _bump_version("2.3.4-beta.1") == "2.3.5-beta.1"

    def test_bump_large_patch(self):
        assert _bump_version("0.0.99") == "0.0.100"

    def test_invalid_version_raises(self):
        with pytest.raises(ValueError):
            _bump_version("not-a-version")

    def test_major_minor_only_raises(self):
        with pytest.raises(ValueError):
            _bump_version("1.2")


class TestApplyBlueprintPatches:
    def _setup_blueprint(self, tmp_path: Path, version: str = "1.0.0") -> Path:
        bp_dir = tmp_path / "blueprints" / "internal" / "test-bp"
        bp_dir.mkdir(parents=True)
        (bp_dir / "blueprint.yaml").write_text(
            f"# comment preserved\nid: test-bp\nversion: {version}\n",
            encoding="utf-8"
        )
        (bp_dir / "persona.md").write_text("Persona content.", encoding="utf-8")
        return bp_dir

    def test_version_bumped(self, tmp_path):
        self._setup_blueprint(tmp_path, "1.0.5")
        patches = _apply_blueprint_patches(tmp_path, "test-bp", "some feedback")
        content = (tmp_path / "blueprints" / "internal" / "test-bp" / "blueprint.yaml").read_text()
        assert "1.0.6" in content
        assert any("Bumped" in p for p in patches)

    def test_comments_preserved(self, tmp_path):
        self._setup_blueprint(tmp_path)
        _apply_blueprint_patches(tmp_path, "test-bp", "feedback")
        content = (tmp_path / "blueprints" / "internal" / "test-bp" / "blueprint.yaml").read_text()
        assert "# comment preserved" in content

    def test_persona_annotated(self, tmp_path):
        self._setup_blueprint(tmp_path)
        _apply_blueprint_patches(tmp_path, "test-bp", "some feedback")
        persona = (tmp_path / "blueprints" / "internal" / "test-bp" / "persona.md").read_text()
        assert "Teacher feedback" in persona

    def test_pre_release_version_bumped(self, tmp_path):
        self._setup_blueprint(tmp_path, "1.0.0-beta")
        _apply_blueprint_patches(tmp_path, "test-bp", "feedback")
        content = (tmp_path / "blueprints" / "internal" / "test-bp" / "blueprint.yaml").read_text()
        assert "1.0.1-beta" in content

    def test_parameters_updated(self, tmp_path):
        bp_dir = tmp_path / "blueprints" / "internal" / "test-bp"
        bp_dir.mkdir(parents=True)
        (bp_dir / "blueprint.yaml").write_text(
            "id: test-bp\nversion: 1.0.0\nmodel:\n  provider: openai\n  model: gpt-4o\n",
            encoding="utf-8"
        )
        (bp_dir / "persona.md").write_text("Persona content.", encoding="utf-8")
        
        feedback = "## Parameter Updates\n[PARAM_UPDATE] temperature: 0.2\n[PARAM_UPDATE] max_tokens: 1000\n"
        patches = _apply_blueprint_patches(tmp_path, "test-bp", feedback)
        
        content = (bp_dir / "blueprint.yaml").read_text(encoding="utf-8")
        assert "temperature: 0.2" in content
        assert "max_tokens: 1000" in content
        assert any("Updated" in p for p in patches)


class TestProposeImprovements:
    @patch("forge.core.teacher.call_llm", return_value="## What Went Wrong\n- test issue")
    def test_propose_generates_feedback(self, mock_llm, tmp_path):
        from forge.core.teacher import propose_improvements
        init_manifest(tmp_path)

        # Setup blueprint
        bp_dir = tmp_path / "blueprints" / "internal" / "bp"
        bp_dir.mkdir(parents=True)
        (bp_dir / "blueprint.yaml").write_text(
            "id: bp\nname: BP\nversion: 1.0.0\n"
            "model:\n  provider: openai\n  model: gpt-4o\n"
            "evaluation:\n  benchmark_cases: []\n",
            encoding="utf-8"
        )
        (bp_dir / "persona.md").write_text("Persona.", encoding="utf-8")

        # Setup run
        run_dir = tmp_path / "runs" / "run_test"
        run_dir.mkdir(parents=True)
        (run_dir / "input.json").write_text(json.dumps({"blueprint_id": "bp"}), encoding="utf-8")
        (run_dir / "output.md").write_text("Bad output.", encoding="utf-8")
        (run_dir / "eval.json").write_text(json.dumps({"final_score": 40}), encoding="utf-8")

        result = propose_improvements(tmp_path, "run_test")
        assert result["status"] == "improved"
        assert (run_dir / "feedback.md").exists()

    def test_score_above_threshold_returns_passed(self, tmp_path):
        from forge.core.teacher import propose_improvements
        run_dir = tmp_path / "runs" / "run_hi"
        run_dir.mkdir(parents=True)
        (run_dir / "input.json").write_text(json.dumps({"blueprint_id": "bp"}), encoding="utf-8")
        (run_dir / "eval.json").write_text(json.dumps({"final_score": 90}), encoding="utf-8")

        result = propose_improvements(tmp_path, "run_hi")
        assert result["status"] == "passed"
