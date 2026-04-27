"""Main pipeline runner: process documents end-to-end.

Reads ground_truth.csv and runs the full pipeline (preprocessing → OCR → extraction)
on all 20 documents, or a specified subset.

Usage:
    python src/run.py                    # process all 20 ground-truth documents
    python src/run.py --doc Real_MaterialCert_EN_NST_Inspection.pdf  # single document
    python src/run.py --limit 5          # process first 5 documents only
    python src/run.py --summary          # show summary report only (no processing)
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

from pipeline import Pipeline, PipelineResult

ROOT = Path(__file__).resolve().parents[1]
GT_CSV = ROOT / "docs" / "ground_truth.csv"
RAW_DIGITAL_DIRS = [
    ROOT / "data" / "raw" / "used" / "digital_pdfs",
    ROOT / "data" / "raw" / "extra" / "digital_pdfs",
]
RAW_SCANNED_DIRS = [
    ROOT / "data" / "raw" / "used" / "scanned_docs",
    ROOT / "data" / "raw" / "extra" / "scanned_docs",
]
PROCESSED_DIR = ROOT / "data" / "processed"
OCR_DIR = ROOT / "outputs" / "ocr"
EXTRACTION_DIR = ROOT / "outputs" / "extracted"
RESULTS_DIR = ROOT / "outputs" / "pipeline_results"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("run")


def find_raw(name: str, modality: str = "digital") -> Path | None:
    """Find raw document by name. Searches modality-matching dirs first,
    then falls back to the other modality. Both `used/` and `extra/` are
    checked to support held-out documents added to ground_truth.csv.
    """
    primary = RAW_SCANNED_DIRS if modality == "scanned" else RAW_DIGITAL_DIRS
    secondary = RAW_DIGITAL_DIRS if modality == "scanned" else RAW_SCANNED_DIRS
    for d in primary + secondary:
        p = d / name
        if p.exists():
            return p
    return None


def load_ground_truth() -> list[dict]:
    """Load ground truth CSV."""
    if not GT_CSV.exists():
        log.error("ground truth not found: %s", GT_CSV)
        sys.exit(1)
    
    with GT_CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_pipeline_results(results: list[PipelineResult], output_dir: Path) -> Path:
    """Save pipeline results summary as JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"pipeline_run_{timestamp}.json"
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_documents": len(results),
        "successful": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "stage_failures": {
            "preprocessing": sum(1 for r in results if r.error_stage == "preprocessing"),
            "ocr": sum(1 for r in results if r.error_stage == "ocr"),
            "extraction": sum(1 for r in results if r.error_stage == "extraction"),
        },
        "avg_ocr_confidence": round(
            sum(r.avg_ocr_confidence for r in results if r.ocr_ok) / max(sum(1 for r in results if r.ocr_ok), 1),
            2
        ),
        "total_pages_processed": sum(r.page_count for r in results),
        "documents": [r.to_dict() for r in results],
    }
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    log.info("saved pipeline results: %s", output_path)
    return output_path


def print_summary(results: list[PipelineResult]) -> None:
    """Print human-readable summary of pipeline results."""
    print("\n" + "=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)
    
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful
    
    print(f"\nTotal documents: {total}")
    print(f"  ✓ Successful: {successful} ({100 * successful / total:.1f}%)")
    print(f"  ✗ Failed: {failed} ({100 * failed / total:.1f}%)")
    
    if failed > 0:
        print("\nFailure breakdown:")
        preprocessing_fails = sum(1 for r in results if r.error_stage == "preprocessing")
        ocr_fails = sum(1 for r in results if r.error_stage == "ocr")
        extraction_fails = sum(1 for r in results if r.error_stage == "extraction")
        
        if preprocessing_fails:
            print(f"  • Preprocessing: {preprocessing_fails}")
        if ocr_fails:
            print(f"  • OCR: {ocr_fails}")
        if extraction_fails:
            print(f"  • Extraction: {extraction_fails}")
    
    # OCR stats
    ocr_ok_results = [r for r in results if r.ocr_ok]
    if ocr_ok_results:
        avg_confidence = sum(r.avg_ocr_confidence for r in ocr_ok_results) / len(ocr_ok_results)
        print(f"\nOCR average confidence: {avg_confidence:.1f}%")
        print(f"Total pages processed: {sum(r.page_count for r in results)}")
    
    # Extraction stats
    extraction_ok_results = [r for r in results if r.extraction_ok]
    if extraction_ok_results:
        print(f"\nExtraction results ({len(extraction_ok_results)} documents):")
        
        field_counts = {
            "project_id": 0,
            "supplier": 0,
            "material": 0,
            "quantity": 0,
            "date": 0,
        }
        
        for r in extraction_ok_results:
            if r.extraction_result:
                if r.extraction_result.project_id:
                    field_counts["project_id"] += 1
                if r.extraction_result.supplier:
                    field_counts["supplier"] += 1
                if r.extraction_result.material:
                    field_counts["material"] += 1
                if r.extraction_result.quantity:
                    field_counts["quantity"] += 1
                if r.extraction_result.date:
                    field_counts["date"] += 1
        
        for field, count in field_counts.items():
            pct = 100 * count / len(extraction_ok_results)
            print(f"  • {field}: {count}/{len(extraction_ok_results)} ({pct:.1f}%)")
    
    # Failed documents
    if failed > 0:
        print("\nFailed documents:")
        for r in results:
            if not r.success:
                print(f"  ✗ {r.document_name}")
                print(f"    Stage: {r.error_stage}")
                print(f"    Error: {r.error_message}")
    
    print("\n" + "=" * 80)


def show_existing_summary() -> int:
    """Show summary from most recent pipeline run."""
    if not RESULTS_DIR.exists():
        log.error("no pipeline results found in %s", RESULTS_DIR)
        return 1
    
    result_files = sorted(RESULTS_DIR.glob("pipeline_run_*.json"))
    if not result_files:
        log.error("no pipeline result files found")
        return 1
    
    latest = result_files[-1]
    log.info("loading results from %s", latest.name)
    
    with latest.open(encoding="utf-8") as f:
        data = json.load(f)
    
    # Reconstruct PipelineResult objects for summary
    results = []
    for doc_data in data["documents"]:
        result = PipelineResult(
            document_name=doc_data["document_name"],
            source_path=Path(doc_data["source_path"]),
            success=doc_data["success"],
            preprocessing_ok=doc_data["stages"]["preprocessing"],
            ocr_ok=doc_data["stages"]["ocr"],
            extraction_ok=doc_data["stages"]["extraction"],
            page_count=doc_data["outputs"]["page_count"],
            avg_ocr_confidence=doc_data["outputs"]["avg_ocr_confidence"],
            total_text_length=doc_data["outputs"]["total_text_length"],
            error_stage=doc_data["error"]["stage"] if doc_data.get("error") else None,
            error_message=doc_data["error"]["message"] if doc_data.get("error") else None,
        )
        results.append(result)
    
    print_summary(results)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run full document intelligence pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--doc",
        metavar="NAME",
        help="process single document by name (e.g., Real_MaterialCert_EN_NST_Inspection.pdf)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="process only first N documents",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="show summary from most recent run (no processing)",
    )
    parser.add_argument(
        "--no-paddle",
        action="store_true",
        help="disable PaddleOCR fallback (Tesseract only)",
    )
    
    args = parser.parse_args()
    
    # Show summary mode
    if args.summary:
        return show_existing_summary()
    
    # Load ground truth
    rows = load_ground_truth()
    log.info("loaded %d documents from ground truth", len(rows))
    
    # Filter by document name if specified
    if args.doc:
        rows = [r for r in rows if r["document_name"] == args.doc]
        if not rows:
            log.error("document not found in ground truth: %s", args.doc)
            return 1
        log.info("processing single document: %s", args.doc)
    
    # Limit if specified
    if args.limit:
        rows = rows[:args.limit]
        log.info("limiting to first %d documents", args.limit)
    
    # Initialize pipeline
    pipeline = Pipeline(
        processed_dir=PROCESSED_DIR,
        ocr_output_dir=OCR_DIR,
        extraction_output_dir=EXTRACTION_DIR,
        fallback_to_paddle=not args.no_paddle,
    )
    
    # Process documents
    results: list[PipelineResult] = []
    for i, row in enumerate(rows, start=1):
        name = row["document_name"]
        modality = row.get("modality", "digital").strip().lower()
        
        log.info("[%d/%d] processing %s", i, len(rows), name)
        
        # Find source file
        src = find_raw(name, modality)
        if src is None:
            log.warning("MISSING raw file: %s", name)
            result = PipelineResult(
                document_name=name,
                source_path=Path("(not found)"),
                success=False,
                error_stage="preprocessing",
                error_message="source file not found",
            )
            results.append(result)
            continue
        
        # Run pipeline
        try:
            result = pipeline.run_document(src, modality=modality)
            results.append(result)
        except Exception as e:
            log.error("UNEXPECTED ERROR processing %s: %s", name, e, exc_info=True)
            result = PipelineResult(
                document_name=name,
                source_path=src,
                success=False,
                error_stage="unknown",
                error_message=str(e),
            )
            results.append(result)
    
    # Save results
    save_pipeline_results(results, RESULTS_DIR)
    
    # Print summary
    print_summary(results)
    
    # Exit code
    failed = sum(1 for r in results if not r.success)
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
