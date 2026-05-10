# AI French Invoice Extraction

Rule-based pipeline that takes a **French invoice PDF or photo**, runs French OCR,
extracts **11 entity fields** with full synonym tolerance, detects payment
status, and writes one structured JSON per invoice.

> Repository: <https://github.com/Arham786Pk/AI-Document-Intelligence-System>
> Client: Muhammad Ahmed · Milestone 1 of 4 · 11 entities · No model training in this milestone

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
│   └── settings.local.json         ← Kiro IDE settings
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
│   └── pipeline_report.json        ← Pipeline execution statistics (Task 9 output)
├── scripts/
│   ├── build_ground_truth.py       ← Regenerates CSV + XLSX from labelled rows
│   └── demo_ocr.py                 ← Task 7 demo / smoke check
├── src/
│   ├── __init__.py
│   ├── preprocessor.py             ← Task 6 — render/deskew/denoise/binarise
│   ├── ocr_engine.py               ← Task 7 — Tesseract + PaddleOCR fallback
│   ├── extractor.py                ← Task 8 — rule-based entity extraction
│   ├── pipeline.py                 ← Task 9 — full pipeline orchestration
│   └── run.py                      ← Task 9 — convenient entry point
├── tests/
│   ├── test_preprocessor.py        ← Task 6 smoke tests
│   ├── test_ocr_engine.py          ← Task 7 smoke tests
│   ├── test_extractor.py           ← Task 8 smoke tests
│   └── test_pipeline.py            ← Task 9 smoke tests
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
| 10 | Metrics + summary report | ⬜ Pending |

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
```

**Note:** Task 7 OCR engine intelligently skips files that are already processed. It only re-processes invoices when source PNG files are newer than the output JSON files.

Task 10 commands will be added as that module lands.
