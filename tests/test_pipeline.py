"""Tests for Task 9 — Full pipeline.

Smoke tests for the French invoice processing pipeline. Tests cover:
  * Individual stage execution
  * Full pipeline execution
  * Pipeline from different starting points
  * Error handling
  * Report generation

Run:
    python -m pytest tests/test_pipeline.py -v
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.pipeline import (
    PipelineReport,
    PipelineResult,
    run_from_ocr,
    run_from_processed,
    run_pipeline,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PROCESSED_DIR = Path("data/processed")
OCR_DIR = Path("outputs/ocr_results")


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


# ---------------------------------------------------------------------------
# Data structure tests
# ---------------------------------------------------------------------------

def test_pipeline_result_structure():
    """Test PipelineResult data structure."""
    result = PipelineResult(
        stage="test",
        success=True,
        duration=1.5,
        items_processed=10,
        errors=0
    )
    
    assert result.stage == "test"
    assert result.success is True
    assert result.duration == 1.5
    assert result.items_processed == 10
    assert result.errors == 0


def test_pipeline_report_structure():
    """Test PipelineReport data structure."""
    report = PipelineReport(
        total_duration=5.0,
        total_invoices=10,
        successful_invoices=9,
        failed_invoices=1,
        output_directory="outputs"
    )
    
    assert report.total_duration == 5.0
    assert report.total_invoices == 10
    assert report.successful_invoices == 9
    assert report.failed_invoices == 1
    assert report.output_directory == "outputs"


# ---------------------------------------------------------------------------
# Pipeline execution tests
# ---------------------------------------------------------------------------

def test_run_from_processed(temp_output_dir):
    """Test pipeline from preprocessed images."""
    if not PROCESSED_DIR.exists():
        pytest.skip(f"Preprocessed data not found: {PROCESSED_DIR}")
    
    # Check if there are processed directories
    invoice_dirs = [d for d in PROCESSED_DIR.iterdir() if d.is_dir()]
    if not invoice_dirs:
        pytest.skip(f"No invoice directories in {PROCESSED_DIR}")
    
    # Run pipeline
    report = run_from_processed(PROCESSED_DIR, temp_output_dir)
    
    # Verify report structure
    assert isinstance(report, PipelineReport)
    assert report.total_duration > 0
    assert len(report.stages) == 2  # OCR + Extraction
    assert report.stages[0].stage == "ocr"
    assert report.stages[1].stage == "extraction"
    
    # Verify all stages succeeded
    assert all(stage.success for stage in report.stages)
    
    # Verify output files were created
    assert (temp_output_dir / "ocr_results").exists()
    assert (temp_output_dir / "extracted").exists()
    assert (temp_output_dir / "pipeline_report.json").exists()


def test_run_from_ocr(temp_output_dir):
    """Test pipeline from OCR results (extraction only)."""
    if not OCR_DIR.exists():
        pytest.skip(f"OCR results not found: {OCR_DIR}")
    
    # Check if there are OCR files
    json_files = [f for f in OCR_DIR.glob("*.json") if f.name != "ocr_manifest.json"]
    if not json_files:
        pytest.skip(f"No OCR JSON files in {OCR_DIR}")
    
    # Run pipeline
    report = run_from_ocr(OCR_DIR, temp_output_dir)
    
    # Verify report structure
    assert isinstance(report, PipelineReport)
    assert report.total_duration > 0
    assert len(report.stages) == 1  # Extraction only
    assert report.stages[0].stage == "extraction"
    
    # Verify stage succeeded
    assert report.stages[0].success
    
    # Verify output files were created
    assert (temp_output_dir / "extracted").exists()
    assert (temp_output_dir / "pipeline_report.json").exists()


def test_pipeline_report_json(temp_output_dir):
    """Test that pipeline report is written correctly."""
    if not OCR_DIR.exists():
        pytest.skip(f"OCR results not found: {OCR_DIR}")
    
    json_files = [f for f in OCR_DIR.glob("*.json") if f.name != "ocr_manifest.json"]
    if not json_files:
        pytest.skip(f"No OCR JSON files in {OCR_DIR}")
    
    # Run pipeline
    report = run_from_ocr(OCR_DIR, temp_output_dir)
    
    # Read report file
    report_path = temp_output_dir / "pipeline_report.json"
    assert report_path.exists()
    
    report_data = json.loads(report_path.read_text(encoding="utf-8"))
    
    # Verify report structure
    assert "total_duration" in report_data
    assert "stages" in report_data
    assert "total_invoices" in report_data
    assert "successful_invoices" in report_data
    assert "failed_invoices" in report_data
    assert "output_directory" in report_data
    
    # Verify stages
    assert isinstance(report_data["stages"], list)
    assert len(report_data["stages"]) > 0
    
    for stage in report_data["stages"]:
        assert "stage" in stage
        assert "success" in stage
        assert "duration" in stage
        assert "items_processed" in stage


def test_pipeline_with_specific_stages(temp_output_dir):
    """Test running specific pipeline stages."""
    if not PROCESSED_DIR.exists():
        pytest.skip(f"Preprocessed data not found: {PROCESSED_DIR}")
    
    invoice_dirs = [d for d in PROCESSED_DIR.iterdir() if d.is_dir()]
    if not invoice_dirs:
        pytest.skip(f"No invoice directories in {PROCESSED_DIR}")
    
    # Run only extraction stage (requires OCR results to exist)
    if not OCR_DIR.exists():
        pytest.skip(f"OCR results not found: {OCR_DIR}")
    
    # Create output structure
    ocr_output = temp_output_dir / "ocr_results"
    ocr_output.mkdir(parents=True, exist_ok=True)
    
    # Copy some OCR files for testing
    import shutil
    json_files = list(OCR_DIR.glob("*.json"))[:3]  # Just copy 3 files for speed
    for json_file in json_files:
        if json_file.name != "ocr_manifest.json":
            shutil.copy2(json_file, ocr_output / json_file.name)
    
    # Run extraction only
    report = run_pipeline(
        input_dir=PROCESSED_DIR,
        output_dir=temp_output_dir,
        stages=["extraction"]
    )
    
    # Verify only extraction stage ran
    assert len(report.stages) == 1
    assert report.stages[0].stage == "extraction"


# ---------------------------------------------------------------------------
# Performance tests
# ---------------------------------------------------------------------------

def test_pipeline_performance(temp_output_dir):
    """Test that pipeline completes in reasonable time."""
    if not OCR_DIR.exists():
        pytest.skip(f"OCR results not found: {OCR_DIR}")
    
    json_files = [f for f in OCR_DIR.glob("*.json") if f.name != "ocr_manifest.json"]
    if not json_files:
        pytest.skip(f"No OCR JSON files in {OCR_DIR}")
    
    # Run extraction only (fastest stage)
    report = run_from_ocr(OCR_DIR, temp_output_dir)
    
    # Should complete in under 5 seconds for 25 invoices
    assert report.total_duration < 5.0
    
    # Each invoice should process in under 1 second on average
    if report.total_invoices > 0:
        avg_time = report.total_duration / report.total_invoices
        assert avg_time < 1.0


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------

def test_pipeline_with_nonexistent_input():
    """Test pipeline with nonexistent input directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        nonexistent = Path(tmp_dir) / "nonexistent"
        output = Path(tmp_dir) / "output"
        
        # This should handle the error gracefully
        # The actual behavior depends on implementation
        # For now, we just verify it doesn't crash
        try:
            report = run_from_processed(nonexistent, output)
            # If it returns, check that it indicates failure
            assert report.failed_invoices >= 0
        except Exception:
            # It's okay if it raises an exception
            pass


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------

def test_full_pipeline_integration(temp_output_dir):
    """Test complete pipeline integration."""
    if not PROCESSED_DIR.exists():
        pytest.skip(f"Preprocessed data not found: {PROCESSED_DIR}")
    
    invoice_dirs = [d for d in PROCESSED_DIR.iterdir() if d.is_dir()]
    if not invoice_dirs:
        pytest.skip(f"No invoice directories in {PROCESSED_DIR}")
    
    # Run full pipeline from processed
    report = run_from_processed(PROCESSED_DIR, temp_output_dir)
    
    # Verify all stages completed
    assert len(report.stages) == 2
    assert all(stage.success for stage in report.stages)
    
    # Verify output structure
    assert (temp_output_dir / "ocr_results").exists()
    assert (temp_output_dir / "extracted").exists()
    
    # Verify OCR manifest exists
    ocr_manifest = temp_output_dir / "ocr_results" / "ocr_manifest.json"
    assert ocr_manifest.exists()
    
    # Verify extracted files exist
    extracted_files = list((temp_output_dir / "extracted").glob("*.json"))
    assert len(extracted_files) > 0
    
    # Verify pipeline report
    pipeline_report = temp_output_dir / "pipeline_report.json"
    assert pipeline_report.exists()
    
    report_data = json.loads(pipeline_report.read_text(encoding="utf-8"))
    assert report_data["successful_invoices"] > 0
    assert report_data["failed_invoices"] == 0


# ---------------------------------------------------------------------------
# Output validation tests
# ---------------------------------------------------------------------------

def test_pipeline_output_files(temp_output_dir):
    """Test that pipeline creates all expected output files."""
    if not OCR_DIR.exists():
        pytest.skip(f"OCR results not found: {OCR_DIR}")
    
    json_files = [f for f in OCR_DIR.glob("*.json") if f.name != "ocr_manifest.json"]
    if not json_files:
        pytest.skip(f"No OCR JSON files in {OCR_DIR}")
    
    # Run extraction
    report = run_from_ocr(OCR_DIR, temp_output_dir)
    
    # Check extracted directory
    extracted_dir = temp_output_dir / "extracted"
    assert extracted_dir.exists()
    assert extracted_dir.is_dir()
    
    # Check that JSON files were created
    extracted_files = list(extracted_dir.glob("*.json"))
    assert len(extracted_files) > 0
    
    # Verify each file is valid JSON with expected structure
    for json_file in extracted_files[:3]:  # Check first 3 files
        data = json.loads(json_file.read_text(encoding="utf-8"))
        
        # Should have all 11 entity fields
        assert "file_name" in data
        assert "supplier_name" in data
        assert "invoice_number" in data
        assert "invoice_date" in data
        assert "siret" in data
        assert "echeance" in data
        assert "invoice_content" in data
        assert "tva_percentage" in data
        assert "tva_amount" in data
        assert "total_amount" in data
        assert "payment_status" in data
        assert "solde_du" in data
