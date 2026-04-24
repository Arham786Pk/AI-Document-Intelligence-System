"""Run OCR on all preprocessed pages from the 20 ground-truth documents.

Reads page PNGs from data/processed/, runs OCR via ocr_engine.py,
and writes structured text output to outputs/ocr/<doc_name>.txt.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from ocr_engine import ocr_document, OCRResult

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "outputs" / "ocr"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("run_ocr")


def group_pages_by_document(processed_dir: Path) -> dict[str, list[Path]]:
    """Group page PNGs by document name (stem before _pNN)."""
    docs: dict[str, list[Path]] = {}
    for png in sorted(processed_dir.glob("*.png")):
        # Extract doc name: Real_MaterialCert_EN_NST_Inspection_p01.png -> Real_MaterialCert_EN_NST_Inspection
        stem = png.stem
        if "_p" in stem:
            doc_name = stem.rsplit("_p", 1)[0]
        else:
            doc_name = stem
        docs.setdefault(doc_name, []).append(png)
    return docs


def save_ocr_results(doc_name: str, results: list[OCRResult], output_dir: Path) -> None:
    """Save OCR results in both human-readable and JSON formats."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Human-readable text file
    txt_path = output_dir / f"{doc_name}.txt"
    with txt_path.open("w", encoding="utf-8") as f:
        f.write(f"# OCR Results: {doc_name}\n")
        f.write(f"# Total pages: {len(results)}\n\n")
        for i, result in enumerate(results, start=1):
            f.write(f"{'=' * 80}\n")
            f.write(f"Page {i}: {result.page_path.name}\n")
            f.write(f"Engine: {result.engine}\n")
            f.write(f"Confidence: {result.avg_confidence:.1f}%\n")
            f.write(f"Words: {len(result.words)}\n")
            f.write(f"{'-' * 80}\n")
            f.write(result.full_text)
            f.write("\n\n")

    # Structured JSON file (for Task 8 extractor)
    json_path = output_dir / f"{doc_name}.json"
    json_data = {
        "document_name": doc_name,
        "total_pages": len(results),
        "pages": [
            {
                "page_number": i,
                "page_file": result.page_path.name,
                "engine": result.engine,
                "avg_confidence": round(result.avg_confidence, 2),
                "full_text": result.full_text,
                "word_count": len(result.words),
                "words": [
                    {
                        "text": w.text,
                        "confidence": round(w.confidence, 2),
                        "bbox": w.bbox,
                    }
                    for w in result.words
                ],
            }
            for i, result in enumerate(results, start=1)
        ],
    }
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    log.info("saved OCR results: %s.txt + %s.json", doc_name, doc_name)


def main() -> int:
    if not PROCESSED_DIR.exists():
        log.error("processed directory not found: %s", PROCESSED_DIR)
        log.error("run 'python src/run_preprocess.py' first")
        return 1

    docs = group_pages_by_document(PROCESSED_DIR)
    if not docs:
        log.error("no page PNGs found in %s", PROCESSED_DIR)
        return 1

    log.info("found %d documents (%d total pages)", len(docs), sum(len(p) for p in docs.values()))

    ok = failed = 0
    for doc_name, pages in sorted(docs.items()):
        log.info("processing %s (%d pages)", doc_name, len(pages))
        try:
            results = ocr_document(pages, fallback_to_paddle=True)
            save_ocr_results(doc_name, results, OUTPUT_DIR)
            ok += 1
        except Exception as e:
            log.error("FAILED %s: %s", doc_name, e)
            failed += 1

    log.info("done: %d ok, %d failed (of %d)", ok, failed, len(docs))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
