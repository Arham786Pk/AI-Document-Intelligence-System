# French Invoice Dataset – Inventory

**Scope:** AI French Invoice Data Extraction – Milestones 1 + 2
**Total physical files (M1 + M2 Task 02):** 73 in repo (16 M1 phone-photo JPGs + 5 M1 scanned PDFs + 52 M2 sourced-internet PDFs — all scoring ≥7/12 entities). 3 additional real-PII PDFs held locally only in `_pii_review/` (git-ignored).
**Total unique invoices (M1 ground-truth labelled):** 19
**Languages:** French only
**Sources:**
- M1: Sample invoices provided by Muhammad Ahmed (2026-05-07)
- M2 Task 02: 36 additional French invoice PDFs downloaded from public sources (2026-05-15) — see [`data/Scanned_PDF/sourced_internet/MANIFEST.md`](Scanned_PDF/sourced_internet/MANIFEST.md)

**Layout on disk:**
- `data/Images/` — 16 phone-photo JPGs (`IMG-20260507-WA0143.jpg` … `WA0158.jpg`) — M1
- `data/Scanned_PDF/` — 5 scanned PDFs (`Invoice_FR_016_scanned_*.pdf` … `Invoice_FR_020_scanned_*.pdf`) — M1
- `data/Scanned_PDF/sourced_internet/` — 52 high-quality French invoice PDFs (Factur-X reference invoices from Securibox/invoice-x/Tiime, real Iberdrola electricity bill, Chorus Pro government test invoices, EDF/ENGIE/SFR/Sigerly/Euresto "comprendre votre facture" educational PDFs) — added in M2 Task 02, all scoring ≥7/12 entities
- `data/Scanned_PDF/sourced_internet/_not_invoices/` — 15 quarantined PDFs (help guides, FAQs, broken downloads, Lorem ipsum placeholders) preserved for traceability, excluded from training
- `data/Scanned_PDF/sourced_internet/_low_quality/` — 22 quarantined PDFs that scored ≤6/12 entities (templates with placeholder data, ENGIE image-only PDFs, Chorus FSO simple test cases), excluded from training per user request

The M1 dataset is referenced by the ground-truth spreadsheet (`docs/ground_truth.csv`).
The M2 Task 02 additions will be annotated in Label Studio during Task 05.

---

## Inventory

| # | Source File | Type | Supplier | Notes |
|---|-------------|------|----------|-------|
| 1 | IMG-20260507-WA0143.jpg | Receipt photo | Aoyama (restaurant, Châtillon) | Justificatif de paiement, CB |
| 2 | IMG-20260507-WA0144.jpg | Receipt photo | Hyper Carrefour Chalon (carburant) | Visa, ticket essence |
| 3 | IMG-20260507-WA0145.jpg | Receipt photo | Orano Le Prisme (cantine) | Badge interne, "Solde" résiduel |
| 4 | IMG-20260507-WA0146.jpg | Receipt photo | Le Creusot Gare TGV (parking Effia) | Visa sans contact |
| 5 | IMG-20260507-WA0147.jpg | Receipt photo | La Boucherie Restaurant (Montchanin) | CB sans contact |
| 6 | IMG-20260507-WA0148.jpg | Invoice photo | Studio Photo Lumière & Art (Marseille) | Conditions Virement 15j |
| 7 | IMG-20260507-WA0149.jpg | Invoice photo | Clinique Dentaire Sourire (Paris) | Payé par Carte Bleue |
| 8 | IMG-20260507-WA0150.jpg | Invoice photo | Chauffage & Climatisation Roux (Grenoble) | Conditions Virement 40/60 |
| 9 | IMG-20260507-WA0151.jpg | Invoice photo | Fleuriste Jardin d'Éden (Nice) | Solde payé American Express |
| 10 | IMG-20260507-WA0152.jpg + IMG-20260507-WA0157.jpg | Invoice photo (two views) | SCA010 / FC20251175 (audit ISO) | Solde dû 4 034,46 € — duplicate photo |
| 11 | IMG-20260507-WA0153.jpg | Invoice photo | Informatique Solutions Pro (Toulouse) | Payé par Visa |
| 12 | IMG-20260507-WA0154.jpg + IMG-20260507-WA0158.jpg | Invoice photo (multi-page) | SCAI Systems / fournisseur métaux (Le Creusot) | 2 pages – Échéance 15/11/2025 |
| 13 | IMG-20260507-WA0155.jpg | Invoice photo | Fers et Métaux du Chalonnais | Conditions le 31/03/26, Virement |
| 14 | IMG-20260507-WA0156.jpg | Invoice photo | Würth Proxi Shop Le Creusot | Page 2/3 only – Conditions 30 jours |
| 15 | Invoice_FR_016_scanned_260508_103316.pdf | Scanned PDF | Épicerie Fine Marchand (Paris) | Payé par Visa |
| 16 | Invoice_FR_017_scanned_260508_103241.pdf | Scanned PDF | Atelier Couture & Retouches Blondel (Lyon) | Espèces reçues |
| 17 | Invoice_FR_018_scanned_260508_103257.pdf | Scanned PDF | Garage Mécanique Verdier (Agen) | Conditions Chèque 15j |
| 18 | Invoice_FR_019_scanned_260508_103345.pdf | Scanned PDF | École de Musique Harmonie (Lille) | Réglé par CB Mastercard |
| 19 | Invoice_FR_020_scanned_260508_103334.pdf | Scanned PDF | Paysagiste Terrain Vert (Montpellier) | Conditions Virement IBAN |

---

## Layout Variety Coverage

| Variety dimension | Coverage |
|-------------------|----------|
| Tall printer-roll receipts | 5 (WA0143–WA0147) |
| Standard A4 invoices | 9 |
| Multi-page invoices | 1 (WA0154+WA0158) |
| Tabular/grid layouts (Numéro/Date/Échéance row at top) | 2 (WA0152/WA0157, WA0156) |
| Documents with explicit "Solde dû" label | 1 (WA0152/WA0157) |
| Different TVA rates seen | 5,5 % / 10 % / 20 % / mixed 10+20 % |
| Payment-status outcomes seen | PAID / UNPAID / UNKNOWN |

This satisfies the Task 1 requirement of 15–20 varied real French invoices.
