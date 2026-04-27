"""OCR engine for Milestone 1.

Extracts text from preprocessed page images using Tesseract (primary)
and PaddleOCR (fallback for low-confidence results). Outputs structured
text with confidence scores and bounding boxes for downstream extraction.
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import cv2
import fitz  # pymupdf
import numpy as np
import pytesseract
from paddleocr import PaddleOCR

log = logging.getLogger(__name__)

# Configure Tesseract path for Windows if not in PATH
if sys.platform == "win32":
    candidate_paths = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"D:\scoop\apps\tesseract\current\tesseract.exe"),
        Path.home() / "scoop" / "apps" / "tesseract" / "current" / "tesseract.exe",
    ]
    for tesseract_path in candidate_paths:
        if tesseract_path.exists():
            pytesseract.pytesseract.tesseract_cmd = str(tesseract_path)
            break

# Tesseract configuration
TESSERACT_CONFIG = r"--oem 3 --psm 3"  # LSTM engine, auto page segmentation
TESSERACT_LANG = "fra+eng"  # bilingual: handles both FR and EN docs in one pass
CONFIDENCE_THRESHOLD = 60.0  # below this, try PaddleOCR fallback

# PaddleOCR configuration (lazy-loaded)
_paddle_ocr: PaddleOCR | None = None


@dataclass
class OCRWord:
    """Single word with position and confidence."""
    text: str
    confidence: float
    bbox: tuple[int, int, int, int]  # (x, y, width, height)


@dataclass
class OCRResult:
    """Complete OCR result for one page."""
    page_path: Path
    full_text: str
    words: list[OCRWord]
    avg_confidence: float
    engine: Literal["tesseract", "paddleocr"]


def _get_paddle_ocr() -> PaddleOCR:
    """Lazy-load PaddleOCR (heavy model download on first use)."""
    global _paddle_ocr
    if _paddle_ocr is None:
        log.info("initialising PaddleOCR (first use may download models)")
        _paddle_ocr = PaddleOCR(
            use_angle_cls=True,  # detect rotated text
            lang="en",  # primary language (supports FR via latin model)
        )
    return _paddle_ocr


def _ocr_tesseract(img: np.ndarray) -> OCRResult | None:
    """Run Tesseract OCR with word-level detail."""
    try:
        data = pytesseract.image_to_data(
            img,
            config=TESSERACT_CONFIG,
            lang=TESSERACT_LANG,
            output_type=pytesseract.Output.DICT,
        )
    except Exception as e:
        log.warning("tesseract failed: %s", e)
        return None

    words: list[OCRWord] = []
    lines: list[str] = []
    confidences: list[float] = []

    for i, text in enumerate(data["text"]):
        text = text.strip()
        if not text:
            continue
        conf = float(data["conf"][i])
        if conf < 0:  # Tesseract returns -1 for non-text blocks
            continue
        x, y, w, h = (
            data["left"][i],
            data["top"][i],
            data["width"][i],
            data["height"][i],
        )
        words.append(OCRWord(text=text, confidence=conf, bbox=(x, y, w, h)))
        lines.append(text)
        confidences.append(conf)

    if not words:
        return None

    avg_conf = sum(confidences) / len(confidences)
    full_text = " ".join(lines)
    return OCRResult(
        page_path=Path(),  # filled by caller
        full_text=full_text,
        words=words,
        avg_confidence=avg_conf,
        engine="tesseract",
    )


def _ocr_paddleocr(img: np.ndarray) -> OCRResult | None:
    """Run PaddleOCR as fallback."""
    try:
        paddle = _get_paddle_ocr()
        result = paddle.ocr(img)
    except Exception as e:
        log.warning("paddleocr failed: %s", e)
        return None

    if not result or not result[0]:
        return None

    words: list[OCRWord] = []
    lines: list[str] = []
    confidences: list[float] = []

    for line in result[0]:
        bbox_points, (text, conf) = line
        text = text.strip()
        if not text:
            continue
        # Convert PaddleOCR's 4-point polygon to bounding box
        xs = [p[0] for p in bbox_points]
        ys = [p[1] for p in bbox_points]
        x, y = int(min(xs)), int(min(ys))
        w, h = int(max(xs) - x), int(max(ys) - y)

        words.append(OCRWord(text=text, confidence=conf * 100, bbox=(x, y, w, h)))
        lines.append(text)
        confidences.append(conf * 100)

    if not words:
        return None

    avg_conf = sum(confidences) / len(confidences)
    full_text = " ".join(lines)
    return OCRResult(
        page_path=Path(),  # filled by caller
        full_text=full_text,
        words=words,
        avg_confidence=avg_conf,
        engine="paddleocr",
    )


def ocr_page(
    image_path: str | Path,
    fallback_to_paddle: bool = True,
) -> OCRResult:
    """Extract text from a preprocessed page image.

    Args:
        image_path: Path to preprocessed PNG (from Task 6).
        fallback_to_paddle: If True and Tesseract confidence is low,
                           retry with PaddleOCR.

    Returns:
        OCRResult with full text, word-level details, and confidence.

    Raises:
        ValueError: If image cannot be read or both engines fail.
    """
    img_path = Path(image_path)
    if not img_path.exists():
        raise ValueError(f"image not found: {img_path}")

    img = cv2.imread(str(img_path))
    if img is None:
        raise ValueError(f"failed to read image: {img_path}")

    # Try Tesseract first
    result = _ocr_tesseract(img)
    if result is not None:
        result.page_path = img_path
        if result.avg_confidence >= CONFIDENCE_THRESHOLD:
            log.debug(
                "tesseract OK: %s (%.1f%% conf, %d words)",
                img_path.name,
                result.avg_confidence,
                len(result.words),
            )
            return result
        log.info(
            "tesseract low confidence (%.1f%%) on %s, trying paddleocr",
            result.avg_confidence,
            img_path.name,
        )

    # Fallback to PaddleOCR
    if fallback_to_paddle:
        paddle_result = _ocr_paddleocr(img)
        if paddle_result is not None:
            paddle_result.page_path = img_path
            log.info(
                "paddleocr fallback: %s (%.1f%% conf, %d words)",
                img_path.name,
                paddle_result.avg_confidence,
                len(paddle_result.words),
            )
            return paddle_result

    # If we got here, either Tesseract failed or both failed
    if result is not None:
        log.warning(
            "using low-confidence tesseract result for %s (%.1f%%)",
            img_path.name,
            result.avg_confidence,
        )
        return result

    raise ValueError(f"all OCR engines failed on {img_path}")


def extract_text_digital_pdf(pdf_path: str | Path) -> list[OCRResult]:
    """Direct text extraction for digital PDFs via PyMuPDF — no OCR.

    Per Project.pdf §3: digital PDFs have selectable text already, so OCR
    is wasteful and lossy. PyMuPDF reads the embedded text layer directly
    with perfect fidelity. Returns one OCRResult per page (engine field
    set to "tesseract" since downstream code keys off the literal type;
    word-level bboxes preserved from PyMuPDF's word coordinates).
    """
    pdf = Path(pdf_path)
    results: list[OCRResult] = []
    with fitz.open(pdf) as doc:
        for page_num, page in enumerate(doc, start=1):
            full_text = page.get_text("text") or ""
            words: list[OCRWord] = []
            for x0, y0, x1, y1, text, *_ in page.get_text("words"):
                t = text.strip()
                if not t:
                    continue
                words.append(OCRWord(
                    text=t,
                    confidence=100.0,  # direct extraction: no OCR uncertainty
                    bbox=(int(x0), int(y0), int(x1 - x0), int(y1 - y0)),
                ))
            results.append(OCRResult(
                page_path=Path(f"{pdf.stem}_p{page_num:02d}.pdf-text"),
                full_text=full_text.strip(),
                words=words,
                avg_confidence=100.0 if words else 0.0,
                engine="tesseract",
            ))
    return results


def ocr_document(
    page_paths: list[Path],
    fallback_to_paddle: bool = True,
) -> list[OCRResult]:
    """Run OCR on all pages of a document.

    Args:
        page_paths: List of preprocessed page PNGs (in order).
        fallback_to_paddle: Enable PaddleOCR fallback for low-confidence pages.

    Returns:
        List of OCRResult, one per page (same order as input).
    """
    results: list[OCRResult] = []
    for page_path in page_paths:
        try:
            result = ocr_page(page_path, fallback_to_paddle=fallback_to_paddle)
            results.append(result)
        except Exception as e:
            log.error("OCR failed on %s: %s", page_path.name, e)
            # Create empty result to maintain page order
            results.append(
                OCRResult(
                    page_path=page_path,
                    full_text="",
                    words=[],
                    avg_confidence=0.0,
                    engine="tesseract",
                )
            )
    return results
