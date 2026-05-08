# OCR Engine — Task 7

Module: [`src/ocr_engine.py`](../src/ocr_engine.py)  
CLI: `python -m src.ocr_engine --input data/processed --output outputs/ocr_results`

Extracts text from preprocessed French invoice images using Tesseract OCR with French language pack, with automatic fallback to PaddleOCR for low-confidence pages.

---

## What it does

The OCR engine takes preprocessed invoice images (output from Task 6) and extracts text with confidence scoring. It handles multi-page invoices and provides structured output ready for the rule-based extractor (Task 8).

| Step | Purpose | Implementation |
|------|---------|---------------|
| 1. Load preprocessed image | Read the clean, binarised 300-DPI PNG from Task 6 | `PIL.Image.open()` |
| 2. Primary OCR | Extract text using Tesseract with French language pack | `pytesseract.image_to_string(lang='fra')` |
| 3. Confidence scoring | Calculate mean confidence across all detected words | `pytesseract.image_to_data()` with confidence extraction |
| 4. Fallback decision | If confidence < 60% or text < 50 chars, trigger PaddleOCR | Threshold-based logic |
| 5. PaddleOCR fallback | Re-OCR the page with PaddleOCR French model | `PaddleOCR(lang='fr')` |
| 6. Multi-page aggregation | Concatenate page texts with page break markers | Join with `\n\n--- PAGE BREAK ---\n\n` |
| 7. Statistics | Calculate invoice-level metrics (confidence, char/word counts) | Aggregate from page results |

---

## Output structure

### Single page result

```python
PageOCRResult(
    page_index=0,
    page_path="data/processed/Invoice_FR_016/page_01.png",
    text="FACTURE N° EFM-2023-0412\nDate: 12/11/2023\n...",
    confidence=0.87,
    char_count=1245,
    word_count=189,
    engine="tesseract",
    fallback_triggered=False
)
```

### Complete invoice result

```python
InvoiceOCRResult(
    invoice_name="Invoice_FR_016_scanned_260508_103316",
    page_count=1,
    pages=[PageOCRResult(...)],
    full_text="FACTURE N° EFM-2023-0412\nDate: 12/11/2023\n...",
    mean_confidence=0.87,
    total_char_count=1245,
    total_word_count=189,
    low_quality_pages=[],
    error=""
)
```

### Output JSON (written to disk)

```json
{
  "invoice_name": "Invoice_FR_016_scanned_260508_103316",
  "page_count": 1,
  "pages": [
    {
      "page_index": 0,
      "page_path": "data/processed/Invoice_FR_016/page_01.png",
      "text": "FACTURE N° EFM-2023-0412\nDate: 12/11/2023\n...",
      "confidence": 0.87,
      "char_count": 1245,
      "word_count": 189,
      "engine": "tesseract",
      "fallback_triggered": false
    }
  ],
  "full_text": "FACTURE N° EFM-2023-0412\nDate: 12/11/2023\n...",
  "mean_confidence": 0.87,
  "total_char_count": 1245,
  "total_word_count": 189,
  "low_quality_pages": [],
  "error": ""
}
```

---

## Configuration

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `TESSERACT_LANG` | `"fra"` | French language pack (mandatory for accents) |
| `TESSERACT_CONFIG` | `"--psm 1 --oem 3"` | PSM 1 = auto page segmentation with OSD; OEM 3 = default LSTM engine |
| `LOW_CONFIDENCE_THRESHOLD` | `0.60` | Below this, trigger PaddleOCR fallback |
| `MIN_TEXT_LENGTH` | `50` | Pages with fewer chars are flagged as suspicious |

---

## Fallback mechanism

The engine uses a two-tier OCR strategy:

1. **Primary: Tesseract** — Fast, accurate for clean scans
2. **Fallback: PaddleOCR** — Slower but better for degraded images

**Fallback triggers when:**
- Tesseract confidence < 60% **AND**
- Extracted text < 50 characters

**Fallback logic:**
```python
if confidence < 0.60 and len(text) < 50:
    paddle_text, paddle_conf = paddleocr_ocr(image)
    if paddle_conf > confidence or len(paddle_text) > len(text):
        use_paddle_result()
```

PaddleOCR is lazy-loaded on first fallback to avoid startup overhead when not needed.

---

## Multi-page handling

Multi-page invoices are processed in order and concatenated:

```
Page 1 text
\n\n--- PAGE BREAK ---\n\n
Page 2 text
\n\n--- PAGE BREAK ---\n\n
Page 3 text
```

The page break marker allows Task 8 (extractor) to:
- Prefer page 1 for header fields (supplier, invoice number, date)
- Search all pages for line items and totals
- Handle multi-page invoices as a single entity

---

## Quality indicators

### Per-page confidence

- **> 0.80** — Excellent OCR quality
- **0.60 – 0.80** — Good quality, minor errors expected
- **< 0.60** — Low quality, fallback triggered

### Low-quality page detection

Pages are flagged as low-quality if:
- Confidence < 60% **OR**
- Character count < 50

These pages are listed in `low_quality_pages` for manual review.

---

## Public API

```python
from src.ocr_engine import ocr_page, ocr_invoice, ocr_folder

# Single page
page_result = ocr_page(Path("data/processed/Invoice_FR_016/page_01.png"), page_index=0)

# Complete invoice (all pages)
invoice_result = ocr_invoice("data/processed/Invoice_FR_016")

# Batch processing
results = ocr_folder("data/processed", output_dir="outputs/ocr_results")
```

---

## CLI usage

### Process all invoices

```bash
python -m src.ocr_engine --input data/processed --output outputs/ocr_results
```

Output:
- One JSON file per invoice in `outputs/ocr_results/`
- Manifest file: `outputs/ocr_results/ocr_manifest.json`

### Process single invoice

```bash
python -m src.ocr_engine --input data/processed --output outputs/ocr_results --single data/processed/Invoice_FR_016
```

---

## OCR manifest

The manifest provides batch-level statistics:

```json
{
  "items": [ /* array of InvoiceOCRResult objects */ ],
  "summary": {
    "total_invoices": 19,
    "total_pages": 23,
    "successful": 19,
    "errors": 0,
    "mean_confidence": 0.78,
    "total_chars": 45678,
    "total_words": 7890,
    "low_quality_invoices": 2,
    "paddleocr_fallbacks": 3
  }
}
```

---

## Error handling

### Missing Tesseract

```
RuntimeError: Tesseract OCR failed: TesseractNotFoundError
```

**Solution:** Install Tesseract and French language pack (see README Task 5).

### Missing French language pack

Symptoms:
- Accents replaced with `?` or wrong glyphs
- Very low confidence scores
- Missing entity fields in extraction

**Solution:**
```bash
# Windows
# Download fra.traineddata to C:\Program Files\Tesseract-OCR\tessdata\

# macOS
brew install tesseract-lang

# Linux
sudo apt-get install tesseract-ocr-fra
```

Verify:
```bash
tesseract --list-langs
# Should show 'fra' in the list
```

### PaddleOCR fallback fails

If PaddleOCR fails, the engine falls back to the Tesseract result with a warning:

```
[WARNING] PaddleOCR fallback failed for page_01.png: <error message>
```

This is non-fatal — the Tesseract result is used.

---

## Performance

Typical processing times (on a modern CPU):

| Invoice type | Pages | Tesseract | PaddleOCR | Total |
|--------------|-------|-----------|-----------|-------|
| Clean PDF | 1 | 0.5s | — | 0.5s |
| Scanned PDF | 1 | 0.8s | — | 0.8s |
| Phone photo | 1 | 1.0s | — | 1.0s |
| Degraded photo | 1 | 1.2s | +3.5s | 4.7s |
| Multi-page (5 pages) | 5 | 4.0s | — | 4.0s |

**Batch processing:** ~1.5s per page average (19 invoices, 23 pages = ~35s total).

---

## Tests

`tests/test_ocr_engine.py` covers:
- Configuration constants
- Single page OCR
- Multi-page concatenation
- Confidence scoring
- French character handling
- Error cases (missing directory, empty directory)
- Batch processing
- Manifest generation
- End-to-end pipeline

```bash
python -m pytest tests/test_ocr_engine.py -v
```

**Note:** Most tests skip when preprocessed data is not available (expected for privacy reasons).

---

## Integration with Task 8

The OCR engine output feeds directly into the rule-based extractor:

```python
from src.ocr_engine import ocr_invoice
from src.extractor import extract_entities  # Task 8

# OCR
ocr_result = ocr_invoice("data/processed/Invoice_FR_016")

# Extract entities
entities = extract_entities(ocr_result.full_text, ocr_result.invoice_name)
```

The extractor uses:
- `full_text` for regex matching
- `page` boundaries for field prioritization
- `confidence` for quality warnings
- `invoice_name` for output file naming

---

## Known limitations

1. **Handwritten text** — Both Tesseract and PaddleOCR struggle with handwriting. Invoices with handwritten notes may have incomplete extraction.

2. **Complex layouts** — Tables with merged cells or rotated text may have reading-order issues. The preprocessor's deskew helps but doesn't solve all cases.

3. **Accent recovery** — Even with the French language pack, heavily degraded scans may lose accents. The Task 8 extractor compensates with accent-tolerant regex.

4. **Number confusion** — `O`/`0`, `I`/`1`/`l`, `S`/`5` confusion is common. Task 8 applies digit normalization for numeric fields (SIRET, amounts).

5. **Multi-column layouts** — Tesseract's reading order may jump between columns. For invoices with side-by-side sections, bounding-box-aware extraction (future enhancement) would help.

---

## Future enhancements (post-Milestone 1)

- **Bounding box extraction** — Return word/line coordinates for layout-aware extraction
- **Table structure detection** — Preserve table grid for line items
- **Confidence-weighted extraction** — Prioritize high-confidence text in Task 8
- **GPU acceleration** — Enable PaddleOCR GPU mode for faster fallback
- **Language auto-detection** — Support mixed French/English invoices
