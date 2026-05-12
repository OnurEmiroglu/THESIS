"""Unit tests for resume-mode config validation (B9)."""
from pathlib import Path
import json
import logging
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.run_context import setup_run, _diff_config


def _write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def _close_thesis_logger():
    """Release log file handles so Windows tempdir cleanup can delete run.log."""
    lg = logging.getLogger("thesis")
    for h in list(lg.handlers):
        h.close()
        lg.removeHandler(h)


def _setup_resumable_run(td: Path, original_cfg: dict, run_id: str = "20260101-000000_seed1_test_abc1234"):
    """Create a fake completed run dir with config_snapshot.json."""
    results_root = td / "results"
    run_dir = results_root / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "plots").mkdir()
    snapshot = {**original_cfg, "run_id": run_id}
    _write_json(run_dir / "config_snapshot.json", snapshot)
    return results_root, run_id


def test_resume_with_matching_config_succeeds():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        cfg = {"seed": 1, "market": {"mid0": 100, "tick_size": 0.01}, "episode": {"n_steps": 8000}}
        results_root, run_id = _setup_resumable_run(td, cfg)
        cfg_path = td / "cfg.json"
        _write_json(cfg_path, cfg)
        try:
            ctx = setup_run(cfg_path, results_root=results_root, resume_run_id=run_id)
            assert ctx.run_id == run_id
            assert ctx.resume_run_id == run_id
        finally:
            _close_thesis_logger()


def test_resume_with_mismatched_config_refuses():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        original = {"seed": 1, "market": {"mid0": 100, "tick_size": 0.01}, "episode": {"n_steps": 8000}}
        results_root, run_id = _setup_resumable_run(td, original)
        mismatched = {"seed": 1, "market": {"mid0": 200, "tick_size": 0.01}, "episode": {"n_steps": 8000}}
        cfg_path = td / "cfg.json"
        _write_json(cfg_path, mismatched)
        try:
            try:
                setup_run(cfg_path, results_root=results_root, resume_run_id=run_id)
            except ValueError as exc:
                msg = str(exc)
                assert "Resume config mismatch" in msg, f"unexpected error: {msg}"
                assert "market.mid0" in msg, f"differing key not reported in diff: {msg}"
                assert "100" in msg and "200" in msg, f"old/new values not reported: {msg}"
                assert "resume_force=True" in msg, f"override hint missing: {msg}"
            else:
                raise AssertionError("expected ValueError on mismatched resume config")
        finally:
            _close_thesis_logger()


def test_resume_with_mismatched_config_force_proceeds():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        original = {"seed": 1, "market": {"mid0": 100, "tick_size": 0.01}, "episode": {"n_steps": 8000}}
        results_root, run_id = _setup_resumable_run(td, original)
        mismatched = {"seed": 1, "market": {"mid0": 200, "tick_size": 0.01}, "episode": {"n_steps": 8000}}
        cfg_path = td / "cfg.json"
        _write_json(cfg_path, mismatched)
        try:
            ctx = setup_run(
                cfg_path,
                results_root=results_root,
                resume_run_id=run_id,
                resume_force=True,
            )
            assert ctx.run_id == run_id
        finally:
            _close_thesis_logger()


def test_resume_with_missing_snapshot_proceeds():
    """Legacy runs predating snapshot saving must remain resumable."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        cfg = {"seed": 1, "market": {"mid0": 100, "tick_size": 0.01}, "episode": {"n_steps": 8000}}
        results_root = td / "results"
        run_id = "20260101-000000_seed1_legacy_xyz9876"
        run_dir = results_root / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "plots").mkdir()
        # NOTE: no config_snapshot.json
        cfg_path = td / "cfg.json"
        _write_json(cfg_path, cfg)
        try:
            ctx = setup_run(cfg_path, results_root=results_root, resume_run_id=run_id)
            assert ctx.run_id == run_id
        finally:
            _close_thesis_logger()


def test_diff_config_finds_nested_keys():
    a = {"x": 1, "nested": {"y": 2, "z": 3}}
    b = {"x": 1, "nested": {"y": 2, "z": 4}}
    diffs = _diff_config(a, b)
    assert any("nested.z" in d for d in diffs), f"nested key not found: {diffs}"
    assert any("3" in d and "4" in d for d in diffs), f"values not in diff: {diffs}"


if __name__ == "__main__":
    test_resume_with_matching_config_succeeds()
    test_resume_with_mismatched_config_refuses()
    test_resume_with_mismatched_config_force_proceeds()
    test_resume_with_missing_snapshot_proceeds()
    test_diff_config_finds_nested_keys()
    print("Resume validation tests passed (5/5)")
