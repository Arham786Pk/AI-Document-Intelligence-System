"""Smoke tests for the preprocessing module.

These run against the French-invoice dataset committed under
``data/Images/`` (JPGs) and ``data/Scanned_PDF/`` (PDFs). They are skipped
when neither folder is populated.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.preprocessor import (
    DEGRADED_THRESHOLD,
    detect_source_type,
    preprocess_invoice,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = [
    ROOT / "data" / "Images",
    ROOT / "data" / "Scanned_PDF",
]


def _has_dataset() -> bool:
    return any(d.exists() and any(d.iterdir()) for d in SOURCE_DIRS)


pytestmark = pytest.mark.skipif(
    not _has_dataset(),
    reason="data/Images/ and data/Scanned_PDF/ are both empty",
)


def _sample(*candidates: str) -> Path:
    for name in candidates:
        for d in SOURCE_DIRS:
            path = d / name
            if path.exists():
                return path
    pytest.skip(f"None of {candidates} present in dataset")


def test_detect_scanned_pdf():
    sample = _sample(
        "Invoice_FR_016_scanned_260508_103316.pdf",
        "Invoice_FR_017_scanned_260508_103241.pdf",
    )
    assert detect_source_type(sample) == "scanned_pdf"


def test_detect_image():
    sample = _sample("IMG-20260507-WA0148.jpg", "IMG-20260507-WA0143.jpg")
    assert detect_source_type(sample) == "image"


def test_preprocess_pdf_writes_pages(tmp_path):
    sample = _sample("Invoice_FR_016_scanned_260508_103316.pdf")
    result = preprocess_invoice(sample, tmp_path)
    assert result.page_count >= 1
    for page in result.pages:
        assert Path(page.output_path).exists()
        assert page.dpi == 300
        assert page.width > 0 and page.height > 0
    assert 0.0 <= result.invoice_quality_score <= 1.0


def test_preprocess_image_writes_one_page(tmp_path):
    sample = _sample("IMG-20260507-WA0148.jpg")
    result = preprocess_invoice(sample, tmp_path)
    assert result.page_count == 1
    page = result.pages[0]
    assert Path(page.output_path).exists()
    assert page.dpi == 300


def test_quality_threshold_constant():
    assert 0.0 < DEGRADED_THRESHOLD < 1.0
