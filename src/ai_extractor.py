"""Milestone 2 — LayoutLMv3-based entity extractor for French invoices.

Uses a fine-tuned LayoutLMv3 token-classification model to extract 12 entity
fields from invoice images / PDFs.  The model was trained on 25 BIO labels
(see ``data/funsd/labels.txt``) produced by ``scripts/build_funsd_dataset.py``.

Output format is identical to the rule-based extractor in ``src/extractor.py``
so that both backends are interchangeable in downstream pipelines.

Public API
----------
- ``extract_entities_ai``   — single-document extraction
- ``extract_from_folder_ai`` — batch-process a folder of images/PDFs

CLI
---
::

    python -m src.ai_extractor --input data/images --output outputs/extracted_ai \\
                               --model models/layoutlmv3/best
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any

from PIL import Image

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Graceful import of heavy ML dependencies
# ---------------------------------------------------------------------------

_TRANSFORMERS_AVAILABLE = False

try:
    import torch
    from transformers import (
        AutoModelForTokenClassification,
        LayoutLMv3Processor,
    )
    _TRANSFORMERS_AVAILABLE = True
except ImportError:  # pragma: no cover
    logger.warning(
        "transformers and/or torch are not installed.  "
        "The AI extractor will not be available.  "
        "Install with:  pip install transformers torch"
    )

# ---------------------------------------------------------------------------
# Constants — BIO label set (must match data/funsd/labels.txt)
# ---------------------------------------------------------------------------

LABELS: list[str] = [
    "O",
    "B-SUPPLIER_NAME",  "I-SUPPLIER_NAME",
    "B-CONSUMER_NAME",  "I-CONSUMER_NAME",
    "B-INVOICE_NUMBER", "I-INVOICE_NUMBER",
    "B-INVOICE_DATE",   "I-INVOICE_DATE",
    "B-SIRET",          "I-SIRET",
    "B-ECHEANCE",       "I-ECHEANCE",
    "B-INVOICE_CONTENT","I-INVOICE_CONTENT",
    "B-TVA_PERCENTAGE", "I-TVA_PERCENTAGE",
    "B-TVA_AMOUNT",     "I-TVA_AMOUNT",
    "B-TOTAL_AMOUNT",   "I-TOTAL_AMOUNT",
    "B-PAYMENT_STATUS", "I-PAYMENT_STATUS",
    "B-SOLDE_DU",       "I-SOLDE_DU",
]
ID2LABEL: dict[int, str] = {i: l for i, l in enumerate(LABELS)}
LABEL2ID: dict[str, int] = {l: i for i, l in enumerate(LABELS)}

# Entity names that map to simple string fields in the output dict.
_SIMPLE_ENTITIES: list[str] = [
    "SUPPLIER_NAME", "CONSUMER_NAME", "INVOICE_NUMBER", "INVOICE_DATE",
    "SIRET", "ECHEANCE", "TVA_PERCENTAGE", "TVA_AMOUNT",
    "TOTAL_AMOUNT", "PAYMENT_STATUS", "SOLDE_DU",
]

# Supported image extensions (for folder scanning)
_IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

# Payment-status keyword mapping (mirrors src/extractor.py logic)
_PAID_KEYWORDS = re.compile(
    r"(?i)\b(pay[eé]|r[eé]gl[eé]|sold[eé]|acquitt[eé]|encaiss[eé]|re[çc]u"
    r"|visa|mastercard|cb|carte\s*bleue|carte\s*bancaire|amex"
    r"|american\s*express|esp[eè]ces)\b"
)
_UNPAID_KEYWORDS = re.compile(
    r"(?i)\b(non\s*pay[eé]|impay[eé]|en\s*attente|reste)\b"
)


# ---------------------------------------------------------------------------
# PDF → PIL helper (pymupdf / fitz)
# ---------------------------------------------------------------------------

def _pdf_to_image(pdf_path: Path, dpi: int = 150) -> Image.Image:
    """Render page 1 of a PDF as a PIL Image at the given DPI.

    Uses pymupdf (``fitz``).  Raises ``RuntimeError`` if fitz is unavailable.
    """
    try:
        import fitz  # pymupdf
    except ImportError as exc:
        raise RuntimeError(
            "pymupdf (fitz) is required for PDF support.  "
            "Install with:  pip install pymupdf"
        ) from exc

    doc = fitz.open(str(pdf_path))
    try:
        pix = doc[0].get_pixmap(dpi=dpi)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    finally:
        doc.close()
    return img


# ---------------------------------------------------------------------------
# Word-level OCR
# ---------------------------------------------------------------------------

def _ocr_words(image: Image.Image) -> tuple[list[str], list[list[int]]]:
    """Run word-level OCR with pytesseract.

    Returns
    -------
    words : list[str]
        The recognised word strings.
    boxes : list[list[int]]
        Bounding boxes normalised to the 0-1000 LayoutLM coordinate space,
        each as ``[x0, y0, x1, y1]``.
    """
    import pytesseract

    W, H = image.size
    if W == 0 or H == 0:
        logger.warning("Image has zero width or height — skipping OCR.")
        return [], []

    data = pytesseract.image_to_data(
        image, lang="fra+eng", output_type=pytesseract.Output.DICT
    )

    words: list[str] = []
    boxes: list[list[int]] = []

    for i, txt in enumerate(data["text"]):
        txt = txt.strip()
        if not txt:
            continue
        x, y, w, h = (
            data["left"][i],
            data["top"][i],
            data["width"][i],
            data["height"][i],
        )
        # Normalise to 0-1000 (same formula as build_funsd_dataset.py)
        x0 = int(1000 * x / W)
        y0 = int(1000 * y / H)
        x1 = int(1000 * (x + w) / W)
        y1 = int(1000 * (y + h) / H)

        # Clamp to valid range
        x0 = max(0, min(1000, x0))
        y0 = max(0, min(1000, y0))
        x1 = max(0, min(1000, x1))
        y1 = max(0, min(1000, y1))

        words.append(txt)
        boxes.append([x0, y0, x1, y1])

    return words, boxes


# ---------------------------------------------------------------------------
# Model loading (cached)
# ---------------------------------------------------------------------------

# Simple module-level cache so the model is loaded only once per process.
_MODEL_CACHE: dict[str, tuple[Any, Any]] = {}


def _load_model(
    model_dir: str | Path,
) -> tuple["LayoutLMv3Processor", "AutoModelForTokenClassification"]:
    """Load (and cache) the fine-tuned LayoutLMv3 model + processor.

    Parameters
    ----------
    model_dir : str | Path
        Local directory containing the saved model weights, config, and
        tokenizer files.

    Returns
    -------
    processor, model
    """
    if not _TRANSFORMERS_AVAILABLE:
        raise RuntimeError(
            "transformers/torch not installed — cannot load LayoutLMv3.  "
            "Install with:  pip install transformers torch"
        )

    model_dir = Path(model_dir).resolve()
    cache_key = str(model_dir)

    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]

    if not model_dir.exists():
        raise FileNotFoundError(
            f"Model directory not found: {model_dir}.  "
            f"Train the model first or update --model path."
        )

    logger.info("Loading LayoutLMv3 model from %s …", model_dir)

    processor = LayoutLMv3Processor.from_pretrained(
        str(model_dir), apply_ocr=False
    )
    model = AutoModelForTokenClassification.from_pretrained(
        str(model_dir),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    model.eval()

    _MODEL_CACHE[cache_key] = (processor, model)
    logger.info("Model loaded successfully (%d labels).", len(LABELS))
    return processor, model


# ---------------------------------------------------------------------------
# Inference helpers
# ---------------------------------------------------------------------------

def _predict_tags(
    words: list[str],
    boxes: list[list[int]],
    image: Image.Image,
    processor: "LayoutLMv3Processor",
    model: "AutoModelForTokenClassification",
) -> list[str]:
    """Run LayoutLMv3 inference and return one BIO tag per OCR word.

    The processor may split a single word into multiple sub-tokens.  We take
    the prediction of the **first** sub-token of each word as the word-level
    label (standard approach for token-classification with sub-word models).
    """
    if not words:
        return []

    encoding = processor(
        image,
        words,
        boxes=boxes,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding="max_length",
    )

    with torch.no_grad():
        outputs = model(**encoding)

    logits = outputs.logits  # (1, seq_len, num_labels)
    preds = torch.argmax(logits, dim=-1).squeeze(0).tolist()

    # Map sub-token predictions back to word-level
    word_ids = encoding.word_ids(batch_index=0)
    word_tags: list[str] = ["O"] * len(words)
    seen_word_ids: set[int | None] = set()

    for token_idx, word_id in enumerate(word_ids):
        if word_id is None:
            continue  # special tokens ([CLS], [SEP], [PAD])
        if word_id in seen_word_ids:
            continue  # take only first sub-token per word
        seen_word_ids.add(word_id)
        if word_id < len(word_tags):
            pred_id = preds[token_idx]
            word_tags[word_id] = ID2LABEL.get(pred_id, "O")

    return word_tags


# ---------------------------------------------------------------------------
# BIO → entity values
# ---------------------------------------------------------------------------

def _classify_payment_status(raw_text: str) -> str:
    """Map raw tagged text to PAID / UNPAID / UNKNOWN.

    Uses the same keyword signals as ``src/extractor.extract_payment_status``.
    """
    if _PAID_KEYWORDS.search(raw_text):
        return "PAID"
    if _UNPAID_KEYWORDS.search(raw_text):
        return "UNPAID"
    return "UNKNOWN"


def _bio_to_entities(
    words: list[str], tags: list[str]
) -> dict[str, Any]:
    """Convert word-level BIO tags into a structured entity dict.

    For most entities the consecutive B-/I- words are joined by spaces.
    Special handling:

    * **INVOICE_CONTENT** — each B-INVOICE_CONTENT starts a new line item;
      the result is ``[{"description": ...}, ...]``.
    * **PAYMENT_STATUS** — the tagged text is mapped to PAID/UNPAID/UNKNOWN.

    Returns the same dict shape as ``src/extractor.extract_entities``.
    """
    # Collect raw spans: { entity_name: [ [word, word, …], … ] }
    spans: dict[str, list[list[str]]] = {e: [] for e in _SIMPLE_ENTITIES}
    spans["INVOICE_CONTENT"] = []

    current_entity: str | None = None

    for word, tag in zip(words, tags):
        if tag.startswith("B-"):
            entity = tag[2:]
            if entity in spans:
                spans[entity].append([word])
                current_entity = entity
            else:
                current_entity = None
        elif tag.startswith("I-"):
            entity = tag[2:]
            if entity == current_entity and spans[entity]:
                spans[entity][-1].append(word)
            # If I- without matching B-, ignore (noisy prediction)
        else:
            current_entity = None

    # Build output dict
    result: dict[str, Any] = {}

    for entity in _SIMPLE_ENTITIES:
        if not spans[entity]:
            result[entity.lower()] = ""
            continue
        # Take the first span (most confident / earliest)
        value = " ".join(spans[entity][0])

        if entity == "PAYMENT_STATUS":
            value = _classify_payment_status(value)

        result[entity.lower()] = value

    # Invoice content: each span is a separate line item
    content_items: list[dict[str, str]] = []
    for span_words in spans["INVOICE_CONTENT"]:
        desc = " ".join(span_words).strip()
        if desc:
            content_items.append({"description": desc})
    result["invoice_content"] = content_items

    return result


# ---------------------------------------------------------------------------
# Open image / PDF
# ---------------------------------------------------------------------------

def _open_document(path: Path) -> Image.Image:
    """Open an invoice document as a PIL Image.

    Supports PDF (page 1 rendered at 150 DPI) and common image formats.
    """
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _pdf_to_image(path, dpi=150)
    if suffix in _IMAGE_EXTENSIONS:
        return Image.open(path).convert("RGB")
    raise ValueError(
        f"Unsupported file format '{suffix}' for {path.name}.  "
        f"Expected .pdf or one of {sorted(_IMAGE_EXTENSIONS)}."
    )


# ===================================================================
# Public API
# ===================================================================

def extract_entities_ai(
    image_or_pdf_path: str | Path,
    model_dir: str | Path = "models/layoutlmv3/best",
) -> dict[str, Any]:
    """Extract invoice entities from a single document using LayoutLMv3.

    Parameters
    ----------
    image_or_pdf_path : str | Path
        Path to an invoice image (PNG/JPG/TIFF/BMP) or PDF.
    model_dir : str | Path
        Local directory with the fine-tuned LayoutLMv3 model.

    Returns
    -------
    dict
        Entity dict with keys: ``file_name``, ``supplier_name``,
        ``consumer_name``, ``invoice_number``, ``invoice_date``, ``siret``,
        ``echeance``, ``invoice_content``, ``tva_percentage``, ``tva_amount``,
        ``total_amount``, ``payment_status``, ``solde_du``.

    Raises
    ------
    RuntimeError
        If transformers/torch is not installed.
    FileNotFoundError
        If the model directory or input file does not exist.
    """
    if not _TRANSFORMERS_AVAILABLE:
        raise RuntimeError(
            "transformers/torch not installed — AI extractor unavailable.  "
            "Install with:  pip install transformers torch"
        )

    path = Path(image_or_pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    logger.info("Processing %s …", path.name)

    # 1. Load model (cached after first call)
    processor, model = _load_model(model_dir)

    # 2. Open document
    image = _open_document(path)

    # 3. Word-level OCR
    words, boxes = _ocr_words(image)
    if not words:
        logger.warning("No words detected by OCR in %s — returning empty.", path.name)
        return _empty_result(path.name)

    logger.debug("OCR returned %d words.", len(words))

    # 4. Inference
    tags = _predict_tags(words, boxes, image, processor, model)

    # 5. BIO → structured entities
    entities = _bio_to_entities(words, tags)
    entities["file_name"] = path.name

    # Ensure payment_status has a value
    if not entities.get("payment_status"):
        entities["payment_status"] = "UNKNOWN"

    return entities


def extract_from_folder_ai(
    input_dir: str | Path,
    output_dir: str | Path,
    model_dir: str | Path = "models/layoutlmv3/best",
) -> list[dict[str, Any]]:
    """Batch-extract entities from all invoices in a folder.

    Scans *input_dir* for PDFs and image files, runs ``extract_entities_ai``
    on each, writes one JSON per document to *output_dir*, and returns the
    list of results.

    Parameters
    ----------
    input_dir : str | Path
        Folder containing invoice images / PDFs.
    output_dir : str | Path
        Folder to write per-document JSON results.
    model_dir : str | Path
        Local directory with the fine-tuned LayoutLMv3 model.

    Returns
    -------
    list[dict]
        List of entity dicts (one per document).
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Gather candidate files
    candidates = sorted(
        f
        for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in (_IMAGE_EXTENSIONS | {".pdf"})
    )

    if not candidates:
        print(f"[WARNING] No image/PDF files found in {input_dir}")
        return []

    print(f"Found {len(candidates)} document(s) to process …")

    results: list[dict[str, Any]] = []

    for idx, filepath in enumerate(candidates, 1):
        print(f"[{idx}/{len(candidates)}] {filepath.name} …", end=" ")
        try:
            entities = extract_entities_ai(filepath, model_dir=model_dir)
            results.append(entities)

            # Write individual JSON
            out_path = output_dir / f"{filepath.stem}.json"
            out_path.write_text(
                json.dumps(entities, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            filled = sum(
                1 for k, v in entities.items()
                if v and k != "file_name"
            )
            print(f"OK ({filled}/12 fields)")
        except Exception as exc:
            logger.exception("Failed to process %s", filepath.name)
            print(f"ERROR: {exc}")
            # Still record an empty result so downstream counts are correct
            results.append(_empty_result(filepath.name))

    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_result(file_name: str) -> dict[str, Any]:
    """Return a result dict with all fields set to empty defaults."""
    return {
        "file_name": file_name,
        "supplier_name": "",
        "consumer_name": "",
        "invoice_number": "",
        "invoice_date": "",
        "siret": "",
        "echeance": "",
        "invoice_content": [],
        "tva_percentage": "",
        "tva_amount": "",
        "total_amount": "",
        "payment_status": "UNKNOWN",
        "solde_du": "",
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    """Command-line interface for the AI extractor."""
    parser = argparse.ArgumentParser(
        description="Extract invoice entities using a fine-tuned LayoutLMv3 model."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input directory containing invoice images/PDFs.",
    )
    parser.add_argument(
        "--output",
        default="outputs/extracted_ai",
        help="Output directory for per-document JSON files.",
    )
    parser.add_argument(
        "--model",
        default="models/layoutlmv3/best",
        help="Path to the fine-tuned LayoutLMv3 model directory.",
    )
    args = parser.parse_args()

    if not _TRANSFORMERS_AVAILABLE:
        print(
            "[ERROR] transformers and/or torch are not installed.\n"
            "Install with:  pip install transformers torch"
        )
        return

    results = extract_from_folder_ai(args.input, args.output, model_dir=args.model)

    print(f"\n{'=' * 60}")
    print("AI Extraction Complete")
    print(f"{'=' * 60}")
    print(f"  Total documents: {len(results)}")
    print(f"  Output:          {args.output}")
    print(f"  Model:           {args.model}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    _cli()
