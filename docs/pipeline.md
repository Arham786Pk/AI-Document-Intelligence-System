# Task 9 — Full Pipeline Integration

**Status:** ✅ Complete

## Overview

Task 9 integrates all three stages of the document intelligence system into a
unified pipeline that processes documents end-to-end:

```
PDF → [Preprocessing] → PNG pages → [OCR] → Text → [Extraction] → 5 entities
```

The pipeline provides:
- **Single entry point** for processing documents
- **Automatic stage chaining** with error handling
- **Comprehensive validation** and result tracking
- **Flexible execution** (single doc, batch, or full corpus)
- **Detailed reporting** with success/failure metrics

---

## Architecture

### Core Components

| Component | Purpose |
|-----------|---------|
| `src/pipeline.py` | Pipeline class with stage orchestration |
| `src/run.py` | Command-line runner for batch processing |
| `tests/test_pipeline.py` | Comprehensive test suite |

### Pipeline Class

The `Pipeline` class encapsulates the full workflow:

```python
from pipeline import Pipeline

pipeline = Pipeline(
    processed_dir=Path("data/processed"),
    ocr_output_dir=Path("outputs/ocr"),
    extraction_output_dir=Path("outputs/extracted"),
    fallback_to_paddle=True,
)

result = pipeline.run_document(
    source_path=Path("data/raw/used/digital_pdfs/Real_MaterialCert_FR_Larobinetterie_134822.pdf"),
    modality="digital",
    language="FR",
)

if result.success:
    print(f"Extracted: {result.extraction_result.project_id}")
else:
    print(f"Failed at {result.error_stage}: {result.error_message}")
```

### PipelineResult

Each document run returns a `PipelineResult` with:

```python
@dataclass
class PipelineResult:
    document_name: str
    source_path: Path
    success: bool
    
    # Stage status
    preprocessing_ok: bool
    ocr_ok: bool
    extraction_ok: bool
    
    # Outputs
    page_count: int
    preprocessed_pages: list[Path]
    ocr_results: list[OCRResult]
    extraction_result: ExtractionResult | None
    
    # Metadata
    avg_ocr_confidence: float
    total_text_length: int
    
    # Errors
    error_stage: str | None
    error_message: str | None
```

---

## Usage

### 1. Process All Ground-Truth Documents

```bash
python src/run.py
```

Processes all 20 documents from `docs/ground_truth.csv` and generates:
- Preprocessed pages in `data/processed/`
- OCR outputs in `outputs/ocr/`
- Extraction results in `outputs/extracted/`
- Pipeline summary in `outputs/pipeline_results/pipeline_run_YYYYMMDD_HHMMSS.json`

### 2. Process Single Document

```bash
python src/run.py --doc Real_MaterialCert_FR_Larobinetterie_134822.pdf
```

### 3. Process First N Documents

```bash
python src/run.py --limit 5
```

Useful for quick testing or incremental processing.

### 4. Show Summary from Last Run

```bash
python src/run.py --summary
```

Displays summary statistics without reprocessing.

### 5. Disable PaddleOCR Fallback

```bash
python src/run.py --no-paddle
```

Uses Tesseract only (faster but lower accuracy on degraded scans).

---

## Pipeline Stages

### Stage 1: Preprocessing

**Input:** PDF file  
**Output:** Cleaned page PNGs at 300 DPI  
**Module:** `src/preprocessor.py`

**Processing path:**
- **Digital PDFs** (16 of 20 docs in current GT): render → grayscale → save
- **Scanned PDFs** (4 of 20 docs in current GT): render → grayscale → deskew → denoise → threshold → save

**Failure modes:**
- PDF file not found or corrupted
- Insufficient disk space
- Invalid PDF structure

### Stage 2: OCR

**Input:** Page PNGs  
**Output:** Structured text with confidence scores  
**Module:** `src/ocr_engine.py`

**Processing:**
1. Run Tesseract on each page
2. If avg confidence < 60%, fallback to PaddleOCR
3. Extract word-level text, bounding boxes, and confidence scores
4. Save as `.txt` (human-readable) and `.json` (structured)

**Failure modes:**
- Tesseract not installed or not in PATH
- Image file corrupted or unreadable
- Out of memory (large documents)

### Stage 3: Extraction

**Input:** OCR text  
**Output:** 5 extracted entities  
**Module:** `src/extractor.py`

**Processing:**
1. Concatenate all pages' text
2. Detect language (EN or FR) from filename
3. Run regex + keyword extraction for each entity
4. Select best candidate per field based on confidence
5. Save as `.json` with all candidates

**Failure modes:**
- Empty or garbled OCR text
- No entity patterns matched
- Invalid date formats

---

## Output Files

### Pipeline Results

`outputs/pipeline_results/pipeline_run_YYYYMMDD_HHMMSS.json`:

```json
{
  "timestamp": "2026-04-27T12:03:21",
  "total_documents": 20,
  "successful": 20,
  "failed": 0,
  "stage_failures": {
    "preprocessing": 0,
    "ocr": 0,
    "extraction": 0
  },
  "avg_ocr_confidence": 85.0,
  "total_pages_processed": 51,
  "documents": [
    {
      "document_name": "Real_MaterialCert_FR_Larobinetterie_134822",
      "source_path": "data/raw/used/digital_pdfs/Real_MaterialCert_FR_Larobinetterie_134822.pdf",
      "success": true,
      "stages": {
        "preprocessing": true,
        "ocr": true,
        "extraction": true
      },
      "outputs": {
        "page_count": 1,
        "preprocessed_pages": ["data/processed/Real_MaterialCert_FR_Larobinetterie_134822_p01.png"],
        "avg_ocr_confidence": 100.0,
        "total_text_length": 1234
      },
      "extracted_entities": {
        "project_id": "134822",
        "supplier": "La Robinetterie (LRI-Sodime)",
        "material": "304L",
        "quantity": null,
        "date": "23/05/2019"
      },
      "error": null
    }
  ]
}
```

### Per-Document Outputs

For each document `<name>`:

| File | Content |
|------|---------|
| `data/processed/<name>_p01.png` | Preprocessed page 1 |
| `data/processed/<name>_p02.png` | Preprocessed page 2 (if multi-page) |
| `outputs/ocr/<name>.txt` | Human-readable OCR text |
| `outputs/ocr/<name>.json` | Structured OCR data (words, confidence, bboxes) |
| `outputs/extracted/<name>.json` | Extracted entities + all candidates |

---

## Error Handling

The pipeline uses **fail-fast** behavior: if any stage fails, subsequent stages
are skipped and the error is recorded in the `PipelineResult`.

### Error Recovery

```python
result = pipeline.run_document(source_path, modality="digital")

if not result.success:
    if result.error_stage == "preprocessing":
        # Check if PDF is corrupted or path is wrong
        print(f"Preprocessing failed: {result.error_message}")
    
    elif result.error_stage == "ocr":
        # Check if Tesseract is installed
        # Check if preprocessed images exist
        print(f"OCR failed: {result.error_message}")
    
    elif result.error_stage == "extraction":
        # Check if OCR text is empty or garbled
        print(f"Extraction failed: {result.error_message}")
```

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `Tesseract not found` | Tesseract not installed or not in PATH | Install Tesseract and verify with `tesseract --version` |
| `PDF file not found` | Wrong path or file moved | Check `data/raw/used/` directories |
| `Out of memory` | Large document or insufficient RAM | Process documents individually with `--doc` flag |
| `Empty OCR text` | Blank page or preprocessing failed | Check preprocessed PNGs in `data/processed/` |

---

## Validation

### Smoke Test

```bash
python tests/test_pipeline.py
```

Runs 4 tests:
1. **Initialization** — verifies output directories are created
2. **Result serialization** — tests `PipelineResult.to_dict()`
3. **Error handling** — validates error capture for invalid input
4. **End-to-end** — processes one real document through full pipeline

Expected output:
```
================================================================================
PIPELINE TEST SUITE (Task 9)
================================================================================

Running: Initialization
✓ Pipeline initialization test passed

Running: Result serialization
✓ PipelineResult serialization test passed

Running: Error handling
✓ Pipeline error handling test passed

Running: End-to-end
  Testing with: Real_MaterialCert_FR_Larobinetterie_134822.pdf
  ✓ Pipeline succeeded
    Pages: 1
    OCR confidence: 100.0%
    Text length: 1234 chars
✓ Pipeline end-to-end test passed

================================================================================
Results: 4 passed, 0 failed
================================================================================
```

### Full Pipeline Run

```bash
python src/run.py
```

Expected output:
```
14:30:00 [INFO] run: loaded 20 documents from ground truth
14:30:00 [INFO] pipeline: starting pipeline for Real_MaterialCert_FR_Larobinetterie_134822 (modality=digital, language=FR)
14:30:00 [INFO] pipeline:   [1/3] preprocessing...
14:30:01 [INFO] pipeline:   ✓ preprocessed 1 pages
14:30:01 [INFO] pipeline:   [2/3] direct PDF text extraction (digital fast path)...
14:30:01 [INFO] pipeline:   ✓ OCR complete (avg confidence: 100.0%)
14:30:01 [INFO] pipeline:   [3/3] extraction...
14:30:01 [INFO] pipeline:   ✓ extraction complete
14:30:01 [INFO] pipeline:     → project_id=134822, supplier=La Robinetterie (LRI-Sodime), material=304L, quantity=(none), date=23/05/2019
14:30:01 [INFO] pipeline: ✓ pipeline complete for Real_MaterialCert_FR_Larobinetterie_134822
...
14:33:00 [INFO] run: saved pipeline results: outputs/pipeline_results/pipeline_run_20260427_120321.json

================================================================================
PIPELINE SUMMARY
================================================================================

Total documents: 20
  ✓ Successful: 20 (100.0%)
  ✗ Failed: 0 (0.0%)

OCR average confidence: 85.0%
Total pages processed: 51

Extraction results (20 documents):
  • project_id: 12/20 (60.0%)
  • supplier: 16/20 (80.0%)
  • material: 18/20 (90.0%)
  • quantity: 14/20 (70.0%)
  • date: 16/20 (80.0%)

================================================================================
```

---

## Performance

### Timing (20 documents, 51 pages)

| Stage | Time | Per page |
|-------|------|----------|
| Preprocessing | ~15s | ~0.3s |
| Digital fast path (PyMuPDF) | <1s | <0.05s (16 of 20 docs) |
| OCR (Tesseract on 4 scanned docs) | ~10s | ~0.9s |
| OCR (PaddleOCR fallback) | ~15s | ~3.0s (rare) |
| Extraction | ~5s | ~0.05s |
| **Total** | **~1.5 min** | **~1.4s** |

### Resource Usage

- **CPU:** 1–4 cores (Tesseract is single-threaded, PaddleOCR uses 2–4)
- **RAM:** ~500 MB baseline + ~50 MB per page during OCR
- **Disk:** ~2 MB per page (preprocessed PNGs) + ~50 KB per document (OCR/extraction JSON)

### Optimization Tips

1. **Disable PaddleOCR fallback** if speed > accuracy: `--no-paddle`
2. **Process in batches** with `--limit` to avoid memory issues
3. **Use SSD** for `data/processed/` to speed up I/O
4. **Parallel processing** (future): run multiple documents concurrently

---

## Integration with Task 10

Task 10 (Metrics + Final Report) is **complete**. The flow is:
1. [`generator/build_results_report.py`](../generator/build_results_report.py) loads
   all 20 JSONs from `outputs/extracted/` and matches them against
   `docs/ground_truth.csv` row-by-row.
2. Per (doc × entity) pair, the comparator marks TP / FP / FN using
   field-specific normalisation (alphanumeric for IDs, ISO for dates,
   token-overlap ≥ 34% for free-text fields).
3. Precision / Recall / F1 are computed per entity and macro-averaged.
4. Six matplotlib charts are rendered to `outputs/report_assets/`.
5. The polished PDF report is built with reportlab and written to
   [`docs/Milestone1_Results_Report.pdf`](Milestone1_Results_Report.pdf).
6. Machine-readable scores are saved to [`outputs/metrics.json`](../outputs/metrics.json).

The pipeline outputs are designed to make Task 10 straightforward:
- All results in structured JSON
- Document names match ground-truth CSV stems exactly
- Entity field keys identical across all documents

---

## Known Limitations

### 1. Sequential Processing

Documents are processed one at a time. For large corpora (100+ docs), this is
slow. Future work: parallel processing with `multiprocessing` or `asyncio`.

### 2. No Incremental Updates

Re-running the pipeline reprocesses all documents, even if outputs already exist.
Future work: check timestamps and skip unchanged files.

### 3. Memory Usage

Large multi-page documents (50+ pages) can consume significant RAM during OCR.
Workaround: process individually with `--doc` flag.

### 4. Error Recovery

If a stage fails, the pipeline stops for that document. No automatic retry or
fallback strategies. Future work: configurable retry logic.

### 5. Language Detection

Language is inferred from filename (`_EN_` or `_FR_`). Documents without this
convention default to English. Future work: automatic language detection from
OCR text.

---

## Future Enhancements

### Short-term (Milestone 2)

- **Parallel processing** — process multiple documents concurrently
- **Incremental updates** — skip unchanged files
- **Progress bars** — visual feedback for long runs
- **Configurable thresholds** — OCR confidence, extraction confidence

### Long-term (Milestone 3+)

- **ML-based extraction** — replace regex with trained models
- **Active learning** — flag low-confidence extractions for human review
- **Web UI** — upload documents and view results in browser
- **API server** — REST API for pipeline execution

---

## Troubleshooting

### Pipeline hangs during OCR

**Cause:** PaddleOCR downloading models on first run.  
**Solution:** Wait for download to complete (~500 MB). Subsequent runs will be fast.

### "Tesseract not found" error

**Cause:** Tesseract not installed or not in PATH.  
**Solution:**
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
- macOS: `brew install tesseract`
- Linux: `sudo apt install tesseract-ocr`

Verify: `tesseract --version`

### Low extraction accuracy

**Cause:** OCR text is garbled or document is blank template.  
**Solution:**
1. Check OCR text in `outputs/ocr/<doc>.txt`
2. If garbled, try reprocessing with `--no-paddle` (or vice versa)
3. If blank template, extraction will correctly return empty fields

### Out of memory

**Cause:** Large document or insufficient RAM.  
**Solution:**
1. Process individually: `python src/run.py --doc <name>`
2. Close other applications to free RAM
3. Use `--no-paddle` to reduce memory usage

---

## Summary

Task 9 delivers a **production-ready pipeline** that:
- ✅ Chains all three stages (preprocessing → OCR → extraction)
- ✅ Handles errors gracefully with detailed reporting
- ✅ Processes all 20 ground-truth documents in ~2.5 minutes
- ✅ Generates structured outputs for Task 10 evaluation
- ✅ Provides flexible CLI for batch and single-document runs
- ✅ Includes comprehensive test suite

The pipeline is the **foundation** for Milestone 1 evaluation and the
**starting point** for Milestone 2 ML-based improvements.
