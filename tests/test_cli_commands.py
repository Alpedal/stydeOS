import os
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import forge.cli.main
from forge.cli.main import (
    cmd_status, cmd_stage, cmd_archive, cmd_cache_stats, cmd_cache
)

def test_cmd_status_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(forge.cli.main, "ROOT", tmp_path)
    
    cmd_status()
    captured = capsys.readouterr().out
    assert "Forge Blueprint Lifecycle Status" in captured
    assert "no active blueprints in refinery" in captured
    assert "no blueprints archived as done" in captured
    assert "no original blueprints left" in captured


def test_cmd_status_with_data(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(forge.cli.main, "ROOT", tmp_path)

    # 1. Setup refinery blueprint
    bp_ref = tmp_path / "refinery" / "bp-ref"
    bp_ref.mkdir(parents=True)
    (bp_ref / "blueprint.yaml").write_text("id: bp-ref\nversion: 1.0.2\n", encoding="utf-8")

    # 2. Setup done blueprint
    bp_done = tmp_path / "done-blueprints" / "bp-done"
    bp_done.mkdir(parents=True)
    (bp_done / "blueprint.yaml").write_text("id: bp-done\nversion: 2.1.0\n", encoding="utf-8")

    # 3. Setup original blueprint
    bp_orig = tmp_path / "blueprints" / "internal" / "bp-orig"
    bp_orig.mkdir(parents=True)
    (bp_orig / "blueprint.yaml").write_text("id: bp-orig\nversion: 0.1.0\n", encoding="utf-8")

    # 4. Setup manifest with run info
    manifest_data = {
        "version": "2.0.0",
        "codename": "Crucible",
        "runs": [
            {
                "run_id": "run_1",
                "blueprint_id": "bp-ref",
                "score": 75.0,
                "status": "needs_improvement"
            }
        ]
    }
    (tmp_path / "forge.json").write_text(json.dumps(manifest_data), encoding="utf-8")

    cmd_status()
    captured = capsys.readouterr().out
    assert "bp-ref (v1.0.2)" in captured
    assert "Latest: 75.0/100 (needs_improvement)" in captured
    assert "bp-done (v2.1.0)" in captured
    assert "bp-orig (v0.1.0)" in captured


def test_cmd_stage_manual(tmp_path, monkeypatch):
    monkeypatch.setattr(forge.cli.main, "ROOT", tmp_path)

    bp_orig = tmp_path / "blueprints" / "internal" / "my-bp"
    bp_orig.mkdir(parents=True)
    (bp_orig / "blueprint.yaml").write_text("id: my-bp\n", encoding="utf-8")

    cmd_stage("my-bp")
    
    assert (tmp_path / "refinery" / "my-bp").exists()
    assert not bp_orig.exists()


def test_cmd_archive_manual(tmp_path, monkeypatch):
    monkeypatch.setattr(forge.cli.main, "ROOT", tmp_path)

    bp_ref = tmp_path / "refinery" / "my-bp"
    bp_ref.mkdir(parents=True)
    (bp_ref / "blueprint.yaml").write_text("id: my-bp\n", encoding="utf-8")

    run_dir = tmp_path / "runs" / "run_test"
    run_dir.mkdir(parents=True)
    (run_dir / "output.md").write_text("success", encoding="utf-8")
    (run_dir / "eval.json").write_text("{}", encoding="utf-8")

    cmd_archive("my-bp", "run_test")

    assert (tmp_path / "production" / "my-bp" / "output.md").exists()
    assert (tmp_path / "done-blueprints" / "my-bp").exists()


def test_cmd_cache_stats_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(forge.cli.main, "ROOT", tmp_path)
    
    cmd_cache_stats()
    captured = capsys.readouterr().out
    assert "Cache stats: .forge_cache directory does not exist yet." in captured


def test_cmd_cache_stats_populated(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(forge.cli.main, "ROOT", tmp_path)

    cache_dir = tmp_path / ".forge_cache"
    cache_dir.mkdir()
    (cache_dir / "q1.json").write_text("test content 1", encoding="utf-8")
    (cache_dir / "q2.json").write_text("test content 222", encoding="utf-8")

    cmd_cache_stats()
    captured = capsys.readouterr().out
    assert "Total Cached Queries:  2" in captured
    assert "Total Cache Size:" in captured
