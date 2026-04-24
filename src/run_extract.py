"""Run entity extraction on all OCR outputs.

Reads JSON files from outputs/ocr/, extracts 5 entities using extractor.py,
and writes results to outputs/extracted/<doc_name>.json.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from extractor import extract_entities

ROOT = Path(__file__).resolve().parents[1]
OCR_DIR = ROOT / "outputs" / "ocr"
OUTPUT_DIR = ROOT / "outputs" / "extracted"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("run_extract")


def load_ocr_json(json_path: Path) -> tuple[str, str, str]:
    """Load OCR JSON and return (doc_name, full_text, language).
    
    Returns:
        Tuple of (document_name, concatenated_full_text, detected_language)
    """
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    
    doc_name = data["document_name"]
    
    # Concatenate all pages' text
    full_text = "\n\n".join(
        page["full_text"] for page in data["pages"]
    )
    
    # Detect language from filename (EN or FR)
    language = "FR" if "_FR_" in doc_name else "EN"
    
    return doc_name, full_text, language


def save_extraction_result(result, output_dir: Path) -> None:
    """Save extraction result as JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"{result.document_name}.json"
    
    # Convert to dict
    output_data = {
        "document_name": result.document_name,
        "extracted_entities": {
            "project_id": result.project_id,
            "supplier": result.supplier,
            "material": result.material,
            "quantity": result.quantity,
            "date": result.date,
        },
        "all_candidates": [
            {
                "field": e.field,
                "value": e.value,
                "confidence": round(e.confidence, 3),
                "source": e.source,
                "raw_text": e.raw_text[:100]  # truncate for readability
            }
            for e in result.entities
        ],
        "notes": result.notes,
    }
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    log.info("saved extraction: %s.json", result.document_name)


def main() -> int:
    if not OCR_DIR.exists():
        log.error("OCR directory not found: %s", OCR_DIR)
        log.error("run 'python src/run_ocr.py' first")
        return 1
    
    ocr_files = sorted(OCR_DIR.glob("*.json"))
    if not ocr_files:
        log.error("no OCR JSON files found in %s", OCR_DIR)
        return 1
    
    log.info("found %d OCR files to process", len(ocr_files))
    
    ok = failed = 0
    for ocr_file in ocr_files:
        try:
            doc_name, full_text, language = load_ocr_json(ocr_file)
            log.info("extracting from %s (%s, %d chars)", doc_name, language, len(full_text))
            
            result = extract_entities(full_text, language)
            result.document_name = doc_name
            
            save_extraction_result(result, OUTPUT_DIR)
            
            # Log summary
            log.info(
                "  → project_id=%s, supplier=%s, material=%s, quantity=%s, date=%s",
                result.project_id or "(none)",
                result.supplier[:30] + "..." if result.supplier and len(result.supplier) > 30 else result.supplier or "(none)",
                result.material or "(none)",
                result.quantity or "(none)",
                result.date or "(none)",
            )
            
            ok += 1
        
        except Exception as e:
            log.error("FAILED %s: %s", ocr_file.name, e, exc_info=True)
            failed += 1
    
    log.info("done: %d ok, %d failed (of %d)", ok, failed, len(ocr_files))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
