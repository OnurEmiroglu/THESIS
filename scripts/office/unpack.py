"""Unpack a .docx (ZIP) into a directory, preserving all entries."""
import sys, zipfile, os, pathlib

def unpack(docx_path: str, out_dir: str):
    out = pathlib.Path(out_dir)
    if out.exists():
        import shutil; shutil.rmtree(out)
    with zipfile.ZipFile(docx_path, "r") as z:
        z.extractall(out)
    print(f"Unpacked {docx_path} -> {out}  ({len(list(out.rglob('*')))} files)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python unpack.py <input.docx> <output_dir>"); sys.exit(1)
    unpack(sys.argv[1], sys.argv[2])
