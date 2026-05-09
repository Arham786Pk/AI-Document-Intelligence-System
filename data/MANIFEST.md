# French Invoice Dataset – Task 1 Inventory

**Scope:** AI French Invoice Data Extraction – Milestone 1
**Total physical files:** 21 (5 scanned PDFs + 16 phone-photo JPGs)
**Total unique invoices:** 19 (some images are extra views or extra pages of the same invoice)
**Languages:** French only
**Source:** Sample invoices provided by Muhammad Ahmed (2026-05-07)
**Layout on disk:**
- `data/Images/` — 16 phone-photo JPGs (`IMG-20260507-WA0143.jpg` … `WA0158.jpg`)
- `data/Scanned_PDF/` — 5 scanned PDFs (`Invoice_FR_016_scanned_*.pdf` … `Invoice_FR_020_scanned_*.pdf`)

The full dataset is committed to the repository for reproducibility and is
referenced by the ground-truth spreadsheet (`docs/ground_truth.csv`).

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
