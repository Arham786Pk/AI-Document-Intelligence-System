# `data/raw/extra/` — 117 reference / unused documents

Documents collected during Task 1 that are **not** part of the Milestone-1
ground-truth set. The pipeline does **not** read this folder.

## Why kept?

- Honest record of what was downloaded / generated, even if not labelled.
- Future expansion: extending ground truth (Task 2) is just a matter of
  picking docs from here, labelling them, and moving them into `used/`.
- Includes templates, foreign-language guides, extra synthetic variants
  (e.g. the "scanned-style" copies of the synthetic-digital PDFs), and the
  page-1 image renders.

## Layout

```
extra/
├── digital_pdfs/   real public PDFs not chosen for labelling
├── scanned_docs/   degraded / scanned variants (incl. synthetic-scanned dups)
└── images/         standalone PNG/JPG renders from Task 1
```

If you want to use any of these in the pipeline, add a row for it in
[`docs/ground_truth.csv`](../../../docs/ground_truth.csv) and move the file
into the matching `data/raw/used/<modality>/` folder.
