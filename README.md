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

# 4. run preprocessing on the 20 ground-truth documents
python src/run_preprocess.py
# -> writes 105 page PNGs into data/processed/
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
│   └── preprocessing.md               Task 6 — methodology & step-by-step
│
├── src/                               pipeline source code (grows per task)
│   ├── preprocessor.py                Task 6 — image cleanup module
│   └── run_preprocess.py              Task 6 — driver: process the 20 docs
│   #  src/ocr_engine.py, extractor.py, pipeline.py, run.py
│   #  will be added by Tasks 7–9.
│
├── tests/                             unit / smoke tests
│   └── test_preprocessor.py           Task 6 — preprocessor smoke test
│
├── outputs/                           Task 9 output (created later — empty for now)
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
   Task 7 → │  ocr_engine.py                     │  (coming next)
            │  (Tesseract / PaddleOCR → text)    │
            └────────────┬───────────────────────┘
                         │
                         ▼
            ┌────────────────────────────────────┐
   Task 8 → │  extractor.py                      │  (coming)
            │  (regex + keyword rules → 5 fields)│
            └────────────┬───────────────────────┘
                         │
                         ▼
            ┌──────────────────────────┐
   Task 9 → │  outputs/*.json          │  (coming)
            └────────────┬─────────────┘
                         │
                         ▼
            ┌────────────────────────────────────┐
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
| 7  | OCR / text extraction       | ⏳     | `src/ocr_engine.py` (next)                                 |
| 8  | Rule-based extractor        | ⏳     | `src/extractor.py`                                         |
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
