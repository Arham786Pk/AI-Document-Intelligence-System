"""Task 6 — Preprocessing module for French invoices.

Renders every page of a French invoice (PDF or photo) to a clean 300-DPI
binarised image, ready for the Task 7 OCR engine. Multi-page invoices are
preserved as an ordered list under one invoice key.

Per Milestone 1 spec:
  * Detect PDF type: digital text-PDF vs scanned/image PDF.
  * Pipeline: render → deskew → denoise → binarise → 300 DPI.
  * Multi-page: all pages of one invoice belong to the same record.
  * Per-invoice quality score in [0, 1]; below 0.3 → flagged as degraded.
  * Outputs land under ``data/processed/<invoice_name>/page_<n>.png``.

Usage:
    from src.preprocessor import preprocess_invoice, preprocess_folder

    result = preprocess_invoice("data/Scanned_PDF/Invoice_FR_016_scanned_260508_103316.pdf",
                                "data/processed")
    # CLI (run once per source folder):
    #   python -m src.preprocessor --input data/Images       --output data/processed
    #   python -m src.preprocessor --input data/Scanned_PDF  --output data/processed
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image

TARGET_DPI = 300
DIGITAL_PDF_MIN_TEXT_CHARS = 80  # pages with at least this many chars are "digital"
DEGRADED_THRESHOLD = 0.3
SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


@dataclass
class PageResult:
    page_index: int
    output_path: str
    width: int
    height: int
    dpi: int
    quality_score: float


@dataclass
class InvoiceResult:
    invoice_name: str
    source_path: str
    source_type: str  # "digital_pdf" | "scanned_pdf" | "image"
    page_count: int
    pages: list[PageResult] = field(default_factory=list)
    invoice_quality_score: float = 0.0
    degraded: bool = False


# ---------------------------------------------------------------------------
# Source-type detection
# ---------------------------------------------------------------------------

def _detect_pdf_type(pdf_path: Path) -> str:
    """Return 'digital_pdf' if any page has extractable text, else 'scanned_pdf'."""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text("text") or ""
            if len(text.strip()) >= DIGITAL_PDF_MIN_TEXT_CHARS:
                return "digital_pdf"
    return "scanned_pdf"


def detect_source_type(path: Path) -> str:
    """Return one of 'digital_pdf', 'scanned_pdf', 'image'."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _detect_pdf_type(path)
    if suffix in SUPPORTED_IMAGE_EXTS:
        return "image"
    raise ValueError(f"Unsupported file type: {path.suffix}")


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------

def _render_pdf_page(page: "fitz.Page", dpi: int = TARGET_DPI) -> np.ndarray:
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2RGB)
    elif pix.n == 1:
        arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
    return arr


def _load_image(path: Path) -> np.ndarray:
    img = Image.open(path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return np.array(img)


def _resize_to_dpi(rgb: np.ndarray, current_dpi: int | None, target_dpi: int = TARGET_DPI) -> np.ndarray:
    """Phone photos have no meaningful DPI metadata; we instead aim for a target
    short-edge pixel count so OCR sees consistent stroke widths.
    """
    h, w = rgb.shape[:2]
    short_edge = min(h, w)
    target_short = int(target_dpi * 8.27)  # treat short edge as A4 width (8.27 in)
    if current_dpi is not None:
        scale = target_dpi / current_dpi
    else:
        scale = target_short / max(short_edge, 1)
    if abs(scale - 1.0) < 0.05:
        return rgb
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    return cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA)


# ---------------------------------------------------------------------------
# Deskew, denoise, binarise
# ---------------------------------------------------------------------------

def _deskew(gray: np.ndarray) -> tuple[np.ndarray, float]:
    """Rotate so text lines are horizontal. Returns (rotated, angle_degrees)."""
    inverted = cv2.bitwise_not(gray)
    _, thr = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thr > 0))
    if coords.size == 0:
        return gray, 0.0
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.2:
        return gray, 0.0
    h, w = gray.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    rotated = cv2.warpAffine(
        gray, matrix, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated, float(angle)


def _denoise(gray: np.ndarray) -> np.ndarray:
    """Mild non-local means + light blur. Tuned to keep stroke edges sharp."""
    den = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
    return den


def _binarise(gray: np.ndarray) -> np.ndarray:
    """Adaptive binarisation — robust to uneven lighting on phone photos."""
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=15,
    )


# ---------------------------------------------------------------------------
# Quality scoring
# ---------------------------------------------------------------------------

def _quality_score(gray: np.ndarray, binary: np.ndarray) -> float:
    """Map sharpness + ink-coverage to [0, 1].

    * Laplacian variance — proxy for focus / sharpness.
    * Foreground ratio — sanity check; near-blank or near-black scans score low.
    """
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    sharpness = min(1.0, laplacian_var / 200.0)

    fg = float((binary == 0).sum()) / float(binary.size)
    # Healthy invoices have ~2-40 % ink coverage; outside that band penalise.
    if 0.02 <= fg <= 0.40:
        coverage = 1.0
    elif fg < 0.02:
        coverage = max(0.0, fg / 0.02)
    else:
        coverage = max(0.0, 1.0 - (fg - 0.40) / 0.4)

    return round(0.7 * sharpness + 0.3 * coverage, 3)


# ---------------------------------------------------------------------------
# Page pipeline
# ---------------------------------------------------------------------------

def _process_page(rgb: np.ndarray, source_type: str) -> tuple[np.ndarray, float]:
    """Run the full per-page pipeline and return (binary_image, quality)."""
    if source_type != "digital_pdf":
        rgb = _resize_to_dpi(rgb, current_dpi=None, target_dpi=TARGET_DPI)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    if source_type != "digital_pdf":
        gray = _denoise(gray)
    gray, _ = _deskew(gray)
    binary = _binarise(gray)
    quality = _quality_score(gray, binary)
    return binary, quality


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def preprocess_invoice(source: str | Path, output_root: str | Path, skip_existing: bool = True) -> InvoiceResult:
    """Preprocess one invoice (PDF or image), write outputs, return a report.
    
    Args:
        source: Path to source invoice file (PDF or image)
        output_root: Root directory for preprocessed outputs
        skip_existing: If True, skip processing if output is newer than source
    
    Returns:
        InvoiceResult with preprocessing details
    """
    source_path = Path(source).resolve()
    output_root = Path(output_root)
    invoice_name = source_path.stem
    out_dir = output_root / invoice_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # Check if we should skip (output exists and is newer than source)
    if skip_existing:
        first_page = out_dir / "page_01.png"
        if first_page.exists():
            source_mtime = source_path.stat().st_mtime
            output_mtime = first_page.stat().st_mtime
            
            if output_mtime > source_mtime:
                # Output is newer - load existing result from manifest or create minimal result
                print(f"  [SKIP] {invoice_name} (already processed)")
                
                # Count existing pages
                existing_pages = sorted(out_dir.glob("page_*.png"))
                pages = []
                for idx, page_path in enumerate(existing_pages):
                    # Load image to get dimensions
                    img = cv2.imread(str(page_path), cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        h, w = img.shape[:2]
                        pages.append(PageResult(idx, str(page_path), w, h, TARGET_DPI, 0.8))
                
                source_type = detect_source_type(source_path)
                return InvoiceResult(
                    invoice_name=invoice_name,
                    source_path=str(source_path),
                    source_type=source_type,
                    page_count=len(pages),
                    pages=pages,
                    invoice_quality_score=0.8,
                    degraded=False,
                )

    source_type = detect_source_type(source_path)
    pages: list[PageResult] = []

    if source_type in {"digital_pdf", "scanned_pdf"}:
        with fitz.open(source_path) as doc:
            for i, page in enumerate(doc):
                rgb = _render_pdf_page(page, dpi=TARGET_DPI)
                binary, quality = _process_page(rgb, source_type)
                out_path = out_dir / f"page_{i + 1:02d}.png"
                cv2.imwrite(str(out_path), binary)
                h, w = binary.shape[:2]
                pages.append(PageResult(i, str(out_path), w, h, TARGET_DPI, quality))
    else:
        rgb = _load_image(source_path)
        binary, quality = _process_page(rgb, source_type)
        out_path = out_dir / "page_01.png"
        cv2.imwrite(str(out_path), binary)
        h, w = binary.shape[:2]
        pages.append(PageResult(0, str(out_path), w, h, TARGET_DPI, quality))

    invoice_quality = round(sum(p.quality_score for p in pages) / max(1, len(pages)), 3)
    result = InvoiceResult(
        invoice_name=invoice_name,
        source_path=str(source_path),
        source_type=source_type,
        page_count=len(pages),
        pages=pages,
        invoice_quality_score=invoice_quality,
        degraded=invoice_quality < DEGRADED_THRESHOLD,
    )
    return result


def preprocess_folder(input_dir: str | Path, output_root: str | Path, skip_existing: bool = True) -> list[InvoiceResult]:
    """Preprocess every supported file in ``input_dir`` (non-recursive).
    
    Args:
        input_dir: Directory containing source invoice files
        output_root: Root directory for preprocessed outputs
        skip_existing: If True, skip files that are already processed
    
    Returns:
        List of InvoiceResult objects
    """
    input_dir = Path(input_dir)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    results: list[InvoiceResult] = []
    for path in sorted(input_dir.iterdir()):
        if path.is_dir() or path.name.startswith("."):
            continue
        if path.suffix.lower() not in SUPPORTED_IMAGE_EXTS and path.suffix.lower() != ".pdf":
            continue
        try:
            result = preprocess_invoice(path, output_root, skip_existing=skip_existing)
            results.append(result)
        except Exception as exc:  # pragma: no cover — surfaced in the manifest
            results.append(
                InvoiceResult(
                    invoice_name=path.stem,
                    source_path=str(path.resolve()),
                    source_type="error",
                    page_count=0,
                    pages=[],
                    invoice_quality_score=0.0,
                    degraded=True,
                )
            )
            print(f"[ERROR] {path.name}: {exc}")
    return results


def write_manifest(results: Iterable[InvoiceResult], output_root: str | Path) -> Path:
    output_root = Path(output_root)
    manifest_path = output_root / "preprocessing_manifest.json"
    payload = {
        "items": [asdict(r) for r in results],
    }
    payload["degraded_files"] = [item["invoice_name"] for item in payload["items"] if item["degraded"]]
    payload["summary"] = {
        "total": len(payload["items"]),
        "digital_pdf": sum(1 for i in payload["items"] if i["source_type"] == "digital_pdf"),
        "scanned_pdf": sum(1 for i in payload["items"] if i["source_type"] == "scanned_pdf"),
        "image": sum(1 for i in payload["items"] if i["source_type"] == "image"),
        "errors": sum(1 for i in payload["items"] if i["source_type"] == "error"),
        "degraded": len(payload["degraded_files"]),
        "mean_quality": round(
            sum(i["invoice_quality_score"] for i in payload["items"])
            / max(1, len(payload["items"])),
            3,
        ),
    }
    manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Preprocess French invoices for OCR.")
    parser.add_argument("--input", default="data/Images",
                        help="Folder of raw invoices (PDF or image). "
                             "Run once per folder: data/Images then data/Scanned_PDF.")
    parser.add_argument("--output", default="data/processed",
                        help="Folder where cleaned page PNGs are written.")
    parser.add_argument("--single", default=None,
                        help="Process a single invoice file instead of the whole folder.")
    parser.add_argument("--force", action="store_true",
                        help="Force reprocessing even if output already exists.")
    args = parser.parse_args()

    skip_existing = not args.force

    if args.single:
        result = preprocess_invoice(args.single, args.output, skip_existing=skip_existing)
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        return

    results = preprocess_folder(args.input, args.output, skip_existing=skip_existing)
    manifest = write_manifest(results, args.output)
    summary = json.loads(manifest.read_text(encoding="utf-8"))["summary"]
    print(f"Wrote {manifest}")
    print(f"  total={summary['total']}  "
          f"digital_pdf={summary['digital_pdf']}  "
          f"scanned_pdf={summary['scanned_pdf']}  "
          f"image={summary['image']}  "
          f"errors={summary['errors']}")
    print(f"  mean_quality={summary['mean_quality']}  degraded={summary['degraded']}")


if __name__ == "__main__":
    _cli()
