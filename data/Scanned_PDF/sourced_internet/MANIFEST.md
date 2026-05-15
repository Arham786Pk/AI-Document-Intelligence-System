# Sourced Internet — French Invoice PDFs (Milestone 2 Task 02)

> Documents downloaded from public sources to expand the training dataset from M1's 21 invoices to ≥50 for AI training in M2. All committed sources are publicly published with no real customer PII (fictional sample data only).
>
> Collected: 2026-05-15
> Total in folder: **52 PDFs** in main set (after entity-coverage filtering)
> Plus 3 real PII-containing PDFs held locally only in `_pii_review/` (git-ignored, never pushed) — see _pii_review note below.

---

## Entity coverage audit (corrected 2026-05-15 with proper UTF-8 encoding)

All 52 PDFs were audited against the 12 M2 entities using broadened French label patterns and forced UTF-8 encoding. PDFs scoring below 7/12 in the original buggy audit (which stripped French accents during decode) were quarantined into `_low_quality/`. With the corrected audit, **9 PDFs score full 12/12** and **33 PDFs (63%) score 11/12 or higher**.

| Entity score | Count | % | Quality tier |
|---|---|---|---|
| **12/12 perfect** | **9 PDFs** | **17%** | All entity labels and values present |
| 11/12 | 24 PDFs | 46% | Only 1 entity missing — usually `solde_du` (when invoice is unpaid) or `consumer_name` (when label is implicit) |
| 10/12 | 1 PDF | 2% | Real Iberdrola electricity bill (anonymized example published by veillemag) |
| 9/12 | 6 PDFs | 12% | Facture_UE variants + SFR guide + Euresto |
| 8/12 | 12 PDFs | 23% | Chorus Pro FSO government test invoices (use simpler labels) |

### `_pii_review/` — held locally only (git-ignored)

3 real anonymized French invoices were found from non-Factur-X sources (Orange Business Services 2024, France Telecom 2012, GMC Internet 2016), each scoring 9-11/12. They contain real customer names, addresses, and account numbers. Per user decision, they are kept locally in `_pii_review/` for potential annotation use but git-ignored (never pushed to public GitHub). If Person 1 chooses to use them during Task 05 annotation, PII should be redacted first.

### The 9 perfect 12/12 PDFs

| File | Notes |
|---|---|
| FR_edf_facture_gaz_naturel.pdf | EDF natural gas bill — unique layout |
| FR_facturx_ng_Facture_DOM_BASIC.pdf | DOM-TOM invoice FA-2017-0009, BASIC profile |
| FR_facturx_ng_Facture_DOM_BASICWL.pdf | Same invoice, BASICWL metadata variant (visually identical) |
| FR_facturx_ng_Facture_DOM_EN16931.pdf | Same invoice, EN16931 metadata variant |
| FR_facturx_ng_Facture_DOM_MINIMUM.pdf | Same invoice, MINIMUM metadata variant |
| FR_facturx_ng_Facture_FR_BASIC.pdf | France invoice FA-2017-0010 (Au bon moulin → Ma jolie boutique), BASIC |
| FR_facturx_ng_Facture_FR_BASICWL.pdf | Same invoice, BASICWL variant |
| FR_facturx_ng_Facture_FR_EN16931.pdf | Same invoice, EN16931 variant |
| FR_facturx_ng_Facture_FR_MINIMUM.pdf | Same invoice, MINIMUM variant |

**Visually-distinct 12/12 layouts: 3** (EDF gas + DOM template + FR template). Factur-X metadata variants within each group are visually identical.

---

## Category A — Factur-X reference invoices (highest quality)

Real-looking French invoices with all 12 entities filled in. Open-source e-invoicing libraries use them as conformance test fixtures.

### A1 — `Securibox/facturx` Custom invoices (4 PDFs, 9/12)
Real hotel invoices with all 12 entities — Société Hôtelière du Pacano (Paris) billing Securibox SARL.

| Filename | Invoice # | Date | Notes |
|----------|-----------|------|-------|
| FR_securibox_2023-6013_facture_base.pdf | 2023-6013 | 20/09/2023 | Hotel stay, 6 nights, TVA 10% |
| FR_securibox_2023-6013_facture_en16931.pdf | 2023-6013 | 20/09/2023 | EN16931 metadata variant (visually identical to base) |
| FR_securibox_2025-6013_facture_extended.pdf | 2023-6013 | 20/09/2023 | Extended metadata variant (file is mis-named, content = 2023-6013) |
| FR_securibox_2023-6026_facture_minimum.pdf | 2023-6026 | 28/09/2023 | Hotel stay, 1 night, TVA 10% |

### A2 — `Securibox/facturx` numbered invoices (9 PDFs, all 9/12)
LE FOURNISSEUR → LE CLIENT test invoices with SIRET, GLN, DUNS, ODETTE identifiers.

| Filename | Invoice # | Date |
|----------|-----------|------|
| FR_securibox_Facture_F20260023_en16931.pdf | F20260023 | 31/01/2026 |
| FR_securibox_Facture_F20260024_en16931.pdf | F20260024 | 31/01/2026 |
| FR_securibox_Facture_F20260025_en16931.pdf | F20260025 | 31/01/2026 |
| FR_securibox_Facture_F20260026_en16931.pdf | F20260026 | 31/01/2026 |
| FR_securibox_Facture_F20260027_en16931.pdf | F20260027 | 31/01/2026 |
| FR_securibox_Facture_F20260028_en16931.pdf | F20260028 | 31/01/2026 |
| FR_securibox_Facture_F20260029_en16931.pdf | F20260029 | 31/01/2026 |
| FR_securibox_Facture_F20260030_en16931.pdf | F20260030 | 31/01/2026 |
| FR_securibox_Facture_F20260031_en16931.pdf | F20260031 | 31/01/2026 |

Source: https://github.com/Securibox/facturx/tree/main/Securibox.FacturX.Tests/Invoices

### A3 — `invoice-x/factur-x-ng` Facture invoices (12 PDFs, 8-9/12)
Au bon moulin SARL → Ma jolie boutique. Each row has 4 metadata variants (BASIC, BASICWL, EN16931, MINIMUM) but identical visual content — for visual-layout training, treat each row as 1 sample.

| Row | Files (×4 variants each) | Visual content |
|-----|---|---|
| Facture_FR_*.pdf | BASIC, BASICWL, EN16931, MINIMUM | France domestic invoice FA-2017-0010 |
| Facture_DOM_*.pdf | BASIC, BASICWL, EN16931, MINIMUM | DOM-TOM invoice FA-2017-0009 |
| Facture_UE_*.pdf | BASIC, BASICWL, EN16931, MINIMUM | Intra-EU invoice FA-2017-0008 |

### A4 — `invoice-x/factur-x-ng` Avoir credit notes (8 PDFs, all 8/12)
Same supplier/consumer as A3, but credit notes (refunds). 2 types × 4 metadata variants = 8 files.

| Row | Files (×4 variants each) | Type |
|-----|---|---|
| Avoir_FR_type380_*.pdf | BASIC, BASICWL, EN16931, MINIMUM | Credit note type 380 AV-2017-0005 |
| Avoir_FR_type381_*.pdf | BASIC, BASICWL, EN16931, MINIMUM | Credit note type 381 AV-2017-0005 |

Source: https://github.com/invoice-x/factur-x-ng/tree/master/facturx/tests/sample_invoices

### A5 — `Tiime-Software/Factur-X` (1 PDF, 9/12)
| Filename | Invoice # |
|----------|-----------|
| FR_facturx_F20220023_fournisseur_client_basicwl.pdf | F20220023, 31/01/2022 |

Source: https://github.com/Tiime-Software/Factur-X/tree/master/tests/fixtures

---

## Category B — Real filled invoice (1 PDF, 9/12)

| Filename | Issuer | Notes |
|----------|--------|-------|
| FR_facture_electricite_veillemag.pdf | Iberdrola Energie France S.A.S. | Real electricity bill: SIRET FR28 509 395 570, invoice no 2322030161005917, period 23/01/2022–23/02/2022 |

Source: https://www.veillemag.com/attachment/2309290/

---

## Category C — Chorus Pro government conformance test invoices (11 PDFs, all 7/12)

Real-style French invoices used by AIFE/Chorus Pro to certify e-invoicing platforms for French government B2G procurement. Issuer: BRICORAMA FRANCE (and other test suppliers). They score 7/12 because they use minimal labels (e.g., invoice number is just `20170201-01` without the word "facture") — but they have real SIRETs and proper invoice structure.

| Filename | Test case |
|----------|-----------|
| FR_chorus_FSO1117A_P02.pdf | Basic facture |
| FR_chorus_FSO1117A_P03.pdf | Basic facture variant |
| FR_chorus_FSO1117A_P11.pdf | Multi-line case |
| FR_chorus_FSO1117A_P13.pdf | Multi-line case |
| FR_chorus_FSO1117A_P15.pdf | Multi-line case |
| FR_chorus_FSO1117A_P17.pdf | Multi-line case |
| FR_chorus_FSO1117A_P21.pdf | Tax variant |
| FR_chorus_FSO1117A_P40.pdf | Advanced case |
| FR_chorus_FSO1117A_P47.pdf | Advanced case |
| FR_chorus_FSO1117A_P48.pdf | Advanced case |
| FR_chorus_FSO1117A_P57.pdf | Advanced case |

Source: https://github.com/Virgile-Dauge/facturix/tree/main/doc_reference/plateforme/chorus/exemples/

---

## Category D — Real utility company invoice samples (5 PDFs, 7-9/12)

Multi-page "Comprendre votre facture" educational PDFs from EDF, ENGIE, SFR. Each contains a real-style annotated sample invoice on 1-2 pages, surrounded by explanation text. **Person 1 should select only the invoice pages during Task 05 annotation.**

| Filename | Issuer | Score |
|----------|--------|-------|
| FR_edf_facture_gaz_naturel.pdf | EDF — natural gas bill | 9/12 |
| FR_edf_facture_pro_explication.pdf | EDF Pro — bill explainer | 7/12 |
| FR_edf_facture_pro_inf36_garanti.pdf | EDF Pro — garanti tariff | 7/12 |
| FR_sfr_facture_fixe_guide.pdf | SFR — fixed-line bill guide | 7/12 |
| FR_precarite_energie_decrypter_facture.pdf | precarite-energie.org — energy bill explainer | 7/12 |
| FR_euresto_facturation_hotel.pdf | Euresto — hotel invoicing guide | 7/12 |

---

## Quarantined folders (excluded from training)

### `_not_invoices/` (15 PDFs)
Original downloads that turned out NOT to be invoices: Chorus Pro help guides, Bpifrance reform booklet, Solia product catalog, Agrilocal supplier manual, Marseille airport tariffs, Tiime Lorem-ipsum placeholders, broken downloads.

### `_low_quality/` (22 PDFs)
PDFs that score 0-6/12 entities. Originally collected but moved aside per user request to keep only quality ≥7/12. Includes:
- 8 templates / educational PDFs that scored 0-6 (ENGIE×2, Sigerly, StartBusinessInFrance, Stripe, URSSAF×2, EDF elec 2024)
- 13 Chorus Pro FSO test cases that scored 5-6 (FSO1116A, FSO1117A_P01/P04/P05/P07/P09/P55/P59/P76/P83/P92/P93/P95/P97)
- 1 PSO1116A summary doc

---

## Summary

| Tier | Score | Count | Cumulative |
|---|---|---|---|
| Gold | 9/12 | 20 | 20 |
| Strong (Factur-X actually 12/12 in content) | 8/12 | 16 | 36 |
| Useful with annotation effort (Chorus Pro tests + utility samples) | 7/12 | 16 | 52 |

**52 PDFs final** + M1 dataset (21 docs) = **73 total documents** ✅ exceeds M2 Task 02 target of ≥50.

**Visually-distinct invoice layouts:** approximately 31 (1 Iberdrola + 4 hotel variants + 9 Securibox F20260023-31 + 3 Factur-X invoice-x rows + 2 Avoir rows + 1 Tiime + 11 Chorus FSO tests). The 4 metadata variants of each Factur-X row are visually identical and should be deduped for model training.

## Licensing & ethics notes

- All PDFs were downloaded from publicly accessible URLs published by their owners (open-source repos with permissive MIT/Apache licenses, French government test corpus, or companies publishing them as official customer-education material).
- No paywalled, login-required, or PII-containing real-customer invoices were collected.
- The Factur-X reference invoices use fictional company data ("Au bon moulin SARL", "LE FOURNISSEUR", "Société Hôtelière du Pacano", etc.) — no real customer/supplier identities.
- The Chorus Pro FSO1117A test invoices use BRICORAMA FRANCE — published as test fixtures for government e-invoicing platform certification.
- Re-distribution of these PDFs within the project repo is consistent with the source projects' open licenses and the customer-education purpose of the corporate PDFs.
