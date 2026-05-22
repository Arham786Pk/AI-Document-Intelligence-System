"""Full M1 pipeline re-run on the complete 200-doc dataset.

Stages: preprocess (data/pdf + data/images) -> OCR -> extract.
Writes fresh outputs/ for all 200 docs with the new filenames.
Metrics are computed separately afterwards against docs/ground_truth_full.csv.
"""

import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.pipeline import run_preprocessing, run_ocr, run_extraction  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
OCR_DIR = ROOT / "outputs" / "ocr_results"
EXTRACTED = ROOT / "outputs" / "extracted"


def main():
    t0 = time.time()
    # fresh start
    for d in (PROCESSED, OCR_DIR, EXTRACTED):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    print("== PREPROCESS data/pdf ==", flush=True)
    r1 = run_preprocessing(ROOT / "data" / "pdf", PROCESSED)
    print(f"   {r1}", flush=True)
    print("== PREPROCESS data/images ==", flush=True)
    r2 = run_preprocessing(ROOT / "data" / "images", PROCESSED)
    print(f"   {r2}", flush=True)

    subdirs = [p for p in PROCESSED.iterdir() if p.is_dir()]
    print(f"== preprocessed invoices: {len(subdirs)} ==", flush=True)

    print("== OCR ==", flush=True)
    r3 = run_ocr(PROCESSED, OCR_DIR)
    print(f"   {r3}", flush=True)

    print("== EXTRACT ==", flush=True)
    r4 = run_extraction(OCR_DIR, EXTRACTED)
    print(f"   {r4}", flush=True)

    n_ocr = len(list(OCR_DIR.glob("*.json")))
    n_ext = len(list(EXTRACTED.glob("*.json")))
    print(f"\nDONE in {time.time()-t0:.0f}s | OCR files: {n_ocr} | extracted: {n_ext}", flush=True)


if __name__ == "__main__":
    main()
