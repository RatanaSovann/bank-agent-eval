"""Check that a synthetic data version still matches its manifest (no silent edits).

Usage:
    python scripts/verify_manifest.py v1
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(version: str) -> int:
    manifest = json.loads((ROOT / "data" / "synthetic" / version / "MANIFEST.json").read_text())
    ok = True
    for group in ("prompts", "outputs"):
        for name, entry in manifest[group].items():
            actual = hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest()
            status = "ok" if actual == entry["sha256"] else "CHANGED"
            ok &= status == "ok"
            print(f"{status:8} {entry['path']}")
    print("all files match the manifest" if ok else "some files changed: create a new version instead of editing")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "v1"))
