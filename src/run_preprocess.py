"""Run preprocessor on the 20 ground-truth documents only.

Reads docs/ground_truth.csv, locates each file under data/raw/{digital_pdfs,scanned_docs},
and writes preprocessed PNGs to data/processed/.
"""
from __future__ import annotations

import csv
import logging
import sys
from pathlib import Path

from preprocessor import preprocess_document

ROOT = Path(__file__).resolve().parents[1]
GT_CSV = ROOT / "docs" / "ground_truth.csv"
RAW_DIRS = [
    ROOT / "data" / "raw" / "used" / "digital_pdfs",
    ROOT / "data" / "raw" / "used" / "scanned_docs",
]
OUT_DIR = ROOT / "data" / "processed"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("run_preprocess")


def find_raw(name: str) -> Path | None:
    for d in RAW_DIRS:
        p = d / name
        if p.exists():
            return p
    return None


def main() -> int:
    if not GT_CSV.exists():
        log.error("ground truth not found: %s", GT_CSV)
        return 1

    with GT_CSV.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ok = missing = failed = 0
    for row in rows:
        name = row["document_name"]
        modality = row.get("modality", "digital").strip().lower()
        src = find_raw(name)
        if src is None:
            log.warning("MISSING raw file: %s", name)
            missing += 1
            continue
        try:
            preprocess_document(src, OUT_DIR, modality=modality)
            ok += 1
        except Exception as e:
            log.error("FAILED %s: %s", name, e)
            failed += 1

    log.info("done: %d ok, %d missing, %d failed (of %d)", ok, missing, failed, len(rows))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
