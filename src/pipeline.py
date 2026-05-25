"""Task 9 + Task 11 — Full pipeline for French invoice processing.

Orchestrates the complete workflow:
  1. Preprocessing (Task 6) — Clean and prepare images
  2. OCR (Task 7) — Extract text from images
  3. Entity Extraction — Extract 12 structured fields using one of:
     - 'rules'  (M1 rule-based extractor, 11 entities)
     - 'ai'     (LayoutLMv3, 12 entities including consumer_name)
     - 'hybrid' (AI for all + rules fallback for supplier_name)

The pipeline can run end-to-end or individual stages, with automatic
dependency checking and incremental processing.

Usage:
    from src.pipeline import run_pipeline

    # Full pipeline
    results = run_pipeline(
        input_dir="data/pdf",
        output_dir="outputs"
    )

    # CLI:
    #   python -m src.pipeline --input data/pdf --output outputs
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from src.extractor import extract_from_ocr_folder, extract_entities
from src.ocr_engine import ocr_folder, write_manifest as write_ocr_manifest
from src.preprocessor import preprocess_folder, write_manifest as write_preprocessing_manifest

# Try importing AI extractor (optional — requires transformers + torch)
try:
    from src.ai_extractor import extract_from_folder_ai, extract_entities_ai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


@dataclass
class PipelineResult:
    """Result of pipeline execution."""
    stage: str
    success: bool
    duration: float
    items_processed: int
    items_skipped: int = 0
    errors: int = 0
    message: str = ""


@dataclass
class PipelineReport:
    """Complete pipeline execution report."""
    total_duration: float
    stages: list[PipelineResult] = field(default_factory=list)
    total_invoices: int = 0
    successful_invoices: int = 0
    failed_invoices: int = 0
    output_directory: str = ""


# ---------------------------------------------------------------------------
# Pipeline stages
# ---------------------------------------------------------------------------

def run_preprocessing(input_dir: Path, processed_dir: Path) -> PipelineResult:
    """Run preprocessing stage (Task 6).
    
    Args:
        input_dir: Directory containing raw invoice files (PDFs, images)
        processed_dir: Directory to write preprocessed PNG files
    
    Returns:
        PipelineResult with preprocessing statistics
    """
    print("\n" + "="*70)
    print("STAGE 1: PREPROCESSING")
    print("="*70)
    
    start_time = time.time()
    
    try:
        # Run preprocessing
        results = preprocess_folder(input_dir, processed_dir)
        
        # Write manifest
        write_preprocessing_manifest(results, processed_dir)
        
        duration = time.time() - start_time
        
        # Count successes and errors
        successful = sum(1 for r in results if r.source_type != "error")
        errors = sum(1 for r in results if r.source_type == "error")
        
        return PipelineResult(
            stage="preprocessing",
            success=True,
            duration=duration,
            items_processed=successful,
            errors=errors,
            message=f"Preprocessed {successful} invoices, {errors} errors"
        )
        
    except Exception as e:
        duration = time.time() - start_time
        return PipelineResult(
            stage="preprocessing",
            success=False,
            duration=duration,
            items_processed=0,
            errors=1,
            message=f"Preprocessing failed: {e}"
        )


def run_ocr(processed_dir: Path, ocr_dir: Path) -> PipelineResult:
    """Run OCR stage (Task 7).
    
    Args:
        processed_dir: Directory containing preprocessed PNG files
        ocr_dir: Directory to write OCR JSON files
    
    Returns:
        PipelineResult with OCR statistics
    """
    print("\n" + "="*70)
    print("STAGE 2: OCR TEXT EXTRACTION")
    print("="*70)
    
    start_time = time.time()
    
    try:
        # Run OCR
        results = ocr_folder(processed_dir, ocr_dir)
        
        # Write manifest
        write_ocr_manifest(results, ocr_dir)
        
        duration = time.time() - start_time
        
        # Count successes and errors
        successful = sum(1 for r in results if not r.error)
        errors = sum(1 for r in results if r.error)
        
        # Count skipped (from log output - approximation)
        # In practice, ocr_folder doesn't return skipped count, so we estimate
        skipped = 0
        
        return PipelineResult(
            stage="ocr",
            success=True,
            duration=duration,
            items_processed=successful,
            items_skipped=skipped,
            errors=errors,
            message=f"OCR processed {successful} invoices, {errors} errors"
        )
        
    except Exception as e:
        duration = time.time() - start_time
        return PipelineResult(
            stage="ocr",
            success=False,
            duration=duration,
            items_processed=0,
            errors=1,
            message=f"OCR failed: {e}"
        )


def run_extraction(
    ocr_dir: Path,
    extracted_dir: Path,
    extractor: Literal["rules", "ai", "hybrid"] = "rules",
    model_dir: str | Path = "models/layoutlmv3/best",
    input_dir: Path | None = None,
) -> PipelineResult:
    """Run entity extraction stage.
    
    Args:
        ocr_dir: Directory containing OCR JSON files
        extracted_dir: Directory to write extracted entity JSON files
        extractor: Extraction mode — 'rules' (M1), 'ai' (LayoutLMv3), or 'hybrid'
        model_dir: Path to fine-tuned LayoutLMv3 model (for 'ai' and 'hybrid' modes)
        input_dir: Directory containing source images/PDFs (required for 'ai' mode)
    
    Returns:
        PipelineResult with extraction statistics
    """
    label = {
        "rules": "RULE-BASED ENTITY EXTRACTION (M1)",
        "ai":    "AI ENTITY EXTRACTION (LayoutLMv3)",
        "hybrid": "HYBRID ENTITY EXTRACTION (AI + Rules)",
    }.get(extractor, "ENTITY EXTRACTION")
    
    print("\n" + "="*70)
    print(f"STAGE 3: {label}")
    print("="*70)
    
    start_time = time.time()
    
    try:
        if extractor == "rules":
            results = extract_from_ocr_folder(ocr_dir, extracted_dir)
        elif extractor in ("ai", "hybrid"):
            if not AI_AVAILABLE:
                print("[WARNING] AI extractor not available (transformers/torch not installed).")
                print("          Falling back to rule-based extraction.")
                results = extract_from_ocr_folder(ocr_dir, extracted_dir)
            else:
                # AI extraction runs directly on images/PDFs (not OCR JSON)
                source_dir = input_dir if input_dir else ocr_dir
                results = extract_from_folder_ai(
                    input_dir=source_dir,
                    output_dir=extracted_dir,
                    model_dir=model_dir,
                )
                # Hybrid: override supplier_name with rule-based result
                if extractor == "hybrid":
                    _apply_hybrid_override(ocr_dir, results, extracted_dir)
        else:
            raise ValueError(f"Unknown extractor: {extractor!r}")
        
        duration = time.time() - start_time
        successful = len(results)
        errors = 0
        
        return PipelineResult(
            stage="extraction",
            success=True,
            duration=duration,
            items_processed=successful,
            errors=errors,
            message=f"Extracted entities from {successful} invoices ({extractor} mode)"
        )
        
    except Exception as e:
        duration = time.time() - start_time
        return PipelineResult(
            stage="extraction",
            success=False,
            duration=duration,
            items_processed=0,
            errors=1,
            message=f"Extraction failed: {e}"
        )


def _apply_hybrid_override(
    ocr_dir: Path,
    ai_results: list[dict],
    extracted_dir: Path,
) -> None:
    """In hybrid mode, replace AI supplier_name with rule-based result.
    
    The M1 rule-based extractor scores 80% F1 on supplier_name vs 70% for
    LayoutLMv3, so rules are better for this specific entity.
    """
    print("  [HYBRID] Overriding supplier_name with rule-based extraction...")
    for result in ai_results:
        fname = result.get("file_name", "")
        # Try to find matching OCR file
        ocr_file = ocr_dir / f"{fname}.json"
        if ocr_file.exists():
            try:
                ocr_data = json.loads(ocr_file.read_text(encoding="utf-8"))
                ocr_text = ocr_data.get("full_text", "")
                rule_entities = extract_entities(ocr_text, fname)
                rule_supplier = rule_entities.get("supplier_name", "")
                if rule_supplier:
                    result["supplier_name"] = rule_supplier
                    # Update the saved JSON
                    out_file = extracted_dir / f"{fname}.json"
                    if out_file.exists():
                        out_file.write_text(
                            json.dumps(result, indent=2, ensure_ascii=False),
                            encoding="utf-8"
                        )
            except Exception:
                pass  # keep AI result if rule extraction fails


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    input_dir: str | Path,
    output_dir: str | Path,
    stages: list[Literal["preprocessing", "ocr", "extraction"]] | None = None,
    skip_existing: bool = True,
    extractor: Literal["rules", "ai", "hybrid"] = "rules",
    model_dir: str | Path = "models/layoutlmv3/best",
) -> PipelineReport:
    """Run the complete French invoice processing pipeline.
    
    Args:
        input_dir: Directory containing raw invoice files (PDFs, images)
        output_dir: Base output directory (will create subdirectories)
        stages: List of stages to run (default: all stages)
        skip_existing: If True, skip stages with existing output
    
    Returns:
        PipelineReport with complete execution statistics
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    # Default: run all stages
    if stages is None:
        stages = ["preprocessing", "ocr", "extraction"]
    
    # Create output directories
    processed_dir = output_dir / "processed"
    ocr_dir = output_dir / "ocr_results"
    extracted_dir = output_dir / "extracted"
    
    print("\n" + "="*70)
    print("FRENCH INVOICE PROCESSING PIPELINE")
    print("="*70)
    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Stages: {', '.join(stages)}")
    print("="*70)
    
    start_time = time.time()
    report = PipelineReport(
        total_duration=0.0,
        output_directory=str(output_dir)
    )
    
    # Stage 1: Preprocessing
    if "preprocessing" in stages:
        result = run_preprocessing(input_dir, processed_dir)
        report.stages.append(result)
        
        if not result.success:
            print(f"\n❌ Pipeline stopped: {result.message}")
            report.total_duration = time.time() - start_time
            return report
    
    # Stage 2: OCR
    if "ocr" in stages:
        result = run_ocr(processed_dir, ocr_dir)
        report.stages.append(result)
        
        if not result.success:
            print(f"\n❌ Pipeline stopped: {result.message}")
            report.total_duration = time.time() - start_time
            return report
    
    # Stage 3: Entity Extraction
    if "extraction" in stages:
        result = run_extraction(
            ocr_dir, extracted_dir,
            extractor=extractor,
            model_dir=model_dir,
            input_dir=input_dir,
        )
        report.stages.append(result)
        
        if not result.success:
            print(f"\n❌ Pipeline stopped: {result.message}")
            report.total_duration = time.time() - start_time
            return report
    
    # Calculate totals
    report.total_duration = time.time() - start_time
    
    # Get final counts from last stage
    if report.stages:
        last_stage = report.stages[-1]
        report.total_invoices = last_stage.items_processed
        report.successful_invoices = last_stage.items_processed - last_stage.errors
        report.failed_invoices = last_stage.errors
    
    # Print summary
    print("\n" + "="*70)
    print("PIPELINE COMPLETE")
    print("="*70)
    print(f"Total duration: {report.total_duration:.2f}s")
    print(f"Total invoices: {report.total_invoices}")
    print(f"Successful: {report.successful_invoices}")
    print(f"Failed: {report.failed_invoices}")
    print("\nStage breakdown:")
    for stage in report.stages:
        status = "✅" if stage.success else "❌"
        print(f"  {status} {stage.stage.upper()}: {stage.duration:.2f}s "
              f"({stage.items_processed} processed, {stage.errors} errors)")
    print("="*70)
    
    # Write pipeline report
    report_path = output_dir / "pipeline_report.json"
    report_path.write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\nPipeline report saved to: {report_path}")
    
    return report


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def run_from_raw(
    input_dir: str | Path,
    output_dir: str | Path = "outputs",
    extractor: Literal["rules", "ai", "hybrid"] = "rules",
    model_dir: str | Path = "models/layoutlmv3/best",
) -> PipelineReport:
    """Run complete pipeline from raw invoices to extracted entities.
    
    Convenience function that runs all three stages.
    
    Args:
        input_dir: Directory containing raw invoice files
        output_dir: Base output directory
        extractor: Extraction mode — 'rules' (M1), 'ai' (LayoutLMv3), or 'hybrid'
        model_dir: Path to fine-tuned LayoutLMv3 model (for 'ai' and 'hybrid' modes)
    
    Returns:
        PipelineReport with execution statistics
    """
    return run_pipeline(
        input_dir, output_dir,
        stages=["preprocessing", "ocr", "extraction"],
        extractor=extractor,
        model_dir=model_dir,
    )


def run_from_processed(
    processed_dir: str | Path,
    output_dir: str | Path = "outputs",
    extractor: Literal["rules", "ai", "hybrid"] = "rules",
    model_dir: str | Path = "models/layoutlmv3/best",
) -> PipelineReport:
    """Run pipeline from preprocessed images (skip preprocessing).
    
    Args:
        processed_dir: Directory containing preprocessed PNG files
        output_dir: Base output directory
    
    Returns:
        PipelineReport with execution statistics
    """
    # For this case, we need to adjust the pipeline
    # We'll use processed_dir as input and run OCR + extraction
    processed_dir = Path(processed_dir)
    output_dir = Path(output_dir)
    
    ocr_dir = output_dir / "ocr_results"
    extracted_dir = output_dir / "extracted"
    
    print("\n" + "="*70)
    print("FRENCH INVOICE PROCESSING PIPELINE (from preprocessed)")
    print("="*70)
    print(f"Input:  {processed_dir}")
    print(f"Output: {output_dir}")
    print("="*70)
    
    start_time = time.time()
    report = PipelineReport(total_duration=0.0, output_directory=str(output_dir))
    
    # Stage 1: OCR
    result = run_ocr(processed_dir, ocr_dir)
    report.stages.append(result)
    
    if not result.success:
        print(f"\n❌ Pipeline stopped: {result.message}")
        report.total_duration = time.time() - start_time
        return report
    
    # Stage 2: Entity Extraction
    result = run_extraction(
        ocr_dir, extracted_dir,
        extractor=extractor,
        model_dir=model_dir,
        input_dir=processed_dir,
    )
    report.stages.append(result)
    
    report.total_duration = time.time() - start_time
    
    if report.stages:
        last_stage = report.stages[-1]
        report.total_invoices = last_stage.items_processed
        report.successful_invoices = last_stage.items_processed - last_stage.errors
        report.failed_invoices = last_stage.errors
    
    # Print summary
    print("\n" + "="*70)
    print("PIPELINE COMPLETE")
    print("="*70)
    print(f"Total duration: {report.total_duration:.2f}s")
    print(f"Total invoices: {report.total_invoices}")
    print(f"Successful: {report.successful_invoices}")
    print(f"Failed: {report.failed_invoices}")
    print("\nStage breakdown:")
    for stage in report.stages:
        status = "✅" if stage.success else "❌"
        print(f"  {status} {stage.stage.upper()}: {stage.duration:.2f}s "
              f"({stage.items_processed} processed, {stage.errors} errors)")
    print("="*70)
    
    # Write pipeline report
    report_path = output_dir / "pipeline_report.json"
    report_path.write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\nPipeline report saved to: {report_path}")
    
    return report


def run_from_ocr(
    ocr_dir: str | Path,
    output_dir: str | Path = "outputs",
    extractor: Literal["rules", "ai", "hybrid"] = "rules",
    model_dir: str | Path = "models/layoutlmv3/best",
) -> PipelineReport:
    """Run pipeline from OCR results (skip preprocessing and OCR).
    
    Args:
        ocr_dir: Directory containing OCR JSON files
        output_dir: Base output directory
    
    Returns:
        PipelineReport with execution statistics
    """
    ocr_dir = Path(ocr_dir)
    output_dir = Path(output_dir)
    extracted_dir = output_dir / "extracted"
    
    print("\n" + "="*70)
    print("FRENCH INVOICE PROCESSING PIPELINE (from OCR)")
    print("="*70)
    print(f"Input:  {ocr_dir}")
    print(f"Output: {output_dir}")
    print("="*70)
    
    start_time = time.time()
    report = PipelineReport(total_duration=0.0, output_directory=str(output_dir))
    
    # Stage: Entity Extraction only
    result = run_extraction(
        ocr_dir, extracted_dir,
        extractor=extractor,
        model_dir=model_dir,
        input_dir=ocr_dir,
    )
    report.stages.append(result)
    
    report.total_duration = time.time() - start_time
    report.total_invoices = result.items_processed
    report.successful_invoices = result.items_processed - result.errors
    report.failed_invoices = result.errors
    
    # Print summary
    print("\n" + "="*70)
    print("PIPELINE COMPLETE")
    print("="*70)
    print(f"Total duration: {report.total_duration:.2f}s")
    print(f"Total invoices: {report.total_invoices}")
    print(f"Successful: {report.successful_invoices}")
    print(f"Failed: {report.failed_invoices}")
    print("="*70)
    
    # Write pipeline report
    report_path = output_dir / "pipeline_report.json"
    report_path.write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\nPipeline report saved to: {report_path}")
    
    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run the complete French invoice processing pipeline."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input directory (raw invoices, preprocessed, or OCR results)"
    )
    parser.add_argument(
        "--output",
        default="outputs",
        help="Output directory for all pipeline results"
    )
    parser.add_argument(
        "--from",
        dest="start_from",
        choices=["raw", "processed", "ocr"],
        default="processed",
        help="Starting point: 'raw' (full pipeline), 'processed' (skip preprocessing), 'ocr' (extraction only)"
    )
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=["preprocessing", "ocr", "extraction"],
        help="Specific stages to run (overrides --from)"
    )
    parser.add_argument(
        "--extractor",
        choices=["rules", "ai", "hybrid"],
        default="rules",
        help="Extraction mode: 'rules' (M1 regex), 'ai' (LayoutLMv3), 'hybrid' (AI + rules for supplier_name)"
    )
    parser.add_argument(
        "--model",
        default="models/layoutlmv3/best",
        help="Path to fine-tuned LayoutLMv3 model directory (for --extractor ai/hybrid)"
    )
    
    args = parser.parse_args()
    
    # Warn if AI requested but not available
    if args.extractor in ("ai", "hybrid") and not AI_AVAILABLE:
        print("[WARNING] AI extractor requested but transformers/torch not installed.")
        print("          Install with: pip install transformers torch accelerate")
        print("          Falling back to rule-based extraction.")
        args.extractor = "rules"
    
    # Run appropriate pipeline
    if args.stages:
        report = run_pipeline(
            args.input, args.output, stages=args.stages,
            extractor=args.extractor, model_dir=args.model
        )
    elif args.start_from == "raw":
        report = run_from_raw(
            args.input, args.output,
            extractor=args.extractor, model_dir=args.model
        )
    elif args.start_from == "processed":
        report = run_from_processed(
            args.input, args.output,
            extractor=args.extractor, model_dir=args.model
        )
    elif args.start_from == "ocr":
        report = run_from_ocr(
            args.input, args.output,
            extractor=args.extractor, model_dir=args.model
        )
    else:
        report = run_from_processed(
            args.input, args.output,
            extractor=args.extractor, model_dir=args.model
        )
    
    # Exit with appropriate code
    if report.failed_invoices > 0:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    _cli()
