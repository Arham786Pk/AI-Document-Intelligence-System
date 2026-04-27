# `data/raw/used/` — primary documents seeding the ground-truth set

These are the documents in `data/raw/used/` that Tasks 6–10 originally
targeted. The Milestone-1 ground truth was later refined to a 20-doc
French-only set with fully populated entity fields; **6 of those 20 docs
live in `data/raw/extra/`** because the held-out folder turned out to
contain real-filled FR PDFs that strengthen the eval set. The pipeline
loaders (`src/run.py`, `src/run_preprocess.py`) search both `used/` and
`extra/` so every row in [`docs/ground_truth.csv`](../../../docs/ground_truth.csv)
resolves correctly.

## Layout

```
used/
├── digital_pdfs/   original 18 digital PDFs (text-searchable)
└── scanned_docs/    original 2 scanned PDFs (deskew/denoise/threshold path)

extra/
├── digital_pdfs/   held-out FR + EN; 2 docs are referenced from ground_truth
├── scanned_docs/   held-out FR + EN; 6 docs (incl. 4 synthetic_FR_01_scanned variants) referenced from ground_truth
└── images/         standalone PNG/JPG (not in ground truth)
```

## Ground-truth composition (20 FR docs, all fully populated)

See [`docs/ground_truth_README.md`](../../../docs/ground_truth_README.md)
for the authoritative breakdown. Quick recap:

| Doc type         | real_filled | synthetic digital | synthetic scanned | total |
|------------------|:-----------:|:-----------------:|:-----------------:|:-----:|
| MaterialCert     | 5           | 2                 | 1                 | 8     |
| WeldingPlan      | 1           | 2                 | 1                 | 4     |
| FabricationSheet | 0           | 2                 | 0                 | 2     |
| InspectionReport | 0           | 2                 | 1                 | 3     |
| Invoice          | 0           | 2                 | 1                 | 3     |
| **Total**        | **6**       | **10**            | **4**             | **20**|

## Why both `used/` and `extra/` are now in scope

Originally `data/raw/extra/` was a held-out pool. The ground-truth refresh
pulled in 6 FR docs from there — 4 real-filled (Larobinetterie 160629,
Dillinger Antelis, Ugitech Alim, Cahier Soudage Filtres) plus 2 paired
scanned-modality synthetic variants — because they had genuine project
data missing from the original `used/` selection. The remaining ~110
files in `extra/` (EN docs, blank templates, educational PDFs) are still
the held-out test pool for Task 8 generalisation checks.
