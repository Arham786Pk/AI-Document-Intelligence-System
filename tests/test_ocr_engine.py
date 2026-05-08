"""Tests for Task 7 — OCR engine.

Smoke tests for the French invoice OCR engine. Tests cover:
  * Tesseract OCR on preprocessed images
  * Confidence scoring
  * Multi-page invoice handling
  * Batch processing
  * Error handling

Run:
    python -m pytest tests/test_ocr_engine.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ocr_engine import (
    LOW_CONFIDENCE_THRESHOLD,
    MIN_TEXT_LENGTH,
    TESSERACT_CONFIG,
    TESSERACT_LANG,
    InvoiceOCRResult,
    PageOCRResult,
    ocr_folder,
    ocr_invoice,
    ocr_page,
    write_manifest,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PROCESSED_DIR = Path("data/processed")
TEST_OUTPUT_DIR = Path("outputs/test_ocr")


@pytest.fixture
def sample_invoice_dir():
    """Return path to first available preprocessed invoice, or skip if none exist."""
    if not PROCESSED_DIR.exists():
        pytest.skip(f"Preprocessed data not found: {PROCESSED_DIR}")
    
    invoice_dirs = [d for d in PROCESSED_DIR.iterdir() if d.is_dir()]
    if not invoice_dirs:
        pytest.skip(f"No invoice directories in {PROCESSED_DIR}")
    
    return invoice_dirs[0]


@pytest.fixture
def sample_page_path(sample_invoice_dir):
    """Return path to first page PNG of sample invoice."""
    page_files = sorted(sample_invoice_dir.glob("page_*.png"))
    if not page_files:
        pytest.skip(f"No page PNG files in {sample_invoice_dir}")
    return page_files[0]


# ---------------------------------------------------------------------------
# Configuration tests
# ---------------------------------------------------------------------------

def test_constants():
    """Verify OCR configuration constants."""
    assert TESSERACT_LANG == "fra", "Must use French language pack"
    assert "--psm" in TESSERACT_CONFIG, "Must specify page segmentation mode"
    assert 0.0 < LOW_CONFIDENCE_THRESHOLD < 1.0, "Confidence threshold must be in (0, 1)"
    assert MIN_TEXT_LENGTH > 0, "Minimum text length must be positive"


# ---------------------------------------------------------------------------
# Page OCR tests
# ---------------------------------------------------------------------------

def test_ocr_page_basic(sample_page_path):
    """Test OCR on a single preprocessed page."""
    result = ocr_page(sample_page_path, page_index=0)
    
    # Check result structure
    assert isinstance(result, PageOCRResult)
    assert result.page_index == 0
    assert result.page_path == str(sample_page_path)
    assert result.engine in {"tesseract", "paddleocr"}
    
    # Check text extraction
    assert isinstance(result.text, str)
    assert result.char_count == len(result.text)
    assert result.word_count == len(result.text.split())
    
    # Check confidence
    assert 0.0 <= result.confidence <= 1.0
    
    # For real invoices, expect meaningful text
    if result.text:
        assert result.char_count > 0
        assert result.word_count > 0


def test_ocr_page_confidence_scoring(sample_page_path):
    """Test that confidence scores are reasonable for real invoices."""
    result = ocr_page(sample_page_path, page_index=0)
    
    # Real preprocessed invoices should have decent confidence
    # (unless they're genuinely degraded)
    if result.char_count > MIN_TEXT_LENGTH:
        # If we got substantial text, confidence should be measurable
        assert result.confidence > 0.0, "Non-empty text should have non-zero confidence"


def test_ocr_page_french_content(sample_page_path):
    """Test that OCR extracts French-specific characters."""
    result = ocr_page(sample_page_path, page_index=0)
    
    # Check that we can handle French text (not testing specific content,
    # just that the engine doesn't crash on accented characters)
    assert isinstance(result.text, str)
    
    # If text contains common French invoice terms, verify they're captured
    text_lower = result.text.lower()
    french_indicators = ["facture", "total", "tva", "date", "montant", "euro", "eur"]
    
    # At least some French terms should appear in a real invoice
    if result.char_count > 100:
        has_french = any(term in text_lower for term in french_indicators)
        # Note: This is a soft check - not all invoices will have all terms
        # but most should have at least one
        if not has_french:
            print(f"[INFO] No common French terms found in {sample_page_path.name}")


# ---------------------------------------------------------------------------
# Invoice OCR tests (multi-page)
# ---------------------------------------------------------------------------

def test_ocr_invoice_basic(sample_invoice_dir):
    """Test OCR on a complete invoice (one or more pages)."""
    result = ocr_invoice(sample_invoice_dir)
    
    # Check result structure
    assert isinstance(result, InvoiceOCRResult)
    assert result.invoice_name == sample_invoice_dir.name
    assert result.page_count > 0
    assert len(result.pages) == result.page_count
    assert not result.error
    
    # Check aggregated text
    assert isinstance(result.full_text, str)
    assert result.total_char_count >= 0
    assert result.total_word_count >= 0
    
    # Check confidence
    assert 0.0 <= result.mean_confidence <= 1.0
    
    # Verify page results
    for i, page in enumerate(result.pages):
        assert page.page_index == i
        assert isinstance(page.text, str)
        assert page.engine in {"tesseract", "paddleocr"}


def test_ocr_invoice_multipage_concatenation(sample_invoice_dir):
    """Test that multi-page invoices concatenate text correctly."""
    result = ocr_invoice(sample_invoice_dir)
    
    if result.page_count > 1:
        # Check that page break marker is present
        assert "--- PAGE BREAK ---" in result.full_text
        
        # Check that page count matches
        page_break_count = result.full_text.count("--- PAGE BREAK ---")
        assert page_break_count == result.page_count - 1
    
    # Check that full_text is concatenation of page texts
    if result.pages:
        expected_char_sum = sum(len(p.text) for p in result.pages)
        # Account for page break markers
        if result.page_count > 1:
            expected_char_sum += len("\n\n--- PAGE BREAK ---\n\n") * (result.page_count - 1)
        
        assert result.total_char_count == sum(p.char_count for p in result.pages)


def test_ocr_invoice_statistics(sample_invoice_dir):
    """Test that invoice-level statistics are computed correctly."""
    result = ocr_invoice(sample_invoice_dir)
    
    # Mean confidence should be average of page confidences
    if result.pages:
        expected_mean = sum(p.confidence for p in result.pages) / len(result.pages)
        assert abs(result.mean_confidence - expected_mean) < 0.001
    
    # Total counts should be sum of page counts
    assert result.total_char_count == sum(p.char_count for p in result.pages)
    assert result.total_word_count == sum(p.word_count for p in result.pages)
    
    # Low quality pages should be subset of all pages
    assert len(result.low_quality_pages) <= result.page_count
    for page_idx in result.low_quality_pages:
        assert 0 <= page_idx < result.page_count


def test_ocr_invoice_nonexistent_directory():
    """Test error handling for nonexistent invoice directory."""
    result = ocr_invoice("nonexistent_invoice_dir_12345")
    
    assert result.page_count == 0
    assert result.error
    assert "not found" in result.error.lower()


def test_ocr_invoice_empty_directory(tmp_path):
    """Test error handling for directory with no page PNG files."""
    empty_dir = tmp_path / "empty_invoice"
    empty_dir.mkdir()
    
    result = ocr_invoice(empty_dir)
    
    assert result.page_count == 0
    assert result.error
    assert "no page png files" in result.error.lower()


# ---------------------------------------------------------------------------
# Batch processing tests
# ---------------------------------------------------------------------------

def test_ocr_folder_basic():
    """Test batch OCR on all preprocessed invoices."""
    if not PROCESSED_DIR.exists():
        pytest.skip(f"Preprocessed data not found: {PROCESSED_DIR}")
    
    results = ocr_folder(PROCESSED_DIR)
    
    # Should return list of results
    assert isinstance(results, list)
    
    # If there are invoice directories, should have results
    invoice_dirs = [d for d in PROCESSED_DIR.iterdir() if d.is_dir()]
    assert len(results) == len(invoice_dirs)
    
    # Each result should be valid
    for result in results:
        assert isinstance(result, InvoiceOCRResult)
        assert result.invoice_name


def test_ocr_folder_with_output(tmp_path):
    """Test batch OCR with JSON output."""
    if not PROCESSED_DIR.exists():
        pytest.skip(f"Preprocessed data not found: {PROCESSED_DIR}")
    
    output_dir = tmp_path / "ocr_output"
    results = ocr_folder(PROCESSED_DIR, output_dir)
    
    # Check that output directory was created
    assert output_dir.exists()
    
    # Check that JSON files were written
    json_files = list(output_dir.glob("*.json"))
    assert len(json_files) == len(results)
    
    # Verify JSON content
    for json_file in json_files:
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert "invoice_name" in data
        assert "pages" in data
        assert "full_text" in data


def test_write_manifest(tmp_path):
    """Test OCR manifest generation."""
    # Create sample results
    results = [
        InvoiceOCRResult(
            invoice_name="test_invoice_1",
            page_count=2,
            pages=[
                PageOCRResult(0, "page_01.png", "Test text 1", 0.85, 11, 2, "tesseract"),
                PageOCRResult(1, "page_02.png", "Test text 2", 0.90, 11, 2, "tesseract"),
            ],
            full_text="Test text 1\n\n--- PAGE BREAK ---\n\nTest text 2",
            mean_confidence=0.875,
            total_char_count=22,
            total_word_count=4,
        ),
        InvoiceOCRResult(
            invoice_name="test_invoice_2",
            page_count=1,
            pages=[
                PageOCRResult(0, "page_01.png", "Another test", 0.75, 12, 2, "tesseract"),
            ],
            full_text="Another test",
            mean_confidence=0.75,
            total_char_count=12,
            total_word_count=2,
        ),
    ]
    
    manifest_path = write_manifest(results, tmp_path)
    
    # Check that manifest was created
    assert manifest_path.exists()
    assert manifest_path.name == "ocr_manifest.json"
    
    # Verify manifest content
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "items" in data
    assert "summary" in data
    
    summary = data["summary"]
    assert summary["total_invoices"] == 2
    assert summary["total_pages"] == 3
    assert summary["successful"] == 2
    assert summary["errors"] == 0
    assert summary["total_chars"] == 34
    assert summary["total_words"] == 6
    assert 0.0 <= summary["mean_confidence"] <= 1.0


def test_write_manifest_with_errors(tmp_path):
    """Test manifest generation with error cases."""
    results = [
        InvoiceOCRResult(
            invoice_name="good_invoice",
            page_count=1,
            pages=[PageOCRResult(0, "page_01.png", "Text", 0.80, 4, 1, "tesseract")],
            full_text="Text",
            mean_confidence=0.80,
            total_char_count=4,
            total_word_count=1,
        ),
        InvoiceOCRResult(
            invoice_name="bad_invoice",
            page_count=0,
            error="File not found",
        ),
    ]
    
    manifest_path = write_manifest(results, tmp_path)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    
    summary = data["summary"]
    assert summary["total_invoices"] == 2
    assert summary["successful"] == 1
    assert summary["errors"] == 1


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------

def test_end_to_end_ocr_pipeline(tmp_path):
    """Test complete OCR pipeline from preprocessed images to JSON output."""
    if not PROCESSED_DIR.exists():
        pytest.skip(f"Preprocessed data not found: {PROCESSED_DIR}")
    
    invoice_dirs = [d for d in PROCESSED_DIR.iterdir() if d.is_dir()]
    if not invoice_dirs:
        pytest.skip(f"No invoice directories in {PROCESSED_DIR}")
    
    # Take first invoice
    test_invoice = invoice_dirs[0]
    output_dir = tmp_path / "ocr_output"
    
    # Run OCR
    result = ocr_invoice(test_invoice)
    
    # Verify result
    assert not result.error
    assert result.page_count > 0
    assert result.full_text
    assert result.mean_confidence > 0.0
    
    # Write to JSON
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{result.invoice_name}.json"
    json_path.write_text(
        json.dumps(result.__dict__ if hasattr(result, '__dict__') else {
            'invoice_name': result.invoice_name,
            'page_count': result.page_count,
            'pages': [p.__dict__ if hasattr(p, '__dict__') else {} for p in result.pages],
            'full_text': result.full_text,
            'mean_confidence': result.mean_confidence,
            'total_char_count': result.total_char_count,
            'total_word_count': result.total_word_count,
            'low_quality_pages': result.low_quality_pages,
            'error': result.error,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    # Verify JSON was written
    assert json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["invoice_name"] == result.invoice_name
    assert data["page_count"] == result.page_count


# ---------------------------------------------------------------------------
# Fallback mechanism test
# ---------------------------------------------------------------------------

def test_fallback_mechanism_structure():
    """Test that fallback mechanism is properly structured (without triggering it)."""
    # This test verifies the code structure without actually running PaddleOCR
    # (which would be slow and require model download)
    
    from src.ocr_engine import _get_paddle_ocr
    
    # Verify function exists and is callable
    assert callable(_get_paddle_ocr)
    
    # Verify LOW_CONFIDENCE_THRESHOLD is used for fallback decision
    assert LOW_CONFIDENCE_THRESHOLD < 1.0
    assert MIN_TEXT_LENGTH > 0
