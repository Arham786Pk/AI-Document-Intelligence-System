# Milestone 2 — Summary & Explanation

> Plain-English walkthrough of Milestone 2. Tasks **01–07 are complete**; tasks
> **08–11 are pending** (need a Google Colab GPU). Companion to
> [`milestone1_summary.md`](milestone1_summary.md).

## What Milestone 2 is about

Milestone 1 built a **rule-based** extractor (regex + heuristics) for 11 invoice
fields. Milestone 2 moves toward **AI models** (LayoutLMv3 and RoBERTa) that learn
from labelled examples, adds a **12th entity** (`consumer_name`), and proves whether
the AI is actually better than the rules.

Tasks 01–07 are all **preparation** (baseline, data, labels, training export).
Tasks 08–11 are the **training, evaluation, and integration**.

---

## The 12 entities

`supplier_name`, `consumer_name` *(new in M2)*, `invoice_number`, `invoice_date`,
`siret`, `echeance`, `invoice_content`, `tva_percentage`, `tva_amount`,
`total_amount`, `payment_status`, `solde_du`. Full spec in
[`entity_schema.md`](entity_schema.md).

---

## Task-by-task (01–07, complete)

### Task 01 — Confirm & lock the M1 baseline
Measure the rule-based system so the AI has a number to beat.
- **Result:** macro F1 **67.78%**, overall accuracy **53.71%** (197 trustworthy docs).
- **Files:** [`m1_baseline.md`](m1_baseline.md), [`m1_baseline.csv`](m1_baseline.csv), `../outputs/metrics_summary.txt`.
- ⚠️ The brief's 55% target is already beaten on this dataset — the fair AI gate is the
  held-out **test split**, and the team should confirm the contractual number with the client.

### Task 02 — Expand the dataset to ≥50 invoices
- **Result:** **200 documents** — `../data/pdf/` (100) + `../data/images/` (100);
  **116 real + 84 synthetic**. Old→new name map in `../data/pdf_manifest.csv` / `images_manifest.csv`.

### Task 03 / 03b — Label Studio + 12-label schema
Set up the annotation tool and labels; add the `consumer_name` entity.
- **Files:** `../label_studio/label_config.xml`, [`label_studio_setup.md`](label_studio_setup.md),
  [`entity_schema.md`](entity_schema.md) (now 12 entities).

### Task 04 — Pre-annotate every document
Run the M1 pipeline to place draft labels so humans only review (3–5× faster).
- **Files:** `../label_studio/preannotations_pdf.json`, `..._images.json` (all 200, 0 offset errors).

### Task 05 — Annotation + quality control *(the most important task)*
Produce **correct** labels — the AI only learns what we label.
- **Ground truth for all 200 docs:**
  - 84 synthetic → exact (from the generator)
  - 32 real → exact, parsed from embedded **Factur-X / EN16931 XML**
  - 11 real → parsed from Chorus Pro template
  - 17 real → reused from Task-2 hand labels
  - 53 real → **read by eye** (every receipt, photo and invoice)
  - 3 real → flagged as **non-invoice guides** (Euresto, RAPPEL, SFR)
- **Annotation files:** `../label_studio/annotations_pdf.json`, `..._images.json`
  (3,071 spans, **0 offset errors**).
- **GT source files:** [`real_ground_truth.json`](real_ground_truth.json),
  [`synthetic_ground_truth.json`](synthetic_ground_truth.json),
  [`ground_truth_full.csv`](ground_truth_full.csv).

### Task 06 — Generate synthetic French invoices
Add clean, perfectly-labelled training data covering all 12 entities.
- **Result:** **84 synthetic docs** (15 PDFs + 69 images).
- **File:** `../scripts/generate_synthetic_invoices.py`.

### Task 07 — Export to FUNSD / LayoutLMv3 format + 70/15/15 split
Convert labels into the token-classification shape the AI needs (words + bounding
boxes + BIO tags), and split so evaluation is honest.
- **Result:** `../data/funsd/` → `train.jsonl` (140), `val.jsonl` (30), `test.jsonl` (30),
  `labels.txt` (25 BIO labels). **0 document overlap** between splits.
- **File:** `../scripts/build_funsd_dataset.py`.

---

## Field difficulty (from the M1 baseline)

| Strong (rules already good) | Weak (AI should help most) |
|---|---|
| echeance 86.7% · siret 83.5% · invoice_date 82.9% · supplier_name 80.2% | invoice_content 36.7% · **invoice_number 49.4%** · solde_du 49.4% |

**Why `invoice_number` is weak:** ~73/174 docs return nothing (receipts have no
invoice number), the rules sometimes grab the wrong token (`Facture` / `Fournisseur`),
and OCR garbles the code (`T109200`→`7109200`). Layout-aware models are expected to
fix exactly these cases.

---

## What's pending (08–11) — needs a Colab GPU

| Task | Description |
|------|-------------|
| 08 | Fine-tune **LayoutLMv3** on `data/funsd/` (Google Colab) |
| 09 | Fine-tune **RoBERTa** (Google Colab) |
| 10 | Evaluate **all 3** on the test split — **rule-based M1 vs LayoutLMv3 vs RoBERTa** — and build a comparison table |
| 11 | Wire the best model into the pipeline + write the final M2 delivery summary |

> **Note on "all 3" in Task 10:** the three are not three AI models. They are
> (1) the **M1 rule-based** extractor (baseline), (2) **LayoutLMv3**, (3) **RoBERTa** —
> all scored on the same held-out `data/funsd/test.jsonl`.

---

## Where everything lives (quick map)

| Item | Location |
|------|----------|
| Source PDFs / images | `data/pdf/` · `data/images/` |
| Ground truth | `docs/real_ground_truth.json` · `docs/synthetic_ground_truth.json` · `docs/ground_truth_full.csv` |
| Annotations (Label Studio) | `label_studio/annotations_*.json` |
| Pre-annotations | `label_studio/preannotations_*.json` |
| Training export (AI input) | `data/funsd/` (train/val/test) |
| M1 baseline | `docs/m1_baseline.md` · `outputs/metrics_summary.txt` |
| Generators / scripts | `scripts/generate_synthetic_invoices.py` · `scripts/build_funsd_dataset.py` |
