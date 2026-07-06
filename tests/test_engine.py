"""Tests for forge.core.engine — manifest I/O and run directory management."""

import json
import tempfile
from pathlib import Path
import pytest

from forge.core.engine import (
    init_manifest, load_manifest, save_manifest,
    create_run_dir, load_run_data, add_run_to_manifest,
    list_runs, ForgeError,
)


@pytest.fixture
def tmp_root(tmp_path):
    """Create a temporary forge root with an initialized manifest."""
    init_manifest(tmp_path)
    return tmp_path


class TestManifest:
    def test_init_creates_forge_json(self, tmp_root):
        assert (tmp_root / "forge.json").exists()

    def test_init_has_expected_keys(self, tmp_root):
        data = load_manifest(tmp_root)
        assert data["version"] == "2.0.0"
        assert "runs" in data
        assert "blueprints" in data

    def test_load_missing_raises(self, tmp_path):
        with pytest.raises(ForgeError, match="forge.json not found"):
            load_manifest(tmp_path)

    def test_save_and_reload(self, tmp_root):
        data = load_manifest(tmp_root)
        data["test_key"] = "test_value"
        save_manifest(tmp_root, data)
        reloaded = load_manifest(tmp_root)
        assert reloaded["test_key"] == "test_value"

    def test_atomic_write(self, tmp_root):
        """Ensure no .tmp file is left after save."""
        data = load_manifest(tmp_root)
        save_manifest(tmp_root, data)
        assert not (tmp_root / "forge.json.tmp").exists()


class TestRunDir:
    def test_create_run_dir_structure(self, tmp_root):
        run_dir = create_run_dir(tmp_root, "test-blueprint")
        assert run_dir.exists()
        assert (run_dir / "input.json").exists()

    def test_create_run_dir_input_json(self, tmp_root):
        run_dir = create_run_dir(tmp_root, "test-blueprint")
        data = json.loads((run_dir / "input.json").read_text())
        assert data["blueprint_id"] == "test-blueprint"
        assert "run_id" in data
        assert "started_at" in data

    def test_run_id_format(self, tmp_root):
        run_dir = create_run_dir(tmp_root, "bp")
        assert run_dir.name.startswith("run_")

    def test_load_run_data_missing_files_are_none(self, tmp_root):
        run_dir = create_run_dir(tmp_root, "bp")
        data = load_run_data(run_dir)
        assert data["output"] is None
        assert data["eval"] is None
        assert data["feedback"] is None

    def test_load_run_data_reads_input(self, tmp_root):
        run_dir = create_run_dir(tmp_root, "bp")
        data = load_run_data(run_dir)
        assert data["input"] is not None
        parsed = json.loads(data["input"])
        assert parsed["blueprint_id"] == "bp"

    def test_load_run_data_reads_output(self, tmp_root):
        run_dir = create_run_dir(tmp_root, "bp")
        (run_dir / "output.md").write_text("Hello world", encoding="utf-8")
        data = load_run_data(run_dir)
        assert data["output"] == "Hello world"


class TestManifestRunTracking:
    def test_add_run_appears_in_list(self, tmp_root):
        create_run_dir(tmp_root, "bp")
        add_run_to_manifest(tmp_root, "run_test001", "bp", score=75.0, status="completed")
        runs = list_runs(tmp_root)
        ids = [r["run_id"] for r in runs]
        assert "run_test001" in ids

    def test_update_existing_run(self, tmp_root):
        add_run_to_manifest(tmp_root, "run_x", "bp", score=50.0, status="running")
        add_run_to_manifest(tmp_root, "run_x", "bp", score=90.0, status="completed")
        runs = list_runs(tmp_root)
        entry = next(r for r in runs if r["run_id"] == "run_x")
        assert entry["score"] == 90.0
        assert entry["status"] == "completed"

    def test_list_runs_newest_first(self, tmp_root):
        add_run_to_manifest(tmp_root, "run_20260101-000000", "bp")
        add_run_to_manifest(tmp_root, "run_20260102-000000", "bp")
        runs = list_runs(tmp_root)
        assert runs[0]["run_id"] == "run_20260102-000000"
