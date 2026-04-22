# Task 2 — Ground-Truth Spreadsheet

Primary set of 20 documents with manually-verified expected values for the
5 target entities. Used as the answer key when scoring the rule-based
extractor (Task 8) and the full pipeline (Tasks 9–10).

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
transcribed exactly as they appear on the document; missing values are
left blank. The `source` column marks each document into one of four
honest categories:

- **real_filled** — real operational document with genuine project data
  (heat numbers, cert numbers, filled fields). These are the most valuable
  for extractor accuracy measurement. Examples: NST inspection cert, La
  Robinetterie 3.1 cert, Dillinger 3.2 cert, Sandvik WPS SS-011.
- **real_template** — real document from a real vendor, but a blank form
  where every fillable field is empty. Still useful — the extractor must
  not hallucinate values when the fields are blank. Example: AWS D17.1 WPS
  form, LANL Weld Inspection Report template, Tennant commercial-invoice
  template.
- **real_educational** — real PDF from a real source, but the content is
  training / reference / standard material rather than an operational
  document. Example: CEREMA QMOS/DMOS presentation, DOE Module 2A slide
  deck, Ifsttar Mai 2020 auscultation guide.
- **synthetic** — Faker-generated PDF from `generator/generate_docs.py`.
  Full ground truth is guaranteed (the generator writes what it seeded).
  Used to plug gaps where real-filled samples are scarce (all 5 doc types
  × both languages are covered by at least one synthetic).

## Primary set composition (20 docs)

| Doc type         | real_filled | real_template | real_educational | synthetic | total |
|------------------|:-----------:|:-------------:|:----------------:|:---------:|:-----:|
| MaterialCert     | 3           | 1             | 0                | 1         | 5     |
| WeldingPlan      | 1           | 1             | 1                | 1         | 4     |
| FabricationSheet | 0           | 0             | 2                | 2         | 4     |
| InspectionReport | 0           | 2             | 1                | 1         | 4     |
| Invoice          | 0           | 2             | 0                | 1         | 3     |
| **Total**        | **4**       | **6**         | **4**            | **6**     | **20**|

Language split: 12 EN + 8 FR. Modality: 18 digital + 2 scanned.

## Held-out corpus

The remaining ~117 documents in `data/raw/` are **not** ground-truthed here.
They act as a held-out test set for Task 8 (rule-based extractor
generalisation). Task 8 will pick a random sample, run the extractor, and
spot-check the output — this validates that the rules don't just memorise
the 20 primary docs.

## Regenerating the XLSX

```bash
python generator/build_ground_truth_xlsx.py
```

The CSV is the source of truth. Edit the CSV, then re-run to refresh the
XLSX. The XLSX is regenerated deterministically (safe to overwrite).
