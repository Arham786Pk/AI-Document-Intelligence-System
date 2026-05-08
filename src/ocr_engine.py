"""Task 7 — OCR text extraction engine for French invoices.

Extracts text from preprocessed invoice images using Tesseract OCR with French
language pack. Falls back to PaddleOCR when Tesseract confidence is below
threshold. Handles multi-page invoices and returns structured text with
confidence scores.

Per Milestone 1 spec:
  * Primary: Tesseract with 'fra' language pack (mandatory for accents).
  * Fallback: PaddleOCR for low-confidence pages (< 60% mean confidence).
  * Multi-page: concatenate text in page order, preserve page boundaries.
  * Output: structured text with per-page confidence, bounding boxes optional.

Usage:
    from src.ocr_engine import ocr_invoice, ocr_folder

    result = ocr_invoice("data/processed/Invoice_FR_016_scanned_260508_103316")
    print(result.full_text)
    print(f"Confidence: {result.mean_confidence:.2%}")

    # CLI:
    #   python -m src.ocr_engine --input data/processed \
    #                            --output outputs/ocr_results
"""
from __future__ import annotations

import argparse
import json
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

import pytesseract
from PIL import Image

# Suppress PaddleOCR verbose logging
warnings.filterwarnings("ignore")
import logging
logging.getLogger("ppocr").setLevel(logging.ERROR)

# PaddleOCR lazy-loaded on first fallback
_PADDLE_OCR = None

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TESSERACT_LANG = "fra"
TESSERACT_CONFIG = "--psm 1 --oem 3"  # PSM 1 = auto page segmentation with OSD
LOW_CONFIDENCE_THRESHOLD = 0.60  # below this, trigger PaddleOCR fallback
MIN_TEXT_LENGTH = 50  # pages with fewer chars are flagged as suspicious


@dataclass
class PageOCRResult:
    """OCR result for a single page."""
    page_index: int
    page_path: str
    text: str
    confidence: float
    char_count: int
    word_count: int
    engine: Literal["tesseract", "paddleocr"]
    fallback_triggered: bool = False


@dataclass
class InvoiceOCRResult:
    """OCR result for a complete invoice (one or more pages)."""
    invoice_name: str
    page_count: int
    pages: list[PageOCRResult] = field(default_factory=list)
    full_text: str = ""
    mean_confidence: float = 0.0
    total_char_count: int = 0
    total_word_count: int = 0
    low_quality_pages: list[int] = field(default_factory=list)
    error: str = ""


# ---------------------------------------------------------------------------
# Tesseract OCR
# ---------------------------------------------------------------------------

def _tesseract_ocr(image_path: Path) -> tuple[str, float]:
    """Run Tesseract OCR with French language pack.
    
    Returns:
        (text, confidence) where confidence is in [0, 1].
    """
    try:
        img = Image.open(image_path)
        
        # Extract text
        text = pytesseract.image_to_string(
            img,
            lang=TESSERACT_LANG,
            config=TESSERACT_CONFIG
        )
        
        # Get confidence scores per word
        data = pytesseract.image_to_data(
            img,
            lang=TESSERACT_LANG,
            config=TESSERACT_CONFIG,
            output_type=pytesseract.Output.DICT
        )
        
        # Calculate mean confidence (filter out -1 values which indicate no text)
        confidences = [
            float(conf) for conf in data["conf"]
            if conf != -1 and str(conf).strip() and float(conf) >= 0
        ]
        
        if confidences:
            mean_conf = sum(confidences) / len(confidences) / 100.0  # normalize to [0, 1]
        else:
            mean_conf = 0.0
        
        return text.strip(), mean_conf
        
    except Exception as e:
        raise RuntimeError(f"Tesseract OCR failed: {e}") from e


# ---------------------------------------------------------------------------
# PaddleOCR fallback
# ---------------------------------------------------------------------------

def _get_paddle_ocr():
    """Lazy-load PaddleOCR instance (downloads French model on first use)."""
    global _PADDLE_OCR
    if _PADDLE_OCR is None:
        from paddleocr import PaddleOCR
        _PADDLE_OCR = PaddleOCR(
            lang="fr",
            use_angle_cls=True,
            show_log=False,
            use_gpu=False
        )
    return _PADDLE_OCR


def _paddleocr_ocr(image_path: Path) -> tuple[str, float]:
    """Run PaddleOCR as fallback for low-confidence Tesseract results.
    
    Returns:
        (text, confidence) where confidence is in [0, 1].
    """
    try:
        ocr = _get_paddle_ocr()
        result = ocr.ocr(str(image_path), cls=True)
        
        if not result or not result[0]:
            return "", 0.0
        
        # Extract text and confidence from PaddleOCR result
        # Format: [[[bbox], (text, confidence)], ...]
        lines = []
        confidences = []
        
        for line in result[0]:
            if line and len(line) >= 2:
                text_info = line[1]
                if isinstance(text_info, (tuple, list)) and len(text_info) >= 2:
                    text, conf = text_info[0], text_info[1]
                    lines.append(text)
                    confidences.append(float(conf))
        
        full_text = "\n".join(lines)
        mean_conf = sum(confidences) / len(confidences) if confidences else 0.0
        
        return full_text.strip(), mean_conf
        
    except Exception as e:
        raise RuntimeError(f"PaddleOCR failed: {e}") from e


# ---------------------------------------------------------------------------
# Page OCR with fallback logic
# ---------------------------------------------------------------------------

def ocr_page(page_path: Path, page_index: int) -> PageOCRResult:
    """OCR a single preprocessed page with automatic fallback.
    
    Args:
        page_path: Path to the preprocessed PNG image.
        page_index: Zero-based page index.
    
    Returns:
        PageOCRResult with text, confidence, and metadata.
    """
    # Try Tesseract first
    text, confidence = _tesseract_ocr(page_path)
    engine = "tesseract"
    fallback_triggered = False
    
    # Fallback to PaddleOCR if confidence is low
    if confidence < LOW_CONFIDENCE_THRESHOLD and len(text) < MIN_TEXT_LENGTH:
        try:
            paddle_text, paddle_conf = _paddleocr_ocr(page_path)
            # Use PaddleOCR result if it's better
            if paddle_conf > confidence or len(paddle_text) > len(text):
                text = paddle_text
                confidence = paddle_conf
                engine = "paddleocr"
                fallback_triggered = True
        except Exception as e:
            # If PaddleOCR fails, stick with Tesseract result
            print(f"[WARNING] PaddleOCR fallback failed for {page_path.name}: {e}")
    
    # Calculate statistics
    char_count = len(text)
    word_count = len(text.split())
    
    return PageOCRResult(
        page_index=page_index,
        page_path=str(page_path),
        text=text,
        confidence=confidence,
        char_count=char_count,
        word_count=word_count,
        engine=engine,
        fallback_triggered=fallback_triggered
    )


# ---------------------------------------------------------------------------
# Invoice OCR (multi-page)
# ---------------------------------------------------------------------------

def ocr_invoice(invoice_dir: str | Path) -> InvoiceOCRResult:
    """OCR all pages of a preprocessed invoice.
    
    Args:
        invoice_dir: Path to the invoice directory containing page_*.png files.
                     Example: data/processed/Invoice_FR_016_scanned_260508_103316/
    
    Returns:
        InvoiceOCRResult with concatenated text and per-page details.
    """
    invoice_dir = Path(invoice_dir)
    invoice_name = invoice_dir.name
    
    if not invoice_dir.exists() or not invoice_dir.is_dir():
        return InvoiceOCRResult(
            invoice_name=invoice_name,
            page_count=0,
            error=f"Invoice directory not found: {invoice_dir}"
        )
    
    # Find all page PNG files (sorted by page number)
    page_files = sorted(invoice_dir.glob("page_*.png"))
    
    if not page_files:
        return InvoiceOCRResult(
            invoice_name=invoice_name,
            page_count=0,
            error=f"No page PNG files found in {invoice_dir}"
        )
    
    # OCR each page
    pages: list[PageOCRResult] = []
    for i, page_path in enumerate(page_files):
        try:
            page_result = ocr_page(page_path, i)
            pages.append(page_result)
        except Exception as e:
            # Create error page result
            pages.append(PageOCRResult(
                page_index=i,
                page_path=str(page_path),
                text="",
                confidence=0.0,
                char_count=0,
                word_count=0,
                engine="tesseract",
                fallback_triggered=False
            ))
            print(f"[ERROR] OCR failed for {page_path.name}: {e}")
    
    # Aggregate results
    full_text = "\n\n--- PAGE BREAK ---\n\n".join(p.text for p in pages if p.text)
    mean_confidence = sum(p.confidence for p in pages) / len(pages) if pages else 0.0
    total_char_count = sum(p.char_count for p in pages)
    total_word_count = sum(p.word_count for p in pages)
    low_quality_pages = [
        p.page_index for p in pages
        if p.confidence < LOW_CONFIDENCE_THRESHOLD or p.char_count < MIN_TEXT_LENGTH
    ]
    
    return InvoiceOCRResult(
        invoice_name=invoice_name,
        page_count=len(pages),
        pages=pages,
        full_text=full_text,
        mean_confidence=mean_confidence,
        total_char_count=total_char_count,
        total_word_count=total_word_count,
        low_quality_pages=low_quality_pages
    )


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def ocr_folder(input_dir: str | Path, output_dir: str | Path | None = None) -> list[InvoiceOCRResult]:
    """OCR all invoices in a preprocessed folder.
    
    Args:
        input_dir: Path to data/processed/ containing invoice subdirectories.
        output_dir: Optional path to write individual JSON files per invoice.
    
    Returns:
        List of InvoiceOCRResult objects.
    """
    input_dir = Path(input_dir)
    results: list[InvoiceOCRResult] = []
    
    # Find all invoice directories (skip files like preprocessing_manifest.json)
    invoice_dirs = sorted([d for d in input_dir.iterdir() if d.is_dir()])
    
    if not invoice_dirs:
        print(f"[WARNING] No invoice directories found in {input_dir}")
        return results
    
    print(f"Found {len(invoice_dirs)} invoices to process...")
    
    for invoice_dir in invoice_dirs:
        print(f"Processing {invoice_dir.name}...", end=" ")
        result = ocr_invoice(invoice_dir)
        results.append(result)
        
        if result.error:
            print(f"ERROR: {result.error}")
        else:
            print(f"OK ({result.page_count} pages, {result.total_char_count} chars, "
                  f"{result.mean_confidence:.1%} confidence)")
        
        # Write individual JSON if output directory specified
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            json_path = output_dir / f"{invoice_dir.name}.json"
            json_path.write_text(
                json.dumps(asdict(result), indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
    
    return results


def write_manifest(results: list[InvoiceOCRResult], output_dir: str | Path) -> Path:
    """Write OCR manifest with summary statistics.
    
    Args:
        results: List of InvoiceOCRResult objects.
        output_dir: Directory to write the manifest.
    
    Returns:
        Path to the written manifest file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "ocr_manifest.json"
    
    # Build manifest
    payload = {
        "items": [asdict(r) for r in results],
        "summary": {
            "total_invoices": len(results),
            "total_pages": sum(r.page_count for r in results),
            "successful": sum(1 for r in results if not r.error),
            "errors": sum(1 for r in results if r.error),
            "mean_confidence": round(
                sum(r.mean_confidence for r in results if not r.error) / 
                max(1, sum(1 for r in results if not r.error)),
                3
            ),
            "total_chars": sum(r.total_char_count for r in results),
            "total_words": sum(r.total_word_count for r in results),
            "low_quality_invoices": sum(1 for r in results if r.low_quality_pages),
            "paddleocr_fallbacks": sum(
                sum(1 for p in r.pages if p.fallback_triggered)
                for r in results
            ),
        }
    }
    
    manifest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    return manifest_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="OCR French invoices using Tesseract + PaddleOCR fallback."
    )
    parser.add_argument(
        "--input",
        default="data/processed",
        help="Folder of preprocessed invoices (output from Task 6)."
    )
    parser.add_argument(
        "--output",
        default="outputs/ocr_results",
        help="Folder to write OCR JSON files and manifest."
    )
    parser.add_argument(
        "--single",
        default=None,
        help="Process a single invoice directory instead of the whole folder."
    )
    args = parser.parse_args()
    
    if args.single:
        # Single invoice mode
        result = ocr_invoice(args.single)
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        
        # Write to output directory
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / f"{result.invoice_name}.json"
        json_path.write_text(
            json.dumps(asdict(result), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"\nWrote {json_path}")
        return
    
    # Batch mode
    results = ocr_folder(args.input, args.output)
    manifest = write_manifest(results, args.output)
    
    # Print summary
    summary = json.loads(manifest.read_text(encoding="utf-8"))["summary"]
    print(f"\n{'='*60}")
    print(f"OCR Complete - Wrote {manifest}")
    print(f"{'='*60}")
    print(f"  Total invoices:        {summary['total_invoices']}")
    print(f"  Total pages:           {summary['total_pages']}")
    print(f"  Successful:            {summary['successful']}")
    print(f"  Errors:                {summary['errors']}")
    print(f"  Mean confidence:       {summary['mean_confidence']:.1%}")
    print(f"  Total characters:      {summary['total_chars']:,}")
    print(f"  Total words:           {summary['total_words']:,}")
    print(f"  Low quality invoices:  {summary['low_quality_invoices']}")
    print(f"  PaddleOCR fallbacks:   {summary['paddleocr_fallbacks']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    _cli()
