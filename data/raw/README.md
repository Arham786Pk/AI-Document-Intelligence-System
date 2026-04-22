# Task 1 — Sample Documents

Raw industrial documents collected for Milestone 1. Feeds the preprocessing,
OCR, and rule-based extraction pipelines (Tasks 6–9).

## Layout (spec-compliant)

```
data/raw/
├── digital_pdfs/     clean text-searchable PDFs
├── scanned_docs/     scanned / degraded PDFs
└── images/           standalone page images (PNG/JPG)
```

All languages (EN + FR) live side by side — language is encoded in the
filename, not the folder.

## Naming convention

```
Real_<DocType>_<Lang>_<Source>.(pdf|png|jpg)
Synthetic_<DocType>_<Lang>_<NN>.(pdf|png|jpg)
```

`<DocType>` ∈ `MaterialCert | WeldingPlan | FabricationSheet | InspectionReport | Invoice`
`<Lang>`    ∈ `EN | FR`

Prefix tells you origin at a glance: `Real_` = downloaded from public
sources, `Synthetic_` = generated via Faker + ReportLab/PIL.

## Counts

### `digital_pdfs/` — 64 files

| Doc type          | Real | Synthetic |
|-------------------|-----:|----------:|
| MaterialCert      |   11 |         4 |
| WeldingPlan       |   15 |         4 |
| FabricationSheet  |    2 |         4 |
| InspectionReport  |    5 |         4 |
| Invoice           |   11 |         4 |
| **Subtotal**      | **44** | **20**  |

### `scanned_docs/` — 31 files

| Doc type          | Real | Synthetic |
|-------------------|-----:|----------:|
| MaterialCert      |    7 |         4 |
| WeldingPlan       |    3 |         4 |
| FabricationSheet  |    0 |         4 |
| InspectionReport  |    1 |         4 |
| Invoice           |    0 |         4 |
| **Subtotal**      | **11** | **20**  |

### `images/` — 42 files

| Doc type          | Real | Synthetic |
|-------------------|-----:|----------:|
| MaterialCert      |   11 |         2 |
| WeldingPlan       |    7 |         2 |
| FabricationSheet  |    3 |         2 |
| InspectionReport  |    7 |         2 |
| Invoice           |    4 |         2 |
| **Subtotal**      | **32** | **10**  |

**Grand total:** 137 files → **87 real + 50 synthetic**

### Language split

| Language | Real | Synthetic | Total |
|----------|-----:|----------:|------:|
| English  |   56 |        25 |    81 |
| French   |   31 |        25 |    56 |

## Primary ground-truth set (Task 2)

The milestone spec targets 15–20 documents for manual ground-truth labelling.
A curated primary set of 20 documents is listed in
[`../../docs/ground_truth.csv`](../../docs/ground_truth.csv). The remaining
~117 documents act as a held-out corpus for Task 8 (rule-based extractor
generalisation testing).

## Sources

Real-document source URLs are listed in
[`real_document_sources.md`](real_document_sources.md).

## Regenerating

All four producer scripts are idempotent (skip existing files).

```bash
# Real PDFs → digital_pdfs/ + scanned_docs/
python generator/download_real_docs.py

# Real images → images/
python generator/download_real_images.py

# Synthetic PDFs → digital_pdfs/ + scanned_docs/
python generator/generate_docs.py

# Synthetic images → images/
python generator/generate_images.py
```
