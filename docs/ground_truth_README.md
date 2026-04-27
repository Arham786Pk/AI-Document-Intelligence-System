# Task 2 — Ground-Truth Spreadsheet

Primary set of 20 French (FR) documents with manually-verified expected
values for the 5 target entities. Every row has populated entity fields —
no blank-template or educational-only entries — so the file functions as
a non-empty answer key when scoring the rule-based extractor (Task 8)
and the full pipeline (Tasks 9–10).

## Files

| File | Purpose |
|------|---------|
| `ground_truth.csv`  | source of truth — version-controlled, easy to diff |
| `ground_truth.xlsx` | formatted Excel workbook (header styled, wrapped, filtered) — regenerated from the CSV via `generator/build_ground_truth_xlsx.py` |

## Columns

Per Milestone 1 spec § Task 02, plus three extras for downstream pipeline
traceability (`language`, `modality`, `source`).

| Column          | Meaning |
|-----------------|---------|
| `document_name` | filename (matches `data/raw/**/document_name`) |
| `doc_type`      | `MaterialCert` \| `WeldingPlan` \| `FabricationSheet` \| `InspectionReport` \| `Invoice` |
| `language`      | `EN` or `FR` |
| `modality`      | `digital` or `scanned` |
| `source`        | `real_filled` \| `real_template` \| `real_educational` \| `synthetic` |
| `project_id`    | unique code / cert no / WPS no / PO no — blank if not present |
| `supplier`      | issuing company / vendor — blank if not present |
| `material`      | material spec / grade — blank if not present |
| `quantity`      | number + unit (e.g. `400 Kgs`, `287 pcs`) — blank if not present |
| `date`          | ISO format `YYYY-MM-DD` for consistency (note: originals use DD/MM/YYYY, DD.MM.YYYY, or YYYY-MM-DD interchangeably — rule-based extractor in Task 8 must handle all three) |
| `notes`         | anything the extractor should be aware of: blank fields, source type, heat numbers, context |

## Methodology

Each document was opened manually and inspected page-by-page. Values were
transcribed exactly as they appear on the document. The dataset was
deliberately filtered to French documents that contain populated fields:
real blank templates, educational/reference PDFs, and EN-only docs were
excluded so every row carries genuine entity values. The `source` column
marks each document into one of two categories:

- **real_filled** — real operational FR document with genuine project
  data (heat numbers, cert numbers, filled fields). These are the most
  valuable for extractor accuracy measurement. Examples: La Robinetterie
  3.1 certs (134822, 160629), Dillinger 3.1/3.2 certs (Antelis), Ugitech
  food-grade attestation.
- **synthetic** — Faker-generated PDF from `generator/generate_docs.py`.
  Full ground truth is guaranteed (the generator writes what it seeded).
  Used to fill out the doc-type matrix where real filled FR samples are
  scarce (WeldingPlan, FabricationSheet, InspectionReport, Invoice).

## Primary set composition (20 FR docs)

| Doc type         | real_filled | synthetic digital | synthetic scanned | total |
|------------------|:-----------:|:-----------------:|:-----------------:|:-----:|
| MaterialCert     | 5           | 2                 | 1                 | 8     |
| WeldingPlan      | 1           | 2                 | 1                 | 4     |
| FabricationSheet | 0           | 2                 | 0                 | 2     |
| InspectionReport | 0           | 2                 | 1                 | 3     |
| Invoice          | 0           | 2                 | 1                 | 3     |
| **Total**        | **6**       | **10**            | **4**             | **20**|

Language: 20 FR. Modality: 14 digital + 6 scanned. The 4 scanned synthetic
rows use the path-prefix `scanned_docs/` in `document_name` to disambiguate
from their digital twins (same generator seed, degraded image quality).

## Held-out corpus

The remaining ~120 documents in `data/raw/` are **not** ground-truthed here.
They act as a held-out test set for Task 8 (rule-based extractor
generalisation). Task 8 will pick a random sample, run the extractor, and
spot-check the output — this validates that the rules don't just memorise
the primary 15 FR docs. EN documents and FR blank-templates / educational
PDFs are part of this held-out pool.

## Regenerating the XLSX

```bash
python generator/build_ground_truth_xlsx.py
```

The CSV is the source of truth. Edit the CSV, then re-run to refresh the
XLSX. The XLSX is regenerated deterministically (safe to overwrite).
