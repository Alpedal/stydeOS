import json
import shutil
from pathlib import Path
import pytest

from forge.core.blueprint import find_blueprint_dir, load_blueprint
from forge.cli.main import _stage_blueprint_to_refinery, _push_to_production_and_archive

def test_find_blueprint_dir_locations(tmp_path):
    # Setup folders
    bp_internal = tmp_path / "blueprints" / "internal" / "bp-1"
    bp_internal.mkdir(parents=True)
    (bp_internal / "blueprint.yaml").write_text("id: bp-1\nversion: 1.0.0\n", encoding="utf-8")

    bp_refinery = tmp_path / "refinery" / "bp-2"
    bp_refinery.mkdir(parents=True)
    (bp_refinery / "blueprint.yaml").write_text("id: bp-2\nversion: 1.0.0\n", encoding="utf-8")

    bp_done = tmp_path / "done-blueprints" / "bp-3"
    bp_done.mkdir(parents=True)
    (bp_done / "blueprint.yaml").write_text("id: bp-3\nversion: 1.0.0\n", encoding="utf-8")

    # Verify discovery
    assert find_blueprint_dir(tmp_path, "bp-1") == bp_internal
    assert find_blueprint_dir(tmp_path, "bp-2") == bp_refinery
    assert find_blueprint_dir(tmp_path, "bp-3") == bp_done
    assert find_blueprint_dir(tmp_path, "non-existent") is None


def test_stage_blueprint_to_refinery(tmp_path, monkeypatch):
    # Mock ROOT in main to point to tmp_path
    import forge.cli.main
    monkeypatch.setattr(forge.cli.main, "ROOT", tmp_path)

    # 1. Start with blueprint in internal
    bp_dir = tmp_path / "blueprints" / "internal" / "test-bp"
    bp_dir.mkdir(parents=True)
    (bp_dir / "blueprint.yaml").write_text("id: test-bp\n", encoding="utf-8")

    _stage_blueprint_to_refinery("test-bp")

    # Should be moved to refinery
    refinery_dir = tmp_path / "refinery" / "test-bp"
    assert refinery_dir.exists()
    assert not bp_dir.exists()
    assert (refinery_dir / "blueprint.yaml").exists()

    # 2. Running stage again when already in refinery should be a no-op
    _stage_blueprint_to_refinery("test-bp")
    assert refinery_dir.exists()


def test_push_to_production_and_archive(tmp_path, monkeypatch):
    import forge.cli.main
    monkeypatch.setattr(forge.cli.main, "ROOT", tmp_path)

    # Setup refinery blueprint
    bp_dir = tmp_path / "refinery" / "my-bp"
    bp_dir.mkdir(parents=True)
    (bp_dir / "blueprint.yaml").write_text("id: my-bp\n", encoding="utf-8")

    # Setup run dir with outputs
    run_dir = tmp_path / "runs" / "run_ok"
    run_dir.mkdir(parents=True)
    (run_dir / "output.md").write_text("Passed output", encoding="utf-8")
    (run_dir / "eval.json").write_text('{"final_score": 90}', encoding="utf-8")

    _push_to_production_and_archive("my-bp", "run_ok")

    # Verify production deployment
    prod_dir = tmp_path / "production" / "my-bp"
    assert prod_dir.exists()
    assert (prod_dir / "output.md").read_text(encoding="utf-8") == "Passed output"
    assert (prod_dir / "eval.json").read_text(encoding="utf-8") == '{"final_score": 90}'

    # Verify archiving
    done_dir = tmp_path / "done-blueprints" / "my-bp"
    assert done_dir.exists()
    assert not bp_dir.exists()
    assert (done_dir / "blueprint.yaml").exists()
