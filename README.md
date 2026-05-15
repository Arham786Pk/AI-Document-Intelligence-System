# AI French Invoice Extraction

Rule-based pipeline that takes a **French invoice PDF or photo**, runs French OCR,
extracts **11 entity fields** with full synonym tolerance, detects payment
status, and writes one structured JSON per invoice.

> Repository: <https://github.com/Arham786Pk/AI-Document-Intelligence-System>
> Client: Muhammad Ahmed · Milestone 1 of 4 complete · Milestone 2 in progress · 11 entities (M1) → 12 (M2 will add `consumer_name`)

---

## Quick Start — Run the Pipeline

```bash
# Step 1: Install dependencies
pip install -r requirements.txt
# Also install Tesseract + French pack — see docs/TESSERACT_INSTALLATION.md

# Step 2: Run from phone photo images
python -m src.pipeline --from raw --input data/Images --output outputs

# Step 3: Run from scanned PDFs
python -m src.pipeline --from raw --input data/Scanned_PDF --output outputs

# Step 4: Run from already-preprocessed images (skip preprocessing)
python -m src.pipeline --from processed --input data/processed --output outputs

# Step 5: Run entity extraction only (if OCR already done)
python -m src.pipeline --from ocr --input outputs/ocr_results --output outputs

# Step 6: Calculate metrics against ground truth
python -m src.metrics --extracted outputs/extracted --ground-truth docs/ground_truth.csv --output outputs
```

**Note on dataset (updated for Milestone 2 Task 02 — 2026-05-15):**

- `data/Images/` — 16 phone photos (M1 dataset)
- `data/Scanned_PDF/` — 5 M1 scanned PDFs + `sourced_internet/` subfolder with 36 additional French invoice PDFs collected from public sources for M2 AI training
- **Total dataset: 57 documents** (meets M2 Task 02 target of ≥50)
- See [`data/Scanned_PDF/sourced_internet/MANIFEST.md`](data/Scanned_PDF/sourced_internet/MANIFEST.md) for per-file source attribution and content classification (real invoices, Factur-X references, templates, "comprendre votre facture" educational PDFs)


---

## Scope (updated 2026-05-08)

The project scope has been rewritten. Previous multi-document-type scaffolding
(fabrication sheets, welding plans, material certs, inspection reports, English
invoices) was removed. The system now works **only on French invoices** and
the entity count moved from 10 → **11** with the addition of `solde_du`.

| Old scope (removed) | New scope (active) |
|---------------------|--------------------|
| 5 document types | French invoices only |
| 10 entities | 11 entities (added `solde_du`) |
| English + French + synthetic | French only — 19 unique invoices (16 photos + 5 scanned PDFs) |

The full task brief is `Milestone1_Simple_Final.docx` (kept locally — not committed).

---

## The 11 entities

| # | Field | Label / synonyms (short) |
|---|-------|--------------------------|
| 1 | `supplier_name` | Header / `Fournisseur` / `Société` / `Entreprise` |
| 2 | `invoice_number` | `Facture N°` / `Numéro de facture` / `Réf. Facture` |
| 3 | `invoice_date` | `Date` / `Date facture` / `Émise le` |
| 4 | `siret` | `SIRET` (14 digits) |
| 5 | `echeance` | `Échéance` / `Date limite de paiement` / `À régler avant` |
| 6 | `invoice_content` | `Désignation` / `Description` / `Prestations` (line items) |
| 7 | `tva_percentage` | Any rate — `0 %`, `5,5 %`, `10 %`, `20 %`, etc. |
| 8 | `tva_amount` | `Montant TVA` / `Total TVA` |
| 9 | `total_amount` | `Total TTC` / `Net à payer` / `Montant total` |
| 10 | `payment_status` | `PAID` / `UNPAID` / `UNKNOWN` (4-signal detector) |
| 11 | `solde_du` | `Solde dû` / `Reste à payer` / `Balance due` / `Montant restant` |

Full synonym matrix and OCR-tolerance rules: [`docs/entity_schema.md`](docs/entity_schema.md).

---

## Repository layout

```
.
├── .claude/
│   └── settings.local.json         IDE settings
├── .venv/                          ← Python virtual environment
├── data/
│   ├── Images/                     ← 16 phone-photo JPGs (IMG-20260507-WA0143…WA0158)
│   ├── Scanned_PDF/                ← 5 scanned PDFs (Invoice_FR_016…FR_020)
│   ├── processed/                  ← Cleaned 300-DPI page PNGs (organized by invoice)
│   │   ├── IMG-20260507-WA0143/
│   │   │   └── page_01.png
│   │   ├── IMG-20260507-WA0144/
│   │   │   └── page_01.png
│   │   ├── ... (25 invoice subdirectories total)
│   │   └── preprocessing_manifest.json
│   └── MANIFEST.md                 ← Inventory of all source files
├── docs/
│   ├── entity_schema.md            ← Contract for extractor + 11 entity definitions
│   ├── ground_truth.csv            ← Labelled answer key, 19 × 11 fields
│   ├── ground_truth.xlsx           ← Formatted Excel for the client
│   ├── ground_truth_README.md      ← Labelling rules
│   ├── preprocessing.md            ← Task 6 module spec
│   ├── ocr_engine.md               ← Task 7 module spec
│   └── TESSERACT_INSTALLATION.md   ← Tesseract setup guide
├── outputs/
│   ├── ocr_results/                ← OCR JSON files + manifest (Task 7 output)
│   │   ├── IMG-20260507-WA0143.json
│   │   ├── IMG-20260507-WA0144.json
│   │   ├── ... (25 OCR JSON files)
│   │   └── ocr_manifest.json
│   ├── extracted/                  ← Entity extraction JSONs (Task 8 output)
│   │   ├── IMG-20260507-WA0143.json
│   │   ├── IMG-20260507-WA0144.json
│   │   └── ... (25 extracted entity JSON files)
│   ├── pipeline_report.json        ← Pipeline execution statistics (Task 9 output)
│   ├── metrics_report.json         ← Complete metrics data (Task 10 output)
│   ├── metrics_summary.txt         ← Human-readable metrics report (Task 10 output)
│   └── detailed_comparison.csv     ← Per-field comparison details (Task 10 output)
├── scripts/
│   ├── build_ground_truth.py       ← Regenerates CSV + XLSX from labelled rows
│   └── demo_ocr.py                 ← Task 7 demo / smoke check
├── src/
│   ├── __init__.py
│   ├── preprocessor.py             ← Task 6 — render/deskew/denoise/binarise
│   ├── ocr_engine.py               ← Task 7 — Tesseract + PaddleOCR fallback
│   ├── extractor.py                ← Task 8 — rule-based entity extraction
│   ├── pipeline.py                 ← Task 9 — full pipeline orchestration
│   ├── run.py                      ← Task 9 — convenient entry point
│   └── metrics.py                  ← Task 10 — metrics calculation and reporting
├── tests/
│   ├── test_preprocessor.py        ← Task 6 smoke tests
│   ├── test_ocr_engine.py          ← Task 7 smoke tests
│   ├── test_extractor.py           ← Task 8 smoke tests
│   ├── test_pipeline.py            ← Task 9 smoke tests
│   └── test_metrics.py             ← Task 10 smoke tests
├── .gitattributes
├── .gitignore
├── requirements.txt                ← Python dependencies
├── TASK_7_SUMMARY.md               ← Task 7 completion summary
└── README.md
```

The full dataset (16 photos + 5 scanned PDFs) and all pipeline outputs are
committed to the repository for full reproducibility.

---

## Task progress

| Task | Description | Status |
|------|-------------|--------|
| 01 | Collect 15–20 French invoices (`data/Images/` + `data/Scanned_PDF/`) | ✅ Done — 19 unique invoices (5 PDFs + 16 photos collapsed to 14 unique) |
| 02 | Ground-truth spreadsheet with 11 fields | ✅ Done — `docs/ground_truth.csv` + `.xlsx` |
| 03 | Entity schema with full French synonyms | ✅ Done — `docs/entity_schema.md` |
| 04 | GitHub repository setup | ✅ Done — repo refactored to French-invoice-only |
| 05 | Python environment with French OCR | ✅ Done — `requirements.txt` + setup notes below |
| 06 | Preprocessing module (`src/preprocessor.py`) | ✅ Done — see [`docs/preprocessing.md`](docs/preprocessing.md) |
| 07 | OCR text extraction in French (`src/ocr_engine.py`) | ✅ Done — see [`docs/ocr_engine.md`](docs/ocr_engine.md) |
| 08 | Rule-based extractor for 11 fields (`src/extractor.py`) | ✅ Done — extracts all 11 entity fields with accent tolerance |
| 09 | Full pipeline (`src/pipeline.py`, `src/run.py`) | ✅ Done — orchestrates preprocessing, OCR, and extraction |
| 10 | Metrics + summary report (`src/metrics.py`) | ✅ Done — compares extracted vs ground truth, generates accuracy reports |

---

## Task 5 — Environment setup

### 1. Python deps

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### 2. Tesseract + French language pack

The system **requires** Tesseract OCR with the `fra` language pack — without it,
accented characters come back as `?` or wrong glyphs and every entity except
SIRET silently fails.

**Windows**

1. Install Tesseract from <https://github.com/UB-Mannheim/tesseract/wiki>.
2. During the installer, tick **Additional language data → French (fra)**.
3. Confirm `tesseract --version` works in a fresh shell.
4. Confirm the language pack is installed:

   ```bash
   tesseract --list-langs
   ```

   `fra` must appear in the output. If it does not, download
   [`fra.traineddata`](https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata)
   into `C:\Program Files\Tesseract-OCR\tessdata\`.

**macOS**

```bash
brew install tesseract tesseract-lang
```

**Linux (Debian/Ubuntu)**

```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-fra
```

### 3. Smoke test

```bash
python -c "import pytesseract; from PIL import Image; \
  print(pytesseract.image_to_string(Image.open('data/Images/IMG-20260507-WA0148.jpg'), lang='fra')[:300])"
```

The output must contain accented words like `Échéance`, `règlement`,
`numériques`. If accents are wrong/missing, the `fra` pack is not installed
correctly — re-do step 2.

### 4. Optional: PaddleOCR fallback

PaddleOCR is the fallback for low-confidence Tesseract pages (Task 7). The
French model downloads on first use:

```bash
python -c "from paddleocr import PaddleOCR; PaddleOCR(lang='fr', use_angle_cls=True)"
```

---

## Task 7 — OCR Engine Features

The OCR engine (`src/ocr_engine.py`) extracts text from preprocessed French invoice images with the following features:

### Core Capabilities

- **Tesseract OCR** with French language pack (`fra`) as primary engine
- **PaddleOCR fallback** for low-confidence pages (< 60% confidence)
- **Multi-page support** with page break markers for proper text concatenation
- **Confidence scoring** at both page and invoice level
- **Smart file handling** — automatically skips already processed files (compares modification times)
- **Batch processing** with summary manifest generation

### Output Structure

Each invoice produces a JSON file with:
- Full extracted text
- Per-page confidence scores
- Character and word counts
- Engine used (Tesseract or PaddleOCR)
- Quality indicators

### Performance

Successfully processed **25 French invoices (31 pages)** with:
- Mean confidence: **82.5%**
- Total characters: **36,376**
- Total words: **5,935**
- Zero errors

### Incremental Processing

The OCR engine is optimized for repeated runs:
- **First run:** Processes all invoices
- **Subsequent runs:** Only processes new or modified files
- **Modification detection:** Compares PNG file timestamps with JSON output timestamps

Example:
```bash
# First run: processes 25 invoices (~30 seconds)
python -m src.ocr_engine --input data/processed --output outputs/ocr_results

# Second run: skips all 25 (already up-to-date, ~2 seconds)
python -m src.ocr_engine --input data/processed --output outputs/ocr_results

# After modifying one file: processes 1, skips 24
python -m src.ocr_engine --input data/processed --output outputs/ocr_results
```

For detailed documentation, see [`docs/ocr_engine.md`](docs/ocr_engine.md).

---

## Quick rebuild commands

```bash
# Regenerate ground truth files
python scripts/build_ground_truth.py

# Task 6 — preprocess every invoice into 300 DPI binarised PNGs
python -m src.preprocessor --input data/Images --output data/processed
python -m src.preprocessor --input data/Scanned_PDF --output data/processed

# Task 6 — smoke tests
python -m pytest tests/test_preprocessor.py -v

# Task 7 — OCR all preprocessed invoices (automatically skips already processed files)
python -m src.ocr_engine --input data/processed --output outputs/ocr_results

# Task 7 — OCR single invoice
python -m src.ocr_engine --single data/processed/Invoice_FR_016 --output outputs/ocr_results

# Task 7 — demo script (verify Tesseract + French language pack)
python scripts/demo_ocr.py

# Task 7 — smoke tests
python -m pytest tests/test_ocr_engine.py -v

# Task 8 — extract entities from all OCR results
python -m src.extractor --input outputs/ocr_results --output outputs/extracted

# Task 8 — smoke tests
python -m pytest tests/test_extractor.py -v

# Task 9 — run full pipeline from preprocessed images (most common)
python -m src.pipeline --input data/processed --output outputs --from processed

# Task 9 — run full pipeline from raw invoices
python -m src.pipeline --input data/raw/french_invoices --output outputs --from raw

# Task 9 — run extraction only (from OCR results)
python -m src.pipeline --input outputs/ocr_results --output outputs --from ocr

# Task 9 — using run.py convenience script
python src/run.py --input data/processed --output outputs

# Task 9 — smoke tests
python -m pytest tests/test_pipeline.py -v

# Task 10 — calculate metrics and generate reports
python -m src.metrics --extracted outputs/extracted --ground-truth docs/ground_truth.csv --output outputs

# Task 10 — smoke tests
python -m pytest tests/test_metrics.py -v

# Run all tests
python -m pytest tests/ -v
```

**Note:** Task 7 OCR engine intelligently skips files that are already processed. It only re-processes invoices when source PNG files are newer than the output JSON files.

---

## Milestone 1 Results

### Overall Performance

**Pipeline Execution:**
- Total invoices processed: 25
- Processing time: 0.71 seconds
- Success rate: 100%
- Mean OCR confidence: 82.5%

**Extraction Accuracy (Task 10 Metrics):**
- Overall accuracy: **39.11%** (70 of 179 fields matched)
- Invoices compared: 19
- Best performing invoice: 80% accuracy
- Perfect matches: 0

### Field-Level Accuracy

| Field | Accuracy | Precision | Recall | F1 Score |
|-------|----------|-----------|--------|----------|
| solde_du | 100.00% | 100.00% | 100.00% | 100.00% |
| echeance | 64.29% | 100.00% | 64.29% | 78.26% |
| payment_status | 57.89% | 57.89% | 100.00% | 73.33% |
| tva_percentage | 47.37% | 90.00% | 50.00% | 64.29% |
| total_amount | 47.37% | 90.00% | 50.00% | 64.29% |
| invoice_content | 42.11% | 72.73% | 50.00% | 59.26% |
| invoice_date | 38.89% | 41.18% | 87.50% | 56.00% |
| tva_amount | 36.84% | 77.78% | 41.18% | 53.85% |
| siret | 28.57% | 57.14% | 36.36% | 44.44% |
| supplier_name | 26.32% | 26.32% | 100.00% | 41.67% |
| invoice_number | 0.00% | 0.00% | 0.00% | 0.00% |

### Key Findings

**Strengths:**
- `solde_du`: Perfect extraction (100%)
- `echeance`: Strong performance (64%)
- `payment_status`: Good detection (58%)
- Money fields (`tva_percentage`, `total_amount`): Moderate accuracy (47%)

**Areas for Improvement:**
- `invoice_number`: Failed to extract (0%) — needs better pattern matching
- `supplier_name`: Low accuracy (26%) — often picks wrong line from header
- `siret`: Low accuracy (29%) — missing from many invoices or not detected
- `invoice_content`: Moderate (42%) — line item parsing needs refinement

**Root Causes:**
1. **OCR quality**: Phone photos have lower quality than scanned PDFs
2. **Layout variation**: Different invoice templates require more robust patterns
3. **Pattern specificity**: Some regex patterns are too strict or too loose
4. **Header parsing**: Supplier name extraction needs better heuristics

### Recommendations for Milestone 2

1. **Improve invoice_number extraction**: Add more pattern variations
2. **Enhance supplier_name detection**: Use better header parsing logic
3. **SIRET detection**: Add fallback patterns for different layouts
4. **Line item parsing**: Implement table structure detection
5. **Consider ML approach**: Rule-based extraction has reached its limits

---

## Project Status

✅ **Milestone 1 Complete** — All 10 tasks finished

**Deliverables:**
- ✅ 19 French invoices collected and preprocessed
- ✅ Ground truth spreadsheet with 11 entity fields
- ✅ Complete entity schema with French synonyms
- ✅ Preprocessing module with image enhancement
- ✅ OCR engine with French language support
- ✅ Rule-based entity extractor for 11 fields
- ✅ Full pipeline orchestration
- ✅ Comprehensive metrics and evaluation reports
- ✅ Test suite with 58 passing tests

**Next Steps:**
- Milestone 2: Machine learning-based extraction
- Milestone 3: Multi-document type support
- Milestone 4: Production deployment

---
