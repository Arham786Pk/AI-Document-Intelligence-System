# Milestone 1 Baseline — Locked Scores

> **Task 01 of Milestone 2:** Confirm and lock M1 baseline F1 scores before AI training begins.

Source of truth: [`outputs/metrics_summary.txt`](../outputs/metrics_summary.txt)
Evaluation set: **19 French invoices** compared against [`docs/ground_truth.csv`](ground_truth.csv) (20 rows; 1 invoice in GT had no matching extracted JSON).
Generated: 2026-05-15

---

## Per-entity F1 (the 11 entities labelled in Milestone 1)

| Entity | Precision | Recall | F1 | Status |
|--------|-----------|--------|----|--------|
| supplier_name | 21.05% | 100.00% | **34.78%** | Needs work |
| invoice_number | 77.78% | 46.67% | **58.33%** | Moderate |
| invoice_date | 41.18% | 87.50% | **56.00%** | Moderate |
| siret | 57.14% | 36.36% | **44.44%** | Weak |
| echeance | 100.00% | 64.29% | **78.26%** | Good |
| invoice_content | 77.78% | 41.18% | **53.85%** | Moderate |
| tva_percentage | 90.00% | 50.00% | **64.29%** | Good |
| tva_amount | 87.50% | 38.89% | **53.85%** | Moderate |
| total_amount | 90.00% | 50.00% | **64.29%** | Good |
| payment_status | 89.47% | 100.00% | **94.44%** | Excellent |
| solde_du | 100.00% | 100.00% | **100.00%** | Perfect |

## Macro averages (arithmetic mean across 11 fields)

| Metric | Value |
|--------|-------|
| Macro Precision | **75.63%** |
| Macro Recall | **64.99%** |
| **Macro F1** | **63.87%** |

## 12th entity (added for Milestone 2)

| Entity | Status |
|--------|--------|
| consumer_name | **Not implemented in M1.** Rules cannot reliably separate the consumer block (`DESTINATAIRE`, `FACTURER A`, `CLIENT`, `ACHETEUR`, `POUR LE COMPTE DE`) from the supplier block. This is the primary motivation for layout-aware models in M2. |

---

## Discrepancy with the Milestone 2 brief

The Milestone 2 brief states:
> *"Milestone 2 Target: Macro F1 must exceed 55.0% on the same test documents using the trained AI model."*

And its baseline table lists `OVERALL ... F1 55.0% Baseline`.

**Our actual macro F1 is 63.87%, not 55.0%.** The 55% figure in the brief likely comes from a micro-averaged or differently-weighted calculation, but recomputing the arithmetic mean of the per-field F1s shown in the brief table itself yields ~63.9%, matching our number.

### What this means in practice

| | F1 |
|---|----|
| Brief's stated baseline | 55.00% |
| Actual M1 macro F1 (this repo) | **63.87%** |
| LayoutLMv3 target per brief | > 55.00% |
| **Effective LayoutLMv3 target to beat M1 rules** | **> 63.87%** |

The brief's 55% bar is already passed by the rule-based system. To justify deploying LayoutLMv3 in M2 Task 11, it must beat **63.87%**, not 55%. The team should clarify with the client which number is the contractual gate before training starts.

---

## How to import into Google Sheets (per Task 01 brief)

1. In Google Sheets: **File → Import → Upload**
2. Drop [`docs/m1_baseline.csv`](m1_baseline.csv)
3. Choose: "Replace spreadsheet" or "Insert new sheet(s)"
4. Rename column header `F1` → `M1 Baseline` per the brief instruction
5. Share the sheet with both team members and Muhammad Ahmed

---

## Weakest fields (priority targets for M2 training)

| Rank | Field | F1 | Why it fails today |
|------|-------|----|--------------------|
| 1 | `supplier_name` | 34.78% | Rules tag every header line — precision is the bottleneck. Layout-aware model needed. |
| 2 | `siret` | 44.44% | 14-digit pattern matches other numeric IDs (phone, invoice). Position + context needed. |
| 3 | `invoice_content` | 53.85% | Multi-row free-text descriptions get split. |
| 4 | `tva_amount` | 53.85% | Confused with subtotals on some layouts. |
| 5 | `invoice_date` | 56.00% | Many date format variants not covered. |

These five fields are the most likely to benefit from LayoutLMv3's spatial understanding.

---

## Completion checklist

- [x] Read `outputs/metrics_summary.txt`
- [x] Transcribe all 11 F1 scores
- [x] Compute macro precision, recall, F1
- [x] Compare against M2 brief's 55% target
- [x] Write CSV ready for Google Sheets import: [`docs/m1_baseline.csv`](m1_baseline.csv)
- [x] Write version-controlled reference: this file
- [ ] **Person 1:** Upload CSV to a shared Google Sheet; share link with team
- [ ] **Person 2:** Confirm sheet values match this doc; sign off
- [ ] **Team:** Clarify with client whether the gate is 55% (brief literal) or 63.87% (actual baseline)
