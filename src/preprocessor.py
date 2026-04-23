"""Document preprocessor for Milestone 1.

Renders PDF pages to PNG and applies OCR-friendly cleanup
(grayscale -> deskew -> denoise -> adaptive threshold) for scanned modality.
Digital modality uses a light path (render only) since text is already crisp.
"""
from __future__ import annotations

import logging
from pathlib import Path

import cv2
import fitz  # pymupdf
import numpy as np

DPI = 300
ZOOM = DPI / 72.0  # pymupdf uses 72 dpi base

log = logging.getLogger(__name__)


def _render_pdf_pages(pdf_path: Path) -> list[np.ndarray]:
    """Render every page of a PDF to a BGR numpy array at DPI."""
    pages: list[np.ndarray] = []
    with fitz.open(pdf_path) as doc:
        mat = fitz.Matrix(ZOOM, ZOOM)
        for page in doc:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )
            if pix.n == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            pages.append(img)
    return pages


def _deskew(gray: np.ndarray) -> np.ndarray:
    """Estimate text-block skew via minAreaRect on dark pixels and rotate."""
    inv = cv2.bitwise_not(gray)
    coords = np.column_stack(np.where(inv > 0))
    if coords.size == 0:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle
    if abs(angle) < 0.3:
        return gray
    h, w = gray.shape
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(
        gray, m, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def _clean_scanned(bgr: np.ndarray) -> np.ndarray:
    """Full OCR-prep: grayscale -> deskew -> denoise -> adaptive threshold."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = _deskew(gray)
    gray = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
        blockSize=31, C=15,
    )


def _clean_digital(bgr: np.ndarray) -> np.ndarray:
    """Light path: just grayscale. Digital PDFs render cleanly already."""
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)


def preprocess_document(
    input_path: str | Path,
    output_dir: str | Path,
    modality: str = "digital",
) -> list[Path]:
    """Preprocess one document. Returns list of saved PNG page paths.

    modality: "digital" (light path) or "scanned" (full clean).
    """
    in_path = Path(input_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if in_path.suffix.lower() != ".pdf":
        raise ValueError(f"Only PDF inputs supported in M1: {in_path}")

    pages = _render_pdf_pages(in_path)
    cleaner = _clean_scanned if modality == "scanned" else _clean_digital

    saved: list[Path] = []
    stem = in_path.stem
    for i, page in enumerate(pages, start=1):
        out = out_dir / f"{stem}_p{i:02d}.png"
        cv2.imwrite(str(out), cleaner(page))
        saved.append(out)
    log.info("preprocessed %s (%d pages, %s)", in_path.name, len(saved), modality)
    return saved
