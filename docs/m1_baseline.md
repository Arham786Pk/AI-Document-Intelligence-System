# Milestone 1 Baseline — Locked Scores

> **Task 01 of Milestone 2:** Confirm and lock M1 baseline F1 scores before AI training begins.

Source of truth: [`outputs/metrics_summary.txt`](../outputs/metrics_summary.txt)
**Re-baselined 2026-05-22** on the full restructured dataset.
Evaluation set: **197 documents** (84 synthetic + 113 real invoices) compared against
[`docs/ground_truth_full.csv`](ground_truth_full.csv). The 3 non-invoice guide PDFs are excluded.

> **History:** the original M1 baseline (2026-05-15) was measured on only 19 noisy real
> receipts and scored **macro F1 63.87% / overall accuracy 45.51%**. After the M2
> dataset expansion to 200 docs and a full pipeline re-run, the baseline was re-measured
> and **adopted** at the numbers below.

---

## Per-entity F1 (the 11 entities labelled in Milestone 1)

| Entity | Precision | Recall | F1 | Status |
|--------|-----------|--------|----|--------|
| supplier_name | 68.04% | 97.78% | **80.24%** | Good |
| invoice_number | 56.44% | 43.85% | **49.35%** | Moderate |
| invoice_date | 80.23% | 85.71% | **82.88%** | Good |
| siret | 79.63% | 87.76% | **83.50%** | Good |
| echeance | 93.94% | 80.52% | **86.71%** | Good |
| invoice_content | 29.53% | 48.35% | **36.67%** | Weak |
| tva_percentage | 73.68% | 62.82% | **67.82%** | Good |
| tva_amount | 82.83% | 48.24% | **60.97%** | Moderate |
| total_amount | 88.24% | 66.67% | **75.95%** | Good |
| payment_status | 56.35% | 100.00% | **72.08%** | Moderate |
| solde_du | 50.00% | 48.89% | **49.44%** | Weak |

## Macro averages (arithmetic mean across 11 fields)

| Metric | Value |
|--------|-------|
| Macro Precision | **68.99%** |
| Macro Recall | **70.05%** |
| **Macro F1** | **67.78%** |
| Overall field-match accuracy | **53.71%** |

## 12th entity (added for Milestone 2)

| Entity | Status |
|--------|--------|
| consumer_name | **Not implemented in the M1 rule-based extractor.** Ground truth now exists for it (all synthetic + most real docs), but rules cannot reliably separate the consumer block (`DESTINATAIRE`, `FACTURÉ À`, `CLIENT`, `ACHETEUR`, `POUR LE COMPTE DE`) from the supplier block. This is the primary motivation for layout-aware models in M2. |

---

## ⚠️ Important: the brief's 55% target is already beaten

The Milestone 2 brief states:
> *"Milestone 2 Target: Macro F1 must exceed 55.0% on the same test documents using the trained AI model."*

| | Macro F1 |
|---|----|
| Brief's stated target | 55.00% |
| **Adopted M1 baseline (this dataset)** | **67.78%** |
| **Effective target for LayoutLMv3 to be worth deploying** | **> 67.78%** |

The rule-based M1 system already exceeds the 55% bar by ~13 points on the current
dataset (now dominated by clean synthetic + clean printed invoices that rules handle
well). **Action for the team:** clarify with the client whether the contractual gate is
the literal 55% or "beat the M1 baseline (67.78%)" before investing in training. A fair
AI-vs-rules comparison should be run on the **held-out test split only** (Task 07 /
Task 10), not the full set.

---

## Weakest fields (priority targets for M2 training)

| Rank | Field | F1 | Why it fails today |
|------|-------|----|--------------------|
| 1 | `invoice_content` | 36.67% | Multi-row free-text descriptions get split/garbled, esp. on receipts. |
| 2 | `invoice_number` | 49.35% | Non-standard refs; receipts often have none. |
| 3 | `solde_du` | 49.44% | Present on a minority of invoices; confused with total. |
| 4 | `tva_amount` | 60.97% | Confused with subtotals on some layouts. |
| 5 | `tva_percentage` | 67.82% | Mixed-rate invoices hurt recall. |

These fields are the most likely to benefit from LayoutLMv3's spatial understanding.

---

## How to import into Google Sheets (per Task 01 brief)

1. In Google Sheets: **File → Import → Upload**
2. Drop [`docs/m1_baseline.csv`](m1_baseline.csv)
3. Rename column header `F1` → `M1 Baseline` per the brief instruction
4. Share with both team members and Muhammad Ahmed

---

## Completion checklist

- [x] Re-run full pipeline on all 200 docs
- [x] Recompute per-field + macro metrics on 197 trustworthy docs
- [x] Adopt new baseline (macro F1 67.78%, accuracy 53.71%)
- [x] Update CSV + this doc
- [ ] **Team:** clarify with client whether the gate is 55% or 67.78%
- [ ] **Person 1:** upload CSV to shared Google Sheet
