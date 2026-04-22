# Industrial Document Intelligence — Milestone 1

Foundation & baseline system for the **AI Document Intelligence Project**
(Client: Muhammad Ahmed).

Milestone 1 takes raw industrial documents and extracts 5 structured entities
per document (Project ID, Supplier, Material Type, Quantity, Date) using a
rule-based baseline. No ML training happens in this milestone.

## Repository layout

```
MileStone1-Documents/
├── data/
│   ├── raw/               Task 1 output — sample documents
│   │   ├── digital_pdfs/  clean text-searchable PDFs (EN + FR)
│   │   ├── scanned_docs/  scanned / degraded PDFs (EN + FR)
│   │   └── images/        page-level image renders (PNG/JPG)
│   └── processed/         Task 6 output — cleaned / deskewed docs
├── outputs/               Task 9 output — one JSON per document
├── src/                   source code (preprocessor, ocr_engine,
│                          extractor, pipeline, run.py)
├── tests/                 unit tests
├── docs/                  entity_schema.md, ground_truth.xlsx, notes
├── generator/             data-collection + synthetic-doc scripts
├── requirements.txt
└── README.md
```

## Document naming convention

Filenames tell you origin, doc type, and language at a glance.

| Prefix      | Meaning                                    | Example                                   |
|-------------|--------------------------------------------|-------------------------------------------|
| `Real_`     | Downloaded from public internet sources    | `Real_MaterialCert_EN_Blackmer.pdf`       |
| `Synthetic_`| Programmatically generated (Faker + PDF)   | `Synthetic_Invoice_FR_01.pdf`             |

Language segment (`EN` / `FR`) follows the document type.

## Progress

| # | Task                         | Status | Artifact                                         |
|---|------------------------------|:------:|--------------------------------------------------|
| 1 | Collect sample documents     | ✅     | `data/raw/` — 137 files (see [raw/README.md](data/raw/README.md)) |
| 2 | Ground-truth spreadsheet     | ✅     | [`docs/ground_truth.csv`](docs/ground_truth.csv) + `docs/ground_truth.xlsx` (20 primary docs). See [ground_truth_README.md](docs/ground_truth_README.md) |
| 3 | Entity schema                | ✅     | [`docs/entity_schema.md`](docs/entity_schema.md) — 5 entities, EN+FR triggers, real examples, regex drafts |
| 4 | GitHub repo                  | ⏳     | remote                                           |
| 5 | Python environment           | ✅     | `requirements.txt`                               |
| 6 | Preprocessing                | ⏳     | `src/preprocessor.py`                            |
| 7 | OCR / text extraction        | ⏳     | `src/ocr_engine.py`                              |
| 8 | Rule-based extractor         | ⏳     | `src/extractor.py`                               |
| 9 | Full pipeline                | ⏳     | `src/pipeline.py`, `run.py`                      |
| 10| Metrics + 1-page summary     | ⏳     | `docs/results.md`                                |

### Task 1 summary

- 5 document types covered: **MaterialCert, WeldingPlan, FabricationSheet,
  InspectionReport, Invoice**.
- Languages: **English + French**.
- Modality mix: digital PDFs + scanned docs + standalone images.
- 87 real downloaded documents + 50 synthetic generated ones = 137 total.

### Task 2 summary

- 20 primary documents ground-truthed by hand (spec target: 15–20).
- Schema: `document_name, doc_type, language, modality, source, project_id,
  supplier, material, quantity, date, notes`.
- Source mix: 4 real_filled + 6 real_template + 4 real_educational +
  6 synthetic — honestly labelled so the Task 8 extractor is scored
  against realistic data.
