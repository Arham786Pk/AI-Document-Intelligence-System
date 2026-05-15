# Sourced Internet — French Invoice PDFs (Milestone 2 Task 02)

> Documents downloaded from public sources to expand the training dataset from M1's 21 invoices to ≥50 for AI training in M2. All sources are publicly published — no PII-containing real invoices.
>
> Collected: 2026-05-15
> Total files in this folder: **36 PDFs**

---

## Category A — Factur-X reference invoices (highest quality)

Real-looking French invoices with all 12 entities filled in (supplier, consumer, dates, SIRET, TVA, amounts, payment terms, échéance, solde). These come from open-source e-invoicing libraries that use them as conformance test fixtures. All visually distinct between rows; the BASIC/BASICWL/EN16931/MINIMUM variants of each row differ only in embedded XML metadata — visual content is identical, so for layout-based training they should be treated as one sample per row.

| Filename | Source repo | Type | Visually distinct |
|----------|-------------|------|---|
| FR_facturx_F20220023_fournisseur_client_basicwl.pdf | Tiime-Software/Factur-X | Facture | yes |
| FR_facturx_ng_Facture_FR_*.pdf (×4) | invoice-x/factur-x-ng | Facture France (FA-2017-0010, Au bon moulin SARL) | 1 layout × 4 metadata variants |
| FR_facturx_ng_Facture_DOM_*.pdf (×4) | invoice-x/factur-x-ng | Facture DOM-TOM (FA-2017-0009) | 1 layout × 4 metadata variants |
| FR_facturx_ng_Facture_UE_*.pdf (×4) | invoice-x/factur-x-ng | Facture intra-UE (FA-2017-0008) | 1 layout × 4 metadata variants |
| FR_facturx_ng_Avoir_FR_type380_*.pdf (×4) | invoice-x/factur-x-ng | Avoir (credit note) type 380 (AV-2017-0005) | 1 layout × 4 metadata variants |
| FR_facturx_ng_Avoir_FR_type381_*.pdf (×4) | invoice-x/factur-x-ng | Avoir (credit note) type 381 (AV-2017-0005) | 1 layout × 4 metadata variants |

**Visual layout count from this category: 6**. Total file count: 21.

Source URLs:
- https://github.com/Tiime-Software/Factur-X/tree/master/tests/fixtures
- https://github.com/invoice-x/factur-x-ng/tree/master/facturx/tests/sample_invoices

---

## Category B — Real filled invoice (single, but the most authentic)

| Filename | Issuer | Notes |
|----------|--------|-------|
| FR_facture_electricite_veillemag.pdf | Iberdrola Energie France S.A.S. | Real electricity bill: SIRET FR28 509 395 570, invoice no 2322030161005917, period 23/01/2022–23/02/2022. Published as a reference example by veillemag.com. |

Source: https://www.veillemag.com/attachment/2309290/

---

## Category C — Templates with sample data

Blank-form invoices with placeholder names/amounts that demonstrate French invoice layout. Useful as visual variety for layout-based training; not useful for entity content training (placeholder data).

| Filename | Source |
|----------|--------|
| FR_urssaf_facturier_autoentrepreneur.pdf | URSSAF — official auto-entrepreneur invoice model |
| FR_urssaf_facturier_exemple_actualites.pdf | URSSAF Actualités — example facturier |
| FR_startbusinessfrance_template.pdf | StartBusinessInFrance.com — French invoice template (Mme. Nathalie Dupond sample) |
| FR_stripe_template.pdf | Stripe.com — minimal French invoice template (mostly blank) |

Source URLs:
- https://www.autoentrepreneur.urssaf.fr/portail/files/Facturier_AE.pdf
- https://www.autoentrepreneur.urssaf.fr/portail/files/Actualites/Exemple%20de%20facturier%20auto-entrepreneur%20.pdf
- https://mcusercontent.com/12f8d8ebc3e8ed04371944abb/files/e8ad9fb6-d2c8-e0b2-fd0d-40b654fc4509/French_Facture_template.pdf
- https://assets.stripeassets.com/fzn2n1nzq965/545hywSLXH7lfly1l5ZTfP/ec42e071753b04f6796958c2de4ef79d/en-US_Template__resources_more_paid-invoice-in-france.docx.pdf

---

## Category D — Utility "Comprendre votre facture" educational PDFs

Multi-page explainer documents from French energy providers. Each contains an annotated sample invoice IMAGE with arrows pointing to entity fields (supplier address, SIRET, échéance, TVA, total, etc.). **Only the page(s) showing the actual invoice are useful for training** — the surrounding pages are explanation text. Person 1 should select the relevant pages during Task 05 annotation.

| Filename | Issuer | Notes |
|----------|--------|-------|
| FR_edf_facture_elec_2024.pdf | EDF Entreprises | New electricity bill format (>36 kVA) |
| FR_edf_facture_pro_explication.pdf | EDF Pro | Pro bill explanation |
| FR_edf_facture_pro_inf36_garanti.pdf | EDF Pro | Pro bill, garanti tariff |
| FR_edf_facture_gaz_naturel.pdf | EDF | Natural gas bill |
| FR_engie_facture_gaz_elec_explication.pdf | ENGIE Particuliers | Gas + electricity bill explainer (image-based PDF) |
| FR_engie_pro_guide_2023.pdf | ENGIE Pro | Detailed bill guide, Nov 2023 |
| FR_sfr_facture_fixe_guide.pdf | SFR | Fixed-line bill reading guide |
| FR_sigerly_guide_factures_c2c3c4.pdf | SIGERLy | Electricity bill C2/C3/C4 (<36 kVA) explainer |
| FR_precarite_energie_decrypter_facture.pdf | precarite-energie.org | Décrypter une facture d'énergie (Fiche 18) |
| FR_euresto_facturation_hotel.pdf | Euresto | Hotel invoicing guide |

Source URLs (all public):
- https://www.edf.fr/sites/default/files/contrib/entreprise/Contrats-et-factures/votre-facture/comprendre-sa-facture/v19/desc_il13_facture_elec_dmep_om_sup36_cer_prix_dissocies_v2.pdf
- https://www.edf.fr/sites/entreprise/files/2024-04/facture_elec_om_sup36_kva.pdf
- https://www.edf.fr/sites/default/files/contrib/entreprise/Contrats-et-factures/votre-facture/comprendre-sa-facture/v19/desc_dmep_om_inf36_garanti_pro_prix_integres.pdf
- https://www.edf.fr/sites/default/files/contrib/entreprise/Contrats-et-factures/votre-facture/comprendre-sa-facture/v19/desc_dmep_gaz_naturel_t3.pdf
- https://particuliers.engie.fr/content/dam/images/fiches-pedagogiques/15_COMPRENDRE__la_facture_de_gaz_naturel_ou_d_electricite.pdf
- https://pro.engie.fr/sites/default/files/2023-11/Guide%20explication%20facture.pdf
- https://static.s-sfr.fr/media/facture-fixe.pdf
- https://sigerly.fr/wp-content/uploads/2020/12/Guide-factures-C2-C3-C4.pdf
- https://www.precarite-energie.org/wp-content/uploads/2021/04/fiche18-decrypter-une-facture-d-energie-23042021.pdf
- https://euresto.com/documentation/docs/H%C3%B4tellerie/Guide%20de%20la%20facturation%20h%C3%B4tel%20version%2031041%20PDF.pdf

---

## Quarantined — `_not_invoices/` subfolder

These were downloaded during the search but turned out to NOT be invoices (help guides, FAQs, catalogs, Lorem ipsum placeholders, or broken downloads). Kept in `_not_invoices/` for traceability but should NOT be used for training.

| Filename | Why excluded |
|----------|--------------|
| FR_chorus_pro_aife_fiche.pdf | Help guide on how to deposit invoices on Chorus Pro, not an invoice |
| FR_engie_green_envoyer_factures.pdf | Supplier guide on how to send PDFs to ENGIE Green |
| FR_engie_pro_guide_facturation.pdf | 30 KB HTML, not a PDF (broken download) |
| FR_enedis_facture_hta.pdf | 986 B HTML error page (404) |
| FR_solia_catalogue_2025.pdf | Product catalog, not an invoice |
| FR_impots_fiche_facturation_electronique.pdf | Government booklet about e-invoicing reform, not an invoice |
| FR_bpifrance_facturation_electronique.pdf | BPI France reform explainer, not an invoice |
| FR_agrilocal_manuel_fournisseur.pdf | Supplier manual for Agrilocal platform |
| FR_marseille_aeroport_redevances.pdf | Marseille airport tariff guide |
| FR_facturx_basic.pdf | Lorem ipsum placeholder (used as Factur-X XML carrier) |
| FR_facturx_basicwl.pdf | Lorem ipsum placeholder |
| FR_facturx_en16931.pdf | Lorem ipsum placeholder |
| FR_facturx_extended.pdf | Lorem ipsum placeholder |
| FR_facturx_minimum.pdf | Lorem ipsum placeholder |
| FR_facturx_sample.pdf | Lorem ipsum placeholder |

---

## Summary

| | Count |
|---|---|
| Real filled invoice | 1 |
| Factur-X reference invoices (6 distinct layouts × variants) | 21 |
| Templates with sample data | 4 |
| "Comprendre votre facture" educational PDFs | 10 |
| **Total usable** | **36** |
| Quarantined (not invoices) | 15 |

**Combined with M1 dataset (16 phone photos + 5 scanned PDFs = 21):**
- **Grand total: 57 documents** → exceeds Milestone 2 Task 02 target of ≥50 ✓

**Visually-distinct invoice layouts (more honest count for training):** ~22 (1 Iberdrola + 6 Factur-X + 4 templates + ~10 utility samples + 1 Tiime).

## Licensing & ethics notes

- All PDFs were downloaded from publicly accessible URLs published by their owners (open-source repos with permissive licenses, government agencies, or companies publishing them as official customer-education material).
- No paywalled, login-required, or PII-containing real-customer invoices were collected.
- The Factur-X reference invoices from `invoice-x/factur-x-ng` and `Tiime-Software/Factur-X` use fictional company data ("Au bon moulin SARL", "LE FOURNISSEUR", etc.) — no real customer/supplier identities.
- Re-distribution of these PDFs within the project repo is consistent with the source projects' open licenses (MIT/Apache for the GitHub repos) and the customer-education purpose of the corporate PDFs.
