"""Smoke test for preprocessor — runs on the first available ground-truth PDF."""
from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from preprocessor import preprocess_document  # noqa: E402


def _first_existing_pdf() -> tuple[Path, str]:
    gt = ROOT / "docs" / "ground_truth.csv"
    raw_dirs = [ROOT / "data" / "raw" / "digital_pdfs", ROOT / "data" / "raw" / "scanned_docs"]
    with gt.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for d in raw_dirs:
                p = d / row["document_name"]
                if p.exists():
                    return p, row["modality"].strip().lower()
    raise RuntimeError("no ground-truth PDF found under data/raw/")


def test_preprocess_one_pdf():
    pdf, modality = _first_existing_pdf()
    with tempfile.TemporaryDirectory() as td:
        out_paths = preprocess_document(pdf, td, modality=modality)
        assert out_paths, "expected at least one page output"
        for p in out_paths:
            assert p.exists() and p.stat().st_size > 0, f"empty output: {p}"
            assert p.suffix == ".png"


if __name__ == "__main__":
    test_preprocess_one_pdf()
    print("OK")
