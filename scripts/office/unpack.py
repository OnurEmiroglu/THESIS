"""Unpack a .docx (ZIP) into a directory under a safe workspace root."""
import sys
import zipfile
import shutil
from pathlib import Path

# Designated workspace for unpacked archives. Recursive delete and
# extraction are both bounded to paths under this root, so an unintended
# CLI argument cannot wipe arbitrary directories or write outside it.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SAFE_ROOT = REPO_ROOT / "manuscript" / "_unpack"


def _assert_under_safe_root(target: Path, safe_root: Path) -> None:
    target_r = target.resolve()
    safe_r = safe_root.resolve()
    try:
        target_r.relative_to(safe_r)
    except ValueError as exc:
        raise ValueError(
            f"Refusing to operate on {target_r}: not under SAFE_ROOT {safe_r}"
        ) from exc


def _safe_extract(zf: zipfile.ZipFile, out_dir: Path) -> None:
    """Extract all members under out_dir with path-traversal and symlink checks."""
    out_resolved = out_dir.resolve()
    for member in zf.infolist():
        name = member.filename
        # Reject POSIX-absolute and Windows-drive-absolute member names.
        if name.startswith("/") or (len(name) >= 2 and name[1] == ":"):
            raise ValueError(f"Refusing absolute path member: {name!r}")
        # Reject symlink members (Unix mode high bits == 0o120000).
        if (member.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError(f"Refusing symlink member: {name!r}")
        target = (out_dir / name).resolve()
        try:
            target.relative_to(out_resolved)
        except ValueError as exc:
            raise ValueError(
                f"Refusing path-traversal member: {name!r} -> {target}"
            ) from exc
        zf.extract(member, out_dir)


def unpack(docx_path: str, out_dir: str) -> None:
    out = Path(out_dir)
    _assert_under_safe_root(out, SAFE_ROOT)
    SAFE_ROOT.mkdir(parents=True, exist_ok=True)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(docx_path, "r") as z:
        _safe_extract(z, out)
    print(f"Unpacked {docx_path} -> {out}  ({len(list(out.rglob('*')))} files)")


def _self_test() -> None:
    """Build synthetic bad/good archives in memory; assert guards trip."""
    import io
    import tempfile

    SAFE_ROOT.mkdir(parents=True, exist_ok=True)

    # 1. SAFE_ROOT guard rejects out-of-root paths.
    try:
        _assert_under_safe_root(REPO_ROOT / "manuscript", SAFE_ROOT)
    except ValueError:
        pass
    else:
        raise AssertionError("Out-of-root path was not rejected")

    def _expect_reject(zip_buf, label):
        zip_buf.seek(0)
        with tempfile.TemporaryDirectory(dir=SAFE_ROOT) as td:
            with zipfile.ZipFile(zip_buf, "r") as zr:
                try:
                    _safe_extract(zr, Path(td))
                except ValueError:
                    return
        raise AssertionError(f"{label} was not rejected")

    # 2. Path-traversal member.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zw:
        zw.writestr("../evil.txt", b"x")
    _expect_reject(buf, "path-traversal member")

    # 3. POSIX absolute-path member.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zw:
        zw.writestr("/abs/evil.txt", b"x")
    _expect_reject(buf, "POSIX absolute-path member")

    # 4. Windows drive-absolute member.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zw:
        zw.writestr("C:/abs/evil.txt", b"x")
    _expect_reject(buf, "Windows drive-absolute member")

    # 5. Good archive extracts.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zw:
        zw.writestr("ok/file.txt", b"hello")
    buf.seek(0)
    with tempfile.TemporaryDirectory(dir=SAFE_ROOT) as td:
        td_path = Path(td)
        with zipfile.ZipFile(buf, "r") as zr:
            _safe_extract(zr, td_path)
        assert (td_path / "ok" / "file.txt").read_bytes() == b"hello"

    print("self-test passed")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--self-test":
        _self_test()
    elif len(sys.argv) < 3:
        print("Usage: python unpack.py <input.docx> <output_dir>")
        print("       python unpack.py --self-test")
        sys.exit(1)
    else:
        unpack(sys.argv[1], sys.argv[2])
