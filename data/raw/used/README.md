# `data/raw/used/` — 20 documents in the Milestone-1 pipeline

These are the **only** documents the Milestone-1 pipeline (Tasks 6–10) reads.
They map 1-to-1 with the rows in [`docs/ground_truth.csv`](../../../docs/ground_truth.csv),
so every prediction can be scored against a labelled answer.

## Layout

```
used/
├── digital_pdfs/   18 PDFs (text-searchable, light preprocessing path)
└── scanned_docs/    2 PDFs (scanned, full deskew/denoise/threshold path)
```

## Composition (matches ground_truth.csv)

| Doc type           | Real filled | Real template | Real educational | Synthetic | Total |
|--------------------|:-----------:|:-------------:|:----------------:|:---------:|:-----:|
| MaterialCert       | 3           | 1             | 0                | 1         | 5     |
| WeldingPlan        | 1           | 1             | 1                | 1         | 4     |
| FabricationSheet   | 0           | 0             | 2                | 2         | 4     |
| InspectionReport   | 0           | 2             | 1                | 1         | 4     |
| Invoice            | 0           | 2             | 0                | 1         | 3     |
| **Total**          | **4**       | **6**         | **4**            | **6**     | **20**|

## Why a separate folder?

`data/raw/extra/` holds the other 117 files we collected (extra real samples
+ synthetic-scanned variants + standalone images). They stayed in the repo for
audit and future expansion but are **not** read by the pipeline — keeping them
out of `used/` avoids any chance of silently scoring against unlabelled docs.
