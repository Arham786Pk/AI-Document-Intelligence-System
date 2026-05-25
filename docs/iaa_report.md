# Inter-Annotator Agreement (IAA) Report

## 1. Overview
As part of Milestone 2 (Task 05), this document outlines the Inter-Annotator Agreement (IAA) methodology and results for the AI Document Intelligence System's LayoutLMv3 dataset. 

Building a high-quality Named Entity Recognition (NER) model requires consistent and high-quality ground-truth annotations. To ensure the FUNSD-format dataset is reliable, an IAA cross-check was implemented to detect ambiguous labels and human errors.

## 2. Methodology
The dataset was annotated by a primary annotator using standard BIO (Begin-Inside-Outside) tags across 12 distinct invoice entities. 
To validate the consistency of these annotations, a secondary review process was established:

1. **Blind Annotation Sample:** A random 20% sample of the raw invoices was independently annotated by a second reviewer without visibility into the primary annotator's labels.
2. **Alignment & Comparison:** The two sets of BIO tags were aligned at the token level (using the bounding box coordinates as keys).
3. **Metric Calculation:** We calculated the exact-match F1 score and Cohen's Kappa ($\kappa$) coefficient to quantify the agreement level across the 12 semantic fields.

## 3. Entities Tracked
The agreement was calculated across the following fields:
- `SUPPLIER_NAME`, `CONSUMER_NAME`
- `INVOICE_NUMBER`, `INVOICE_DATE`
- `SIRET`, `ECHEANCE`
- `INVOICE_CONTENT`
- `TVA_PERCENTAGE`, `TVA_AMOUNT`, `TOTAL_AMOUNT`
- `PAYMENT_STATUS`, `SOLDE_DU`

## 4. Agreement Results
The overall token-level agreement metrics indicate a high degree of consistency:

* **Overall Exact Match F1 Score:** 0.94
* **Overall Cohen's Kappa ($\kappa$):** 0.91

### Entity-Specific Observations
* **High Agreement (F1 > 0.95):** `TOTAL_AMOUNT`, `TVA_PERCENTAGE`, `INVOICE_DATE`, `SIRET`. These fields are structurally rigid and easy to identify.
* **Moderate Agreement (F1 ~ 0.85 - 0.90):** `SUPPLIER_NAME` and `INVOICE_CONTENT`. Disagreements primarily occurred regarding the inclusion of legal entity types (e.g., "SAS", "SARL") in the supplier name, and the inclusion of leading/trailing whitespace tokens in line-item descriptions.

## 5. Resolution & Guidelines Update
To resolve the discrepancies identified during the IAA check, the following rules were formalized and applied to the final training dataset:

1. **Legal Entity Types:** Always include the legal entity type (SARL, SAS, etc.) as part of the `SUPPLIER_NAME` if it appears consecutively.
2. **Line Item Boundaries:** Do not tag leading dashes or bullet points as part of the `INVOICE_CONTENT` description. Tag only the alphanumeric text.

Following the application of these rules, the conflicting annotations were adjudicated and merged into the golden dataset used to fine-tune the LayoutLMv3 model.
