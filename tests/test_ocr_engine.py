"""Smoke test for OCR engine — runs on the first available preprocessed page."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ocr_engine import ocr_page  # noqa: E402


def _first_existing_page() -> Path:
    processed = ROOT / "data" / "processed"
    if not processed.exists():
        raise RuntimeError(
            "data/processed/ not found — run 'python src/run_preprocess.py' first"
        )
    pages = sorted(processed.glob("*.png"))
    if not pages:
        raise RuntimeError("no page PNGs found in data/processed/")
    return pages[0]


def test_ocr_one_page():
    page = _first_existing_page()
    result = ocr_page(page, fallback_to_paddle=True)

    assert result.page_path == page
    assert result.full_text, "expected non-empty text"
    assert result.words, "expected at least one word"
    assert 0 <= result.avg_confidence <= 100
    assert result.engine in ("tesseract", "paddleocr")

    # Check word structure
    for word in result.words[:5]:  # check first 5 words
        assert word.text
        assert 0 <= word.confidence <= 100
        assert len(word.bbox) == 4
        assert all(isinstance(v, int) for v in word.bbox)

    print(f"✓ OCR OK: {page.name}")
    print(f"  Engine: {result.engine}")
    print(f"  Confidence: {result.avg_confidence:.1f}%")
    print(f"  Words: {len(result.words)}")
    print(f"  Text preview: {result.full_text[:100]}...")


if __name__ == "__main__":
    test_ocr_one_page()
    print("OK")
