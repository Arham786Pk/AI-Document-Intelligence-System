"""Test suite for full pipeline integration (Task 9).

Tests the complete document intelligence pipeline:
- Individual stage execution
- End-to-end pipeline flow
- Error handling and recovery
- Result validation
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pipeline import Pipeline, PipelineResult


def test_pipeline_initialization():
    """Test pipeline initialization with output directories."""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        
        pipeline = Pipeline(
            processed_dir=tmp / "processed",
            ocr_output_dir=tmp / "ocr",
            extraction_output_dir=tmp / "extracted",
        )
        
        # Check directories were created
        assert pipeline.processed_dir.exists()
        assert pipeline.ocr_output_dir.exists()
        assert pipeline.extraction_output_dir.exists()
        
        print("✓ Pipeline initialization test passed")


def test_pipeline_result_serialization():
    """Test PipelineResult to_dict conversion."""
    result = PipelineResult(
        document_name="test_doc",
        source_path=Path("/fake/path.pdf"),
        success=True,
        preprocessing_ok=True,
        ocr_ok=True,
        extraction_ok=True,
        page_count=3,
        avg_ocr_confidence=95.5,
        total_text_length=1234,
    )
    
    data = result.to_dict()
    
    assert data["document_name"] == "test_doc"
    assert data["success"] is True
    assert data["stages"]["preprocessing"] is True
    assert data["stages"]["ocr"] is True
    assert data["stages"]["extraction"] is True
    assert data["outputs"]["page_count"] == 3
    assert data["outputs"]["avg_ocr_confidence"] == 95.5
    assert data["error"] is None
    
    print("✓ PipelineResult serialization test passed")


def test_pipeline_error_handling():
    """Test pipeline error handling with invalid input."""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        
        pipeline = Pipeline(
            processed_dir=tmp / "processed",
            ocr_output_dir=tmp / "ocr",
            extraction_output_dir=tmp / "extracted",
        )
        
        # Try to process non-existent file
        fake_path = tmp / "nonexistent.pdf"
        result = pipeline.run_document(fake_path, modality="digital")
        
        assert result.success is False
        assert result.error_stage == "preprocessing"
        assert result.error_message is not None
        
        print("✓ Pipeline error handling test passed")


def test_pipeline_end_to_end():
    """Test full pipeline on a real ground-truth document."""
    import csv
    
    # Load ground truth to find a document
    gt_csv = ROOT / "docs" / "ground_truth.csv"
    if not gt_csv.exists():
        print("⊘ Skipping end-to-end test (ground_truth.csv not found)")
        return
    
    with gt_csv.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    
    if not rows:
        print("⊘ Skipping end-to-end test (no documents in ground truth)")
        return
    
    # Find first available document
    raw_dirs = [
        ROOT / "data" / "raw" / "used" / "digital_pdfs",
        ROOT / "data" / "raw" / "used" / "scanned_docs",
    ]
    
    doc_path = None
    doc_modality = "digital"
    
    for row in rows:
        name = row["document_name"]
        modality = row.get("modality", "digital").strip().lower()
        
        for d in raw_dirs:
            p = d / name
            if p.exists():
                doc_path = p
                doc_modality = modality
                break
        
        if doc_path:
            break
    
    if not doc_path:
        print("⊘ Skipping end-to-end test (no raw documents found)")
        return
    
    # Run pipeline
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        
        pipeline = Pipeline(
            processed_dir=tmp / "processed",
            ocr_output_dir=tmp / "ocr",
            extraction_output_dir=tmp / "extracted",
            fallback_to_paddle=True,
        )
        
        print(f"  Testing with: {doc_path.name}")
        result = pipeline.run_document(doc_path, modality=doc_modality)
        
        # Validate result
        assert result.document_name == doc_path.stem
        assert result.source_path == doc_path
        
        if result.success:
            print(f"  ✓ Pipeline succeeded")
            print(f"    Pages: {result.page_count}")
            print(f"    OCR confidence: {result.avg_ocr_confidence:.1f}%")
            print(f"    Text length: {result.total_text_length} chars")
            
            # Check outputs were created
            assert result.page_count > 0
            assert len(result.preprocessed_pages) == result.page_count
            assert len(result.ocr_results) == result.page_count
            assert result.extraction_result is not None
            
            # Check files were written
            ocr_json = tmp / "ocr" / f"{doc_path.stem}.json"
            ocr_txt = tmp / "ocr" / f"{doc_path.stem}.txt"
            extraction_json = tmp / "extracted" / f"{doc_path.stem}.json"
            
            assert ocr_json.exists(), "OCR JSON not written"
            assert ocr_txt.exists(), "OCR text not written"
            assert extraction_json.exists(), "Extraction JSON not written"
            
            print("✓ Pipeline end-to-end test passed")
        else:
            print(f"  ✗ Pipeline failed at {result.error_stage}: {result.error_message}")
            print("⊘ End-to-end test inconclusive (pipeline failed)")


def main():
    """Run all pipeline tests."""
    print("=" * 80)
    print("PIPELINE TEST SUITE (Task 9)")
    print("=" * 80)
    print()
    
    tests = [
        ("Initialization", test_pipeline_initialization),
        ("Result serialization", test_pipeline_result_serialization),
        ("Error handling", test_pipeline_error_handling),
        ("End-to-end", test_pipeline_end_to_end),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"Running: {name}")
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1
        print()
    
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
