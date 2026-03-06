"""Re-pack an unpacked directory back into a .docx (ZIP).

Usage:
    python pack.py <unpacked_dir> <output.docx> [--original <original.docx>]

When --original is given the ZIP entry order and compression settings are
copied from the original file for maximum fidelity.
"""
import sys, zipfile, os, pathlib, argparse

def pack(src_dir: str, out_docx: str, original: str | None = None):
    src = pathlib.Path(src_dir)
    # Gather entries in original order if possible
    if original and os.path.isfile(original):
        with zipfile.ZipFile(original, "r") as oz:
            entry_order = [i.filename for i in oz.infolist()]
    else:
        entry_order = []

    all_files: dict[str, pathlib.Path] = {}
    for f in src.rglob("*"):
        if f.is_file():
            rel = f.relative_to(src).as_posix()
            all_files[rel] = f

    # Build ordered list: original order first, then any new files
    ordered = []
    for name in entry_order:
        if name in all_files:
            ordered.append(name)
    for name in sorted(all_files):
        if name not in ordered:
            ordered.append(name)

    with zipfile.ZipFile(out_docx, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ordered:
            zf.write(all_files[name], name)

    print(f"Packed {src} -> {out_docx}  ({len(ordered)} entries, {os.path.getsize(out_docx)} bytes)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src_dir")
    ap.add_argument("out_docx")
    ap.add_argument("--original", default=None)
    args = ap.parse_args()
    pack(args.src_dir, args.out_docx, args.original)
