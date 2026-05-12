"""Unit tests for CSVMetricLogger schema enforcement (B8)."""
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.run_context import CSVMetricLogger


def test_inferred_schema_rejects_mismatched_row():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "metrics.csv"
        logger = CSVMetricLogger(path)
        logger.log({"a": 1, "b": 2})
        try:
            logger.log({"a": 3, "c": 4})
        except ValueError as exc:
            msg = str(exc)
            assert "schema mismatch" in msg, f"unexpected error: {msg}"
            assert "missing=['b']" in msg, f"missing key not reported: {msg}"
            assert "extra=['c']" in msg, f"extra key not reported: {msg}"
        else:
            raise AssertionError("expected ValueError on schema mismatch")


def test_explicit_schema_rejects_mismatched_row_at_first_log():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "metrics.csv"
        logger = CSVMetricLogger(path, fieldnames=["x", "y"])
        try:
            logger.log({"x": 1, "z": 2})
        except ValueError as exc:
            assert "schema mismatch" in str(exc), f"unexpected error: {exc}"
        else:
            raise AssertionError("expected ValueError on schema mismatch at first log")


def test_consistent_rows_succeed():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "metrics.csv"
        logger = CSVMetricLogger(path)
        logger.log({"a": 1, "b": 2})
        logger.log({"a": 3, "b": 4})
        content = path.read_text(encoding="utf-8")
        lines = [l for l in content.splitlines() if l]
        assert len(lines) == 3, f"expected 3 lines (header + 2 rows), got {len(lines)}: {content!r}"
        assert lines[0] == "a,b", f"header should be 'a,b', got {lines[0]!r}"


if __name__ == "__main__":
    test_inferred_schema_rejects_mismatched_row()
    test_explicit_schema_rejects_mismatched_row_at_first_log()
    test_consistent_rows_succeed()
    print("CSVMetricLogger tests passed (3/3)")
