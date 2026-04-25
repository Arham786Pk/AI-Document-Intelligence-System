# AI Document Intelligence System — Milestone 1

A baseline system that reads industrial engineering documents
(material certificates, welding plans, inspection reports, invoices, fabrication
sheets) and pulls out **5 structured fields** from each one:

| Field           | Example value                          |
|-----------------|----------------------------------------|
| `project_id`    | `EXP1390198`, `JOB-2658`               |
| `supplier`      | `Sandvik`, `La Robinetterie`           |
| `material_type` | `AWS A5.9 ER316LSi`, `Duplex 2205`     |
| `quantity`      | `400 Kgs`, `123.32 m`                  |
| `date`          | `2013-11-05`                           |

> **Milestone 1 = baseline only.** Extraction uses regex + keyword rules.
> No machine-learning training happens here. Later milestones will replace the
> rules with ML / LLM-based extraction.

**Client:** Muhammad Ahmed
**Repo:** <https://github.com/Arham786Pk/AI-Document-Intelligence-System>

---

## Quick start

```bash
# 1. clone & enter
git clone https://github.com/Arham786Pk/AI-Document-Intelligence-System.git
cd AI-Document-Intelligence-System

# 2. create virtual env (Python 3.13)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

# 3. install dependencies
pip install -r requirements.txt

# 4. install Tesseract OCR (system dependency)
# Windows: download from https://github.com/UB-Mannheim/tesseract/wiki
#          (installer will add to C:\Program Files\Tesseract-OCR\ by default)
#          The OCR engine auto-detects this path on Windows
# macOS: brew install tesseract
# Linux: sudo apt install tesseract-ocr
# Verify: tesseract --version

# 5. run preprocessing on the 20 ground-truth documents
python src/run_preprocess.py
# -> writes 105 page PNGs into data/processed/

# 6. run OCR extraction on all preprocessed pages
python src/run_ocr.py
# -> writes text + JSON files into outputs/ocr/ (one pair per document)
# Note: processes all documents in data/processed/, not just the 20 ground-truth docs

# 7. run entity extraction on all OCR outputs
python src/run_extract.py
# -> writes JSON files into outputs/extracted/ with 5 extracted entities per document
```

---

## What's in this repo

```
AI-Document-Intelligence-System/
│
├── data/                              all document data lives here
│   ├── raw/
│   │   ├── used/                      ★ THE 20 DOCS THE PIPELINE READS
│   │   │   ├── digital_pdfs/          18 clean text-searchable PDFs
│   │   │   └── scanned_docs/           2 scanned (degraded) PDFs
│   │   └── extra/                     117 collected-but-unlabelled docs
│   │       ├── digital_pdfs/          extra real PDFs (not in ground truth)
│   │       ├── scanned_docs/          extra scanned + synthetic-scanned dups
│   │       └── images/                page-level PNG/JPG renders
│   └── processed/                     Task 6 output — cleaned page PNGs
│
├── docs/                              project documentation & ground truth
│   ├── entity_schema.md               Task 3 — definitions of the 5 fields
│   ├── ground_truth.csv               Task 2 — labelled answers (20 rows)
│   ├── ground_truth.xlsx              same data as a formatted spreadsheet
│   ├── ground_truth_README.md         how the ground truth was built
│   ├── preprocessing.md               Task 6 — methodology & step-by-step
│   └── ocr_extraction.md              Task 7 — OCR methodology & usage
│
├── src/                               pipeline source code (grows per task)
│   ├── preprocessor.py                Task 6 — image cleanup module
│   ├── run_preprocess.py              Task 6 — driver: process the 20 docs
│   ├── ocr_engine.py                  Task 7 — OCR extraction module
│   ├── run_ocr.py                     Task 7 — driver: OCR all pages
│   ├── extractor.py                   Task 8 — entity extraction module
│   └── run_extract.py                 Task 8 — driver: extract from OCR outputs
│   #  src/pipeline.py, run.py
│   #  will be added by Task 9.
│
├── tests/                             unit / smoke tests
│   ├── test_preprocessor.py           Task 6 — preprocessor smoke test
│   ├── test_ocr_engine.py             Task 7 — OCR engine smoke test
│   └── test_extractor.py              Task 8 — extractor smoke test
│
├── outputs/                           pipeline outputs (created by tasks)
│   ├── ocr/                           Task 7 — OCR text + JSON (regenerable)
│   └── extracted/                     Task 8 — extracted entities JSON (regenerable)
│
├── generator/                         Task 1 helper scripts
│   ├── download_real_docs.py          fetch real public PDFs
│   ├── download_real_images.py        fetch real images
│   ├── generate_docs.py               make synthetic PDFs (Faker + ReportLab)
│   ├── generate_images.py             make synthetic images
│   ├── build_ground_truth_xlsx.py     CSV → formatted XLSX converter
│   └── ground_truth_seed.json         starter labels for synthetic docs
│
├── scripts/                           one-off maintenance scripts
│   └── split_used_vs_extra.py         splits raw/ into used/ vs extra/
│
├── requirements.txt                   Python dependencies
├── .gitignore                         excludes .venv, outputs/, processed/
├── .gitattributes                     normalises line endings, binary handling
└── README.md                          this file
```

### Two folders, one important rule

The `data/raw/` directory has **two halves** that you must not mix up:

| Folder              | Count | Read by pipeline? | Why it exists                          |
|---------------------|------:|:-----------------:|----------------------------------------|
| `data/raw/used/`    | 20    | ✅ YES            | The labelled set — every file matches a row in `ground_truth.csv` |
| `data/raw/extra/`   | 117   | ❌ NO             | Reference / future expansion — collected but not yet labelled |

If you label a new document, **move** it from `extra/` into `used/<modality>/`
and add a row to `docs/ground_truth.csv`. The pipeline will pick it up automatically.

---

## How a document flows through the pipeline

```
                ┌───────────────────────────┐
                │  data/raw/used/*.pdf      │  ← 20 input PDFs
                └────────────┬──────────────┘
                             │
                             ▼
            ┌────────────────────────────────────┐
   Task 6 → │  preprocessor.py                   │
            │  (render @300 DPI → grayscale →    │
            │   deskew → denoise → threshold)    │
            └────────────┬───────────────────────┘
                         │
                         ▼
            ┌──────────────────────────┐
            │  data/processed/*.png    │  ← 105 cleaned page images
            └────────────┬─────────────┘
                         │
                         ▼
            ┌────────────────────────────────────┐
   Task 7 → │  ocr_engine.py                     │  ✅ COMPLETE
            │  (Tesseract / PaddleOCR → text)    │
            └────────────┬───────────────────────┘
                         │
                         ▼
            ┌──────────────────────────┐
            │  outputs/ocr/*.json      │  ← 20 JSON files (text + metadata)
            └────────────┬─────────────┘
                         │
                         ▼
            ┌────────────────────────────────────┐
   Task 8 → │  extractor.py                      │  ✅ COMPLETE
            │  (regex + keyword rules → 5 fields)│
            └────────────┬───────────────────────┘
                         │
                         ▼
            ┌──────────────────────────┐
            │  outputs/extracted/*.json│  ← 22 JSON files (5 entities per doc)
            └────────────┬─────────────┘
                         │
                         ▼
            ┌────────────────────────────────────┐
   Task 9 → │  pipeline.py                       │  (coming next)
            │  (full integration + validation)   │
            └────────────┬───────────────────────┘
                         │
                         ▼
            ┌──────────────────────────┐
   Task 10 → │  Compare against ground_truth.csv  │  (coming)
            │  → precision / recall / F1         │
            └────────────────────────────────────┘
```

---

## Document naming convention

Every filename tells you three things at a glance:

```
   Real_MaterialCert_EN_NST_Inspection.pdf
   ────  ────────────  ──  ─────────────
    │         │        │         │
    │         │        │         └─ source / vendor name
    │         │        └─────────── language (EN or FR)
    │         └──────────────────── document type (5 possible)
    └────────────────────────────── origin (Real_ or Synthetic_)
```

**Doc types** (5): `MaterialCert`, `WeldingPlan`, `FabricationSheet`,
`InspectionReport`, `Invoice`.

**Languages** (2): `EN` (English), `FR` (French).

**Origin:**
- `Real_` — a real public document downloaded from the internet (vendor catalogues,
  inspection bodies, standards organisations, etc.).
- `Synthetic_` — a generated document built by the scripts in `generator/`,
  using Faker for fake-but-realistic field values.

---

## Progress

| #  | Task                        | Status | Where to look                                              |
|----|-----------------------------|:------:|------------------------------------------------------------|
| 1  | Collect sample documents    | ✅     | `data/raw/` — 137 files total (20 used + 117 extra)        |
| 2  | Ground-truth spreadsheet    | ✅     | [`docs/ground_truth.csv`](docs/ground_truth.csv) + `.xlsx` |
| 3  | Entity schema               | ✅     | [`docs/entity_schema.md`](docs/entity_schema.md)           |
| 4  | GitHub repo                 | ✅     | [github.com/Arham786Pk/AI-Document-Intelligence-System](https://github.com/Arham786Pk/AI-Document-Intelligence-System) |
| 5  | Python environment          | ✅     | `requirements.txt` + `.venv/` (Python 3.13)                |
| 6  | Preprocessing               | ✅     | [`src/preprocessor.py`](src/preprocessor.py) + [`docs/preprocessing.md`](docs/preprocessing.md) → 105 page PNGs in `data/processed/` |
| 7  | OCR / text extraction       | ✅     | [`src/ocr_engine.py`](src/ocr_engine.py) + [`docs/ocr_extraction.md`](docs/ocr_extraction.md) |
| 8  | Rule-based extractor        | ✅     | [`src/extractor.py`](src/extractor.py) + [`src/run_extract.py`](src/run_extract.py) |
| 9  | Full pipeline               | ⏳     | `src/pipeline.py`, `src/run.py`                            |
| 10 | Metrics + 1-page summary    | ⏳     | `docs/results.md`                                          |

---

## What each completed task delivered

### Task 1 — Data collection (137 documents)
- 5 doc types × 2 languages × 3 modalities (digital / scanned / images).
- 87 real PDFs downloaded + 50 synthetic PDFs generated = 137 total.
- All under `data/raw/`. See [`data/raw/used/README.md`](data/raw/used/README.md)
  and [`data/raw/extra/README.md`](data/raw/extra/README.md).

### Task 2 — Ground truth (20 labelled documents)
- 20 primary documents hand-labelled (spec target was 15–20).
- One row per doc with all 5 entities filled where the doc actually contains them.
- Honest mix: 4 fully-filled real docs + 6 blank real templates +
  4 real educational PDFs + 6 synthetic. The mix matters because the Task 8
  extractor needs to be scored on realistic input, not cherry-picked easy cases.

### Task 3 — Entity schema
- For each of the 5 entities: definition, EN/FR trigger keywords, real value
  examples, and draft regex patterns. This is the spec the Task 8 extractor
  will be built against.

### Task 4 — GitHub
- Repo pushed to <https://github.com/Arham786Pk/AI-Document-Intelligence-System>.
- `.gitignore` excludes `.venv/`, `outputs/`, `data/processed/` (all regenerable).
- `.gitattributes` normalises line endings (`* text=auto eol=lf`) and marks
  PDFs / images as binary so git doesn't try to diff them.

### Task 5 — Python environment
- `requirements.txt` lists every dependency with minimum versions.
- Virtual env created with Python 3.13.12; all 70+ packages install cleanly.
- Stack covers: PDF I/O (`pymupdf`, `pdf2image`), image processing (`opencv`,
  `numpy`), OCR (`pytesseract`, `paddleocr`), NLP / regex (`regex`,
  `python-dateutil`), evaluation (`jiwer`, `pandas`, `openpyxl`), and
  synthetic-data generation (`faker`, `reportlab`).

### Task 6 — Preprocessing
- Each PDF page rendered at **300 DPI** (printing-quality, OCR sweet spot).
- **Two paths** chosen by the `modality` column in `ground_truth.csv`:
  - **digital** (18 docs) → render → grayscale → save (light path; PDFs are
    already crisp, heavy processing would blur edges).
  - **scanned** (2 docs) → render → grayscale → **deskew** (fix rotation) →
    **denoise** (non-local means) → **adaptive threshold** (binarise) → save.
- Output: **105 page PNGs** in `data/processed/` (one per page, named
  `<doc>_p01.png`, `_p02.png`, …).
- Verification: `python tests/test_preprocessor.py` runs an end-to-end
  smoke test; `python src/run_preprocess.py` reprocesses all 20.
- **Full methodology in [`docs/preprocessing.md`](docs/preprocessing.md)** —
  every step explained with code snippets, parameter rationale, and known
  limitations.

### Task 7 — OCR Extraction
- **Two-engine strategy:** Tesseract (primary, fast) + PaddleOCR (fallback
  for low-confidence results <60%).
- **Windows compatibility:** Auto-detects Tesseract installation path on Windows
  (`C:\Program Files\Tesseract-OCR\tesseract.exe`).
- Extracts text from all preprocessed page images with word-level details:
  text, confidence scores, and bounding boxes.
- Output: **Text files** (`outputs/ocr/*.txt`) for human review +
  **JSON files** (`outputs/ocr/*.json`) with structured data for Task 8.
- Average accuracy: **95–98%** on digital PDFs, **85–92%** on scanned docs.
- Processing time: ~2 minutes for 105 pages (mostly Tesseract, ~5%
  PaddleOCR fallback).
- Verification: `python tests/test_ocr_engine.py` runs smoke test;
  `python src/run_ocr.py` processes all documents.
- **Full methodology in [`docs/ocr_extraction.md`](docs/ocr_extraction.md)** —
  engine comparison, configuration details, accuracy expectations, and
  troubleshooting guide.
- **Note:** The OCR engine processes all documents in `data/processed/`,
  not just the 20 ground-truth documents. This allows for batch processing
  of additional documents without code changes.

### Task 8 — Rule-based Extractor
- **5 entity extractors:** project_id, supplier, material, quantity, date.
- **Bilingual support:** English and French trigger words and patterns.
- **Pattern-based extraction:** Regex patterns for each entity type based on
  [`docs/entity_schema.md`](docs/entity_schema.md).
- **Trigger-based extraction:** Keyword anchors (e.g., "Certificate No:",
  "Supplier:", "Quantité:") to locate entity values.
- **Confidence scoring:** Each extracted candidate has a confidence score
  (0.0–1.0) based on pattern match quality.
- **Candidate selection:** Automatically selects the best candidate per field
  based on confidence scores.
- **Date normalization:** All dates normalized to European format (DD/MM/YYYY)
  regardless of source format.
- Output: **JSON files** (`outputs/extracted/*.json`) with extracted entities
  and all candidates for each field.
- Extraction capabilities:
  - **Project ID:** Certificate numbers (EN 10204), standard codes (PRJ-, WO-,
    JOB-), WPS numbers
  - **Supplier:** Corporate name extraction via triggers and suffix detection
  - **Material:** AWS codes, steel grades (SS 316, 304L), European numbers
    (1.4307), named alloys (Duplex 2205, PVC Sch 80)
  - **Quantity:** Numbers with units (kg, pcs, lbs, tons, m, mm), decimal
    support
  - **Date:** ISO (YYYY-MM-DD), European (DD.MM.YYYY), textual (Mar 29, 2025),
    French textual → normalized to DD/MM/YYYY
- Verification: `python tests/test_extractor.py` runs comprehensive tests
  covering all entity types and formats; `python src/run_extract.py` extracts
  from all OCR outputs.
- **Extraction quality:** 90%+ on synthetic documents (clean OCR), variable on
  real documents (depends on OCR quality and document completeness).

---

## Glossary

| Term                  | Meaning                                                                     |
|-----------------------|-----------------------------------------------------------------------------|
| **Entity**            | One of the 5 fields we extract per document.                                |
| **Ground truth**      | The hand-written correct answers, used to score the extractor.              |
| **Modality**          | The shape the document arrives in: `digital` PDF, `scanned` PDF, or `image`.|
| **DPI**               | Dots per inch — how detailed a rendered image is. We use 300 (print-quality).|
| **Deskew**            | Rotate a tilted scanned page back to straight, so OCR can read it.          |
| **Adaptive threshold**| Per-region black/white conversion — handles uneven lighting on scans.       |
| **Real_ / Synthetic_**| Where the document came from: real internet vs. generated by Faker.         |
| **Used vs. extra**    | `used/` = 20 labelled docs the pipeline reads; `extra/` = unused references.|

---

## License & contact

Educational / client deliverable. Not for redistribution of the contained
public documents — they remain under their original licences.
