"""One-shot reorganizer.

Splits data/raw/{digital_pdfs,scanned_docs,images} into two clearly named groups:

  data/raw/used/      <- the 20 documents listed in docs/ground_truth.csv
  data/raw/extra/     <- everything else (kept for reference, not in pipeline)

Both halves preserve the digital_pdfs/scanned_docs/images subfolder layout.
Idempotent: re-running after split is a no-op.
"""
from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
GT = ROOT / "docs" / "ground_truth.csv"
SUBFOLDERS = ("digital_pdfs", "scanned_docs", "images")


def used_set() -> set[str]:
    with GT.open(encoding="utf-8") as f:
        return {row["document_name"].strip() for row in csv.DictReader(f)}


def main() -> int:
    if not GT.exists():
        print(f"ERROR ground truth not found: {GT}", file=sys.stderr)
        return 1

    used = used_set()
    used_dir = RAW / "used"
    extra_dir = RAW / "extra"

    moved_used = moved_extra = 0
    for sub in SUBFOLDERS:
        src = RAW / sub
        if not src.exists():
            continue
        (used_dir / sub).mkdir(parents=True, exist_ok=True)
        (extra_dir / sub).mkdir(parents=True, exist_ok=True)
        for f in src.iterdir():
            if not f.is_file():
                continue
            dest_root = used_dir if f.name in used else extra_dir
            dest = dest_root / sub / f.name
            shutil.move(str(f), str(dest))
            if dest_root is used_dir:
                moved_used += 1
            else:
                moved_extra += 1
        # remove the now-empty original subfolder
        try:
            src.rmdir()
        except OSError:
            pass  # not empty (e.g. README) — leave it alone

    print(f"moved {moved_used} into used/, {moved_extra} into extra/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
