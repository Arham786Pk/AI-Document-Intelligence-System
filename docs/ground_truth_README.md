# Ground Truth — French Invoices (Milestone 1)

This is the **answer key** the extraction pipeline is measured against.
Both `ground_truth.csv` and `ground_truth.xlsx` carry the same 19 rows; the
xlsx is formatted (header fill, frozen header row, wrapped cells) for the
client review and the csv is used by the evaluation script in Task 10.

## Columns (13)

The spec (Milestone1_Simple_Final) requires the 11 entity fields plus a
file-name and notes column for evaluator context:

| # | Column | Notes |
|---|--------|-------|
| 0 | File Name | Source filename in `data/Images/` (JPGs) or `data/Scanned_PDF/` (PDFs). Two filenames separated by ` + ` denote multi-page invoices or duplicate photos of the same invoice. |
| 1 | Supplier Name | Issuing company (header, logo line, or `Fournisseur` block). |
| 2 | Invoice Number | The unique reference (`Facture N°`, `N° Facture`, `Réf.`). For till receipts this is the ticket number. |
| 3 | Invoice Date | DD/MM/YYYY. |
| 4 | SIRET | 14-digit French business ID. Empty when the document does not carry one (some receipts only print TVA intracom). |
| 5 | Echeance | Payment due date (`Échéance`, `Date limite`, `À régler avant`). Empty for till receipts paid on the spot. |
| 6 | Invoice Content | Semicolon-separated list of line items copied from the `DESIGNATION`/`Description` column. |
| 7 | TVA Percentage | A single rate, or `r1; r2` for invoices that mix rates. |
| 8 | TVA Amount | Total VAT amount in euros. For mixed-rate receipts this is the sum across rates. |
| 9 | Total Amount | `Total TTC` / `Net à payer` / `Montant TTC`. |
| 10 | Payment Status | `PAID` / `UNPAID` / `UNKNOWN` per the Milestone 1 payment-detection rules. |
| 11 | Solde du | Outstanding balance (`Solde dû`, `Reste à payer`, `Balance due`, `Montant restant`). Empty when the document does not carry one of those labels. **Not** the same as Total Amount. |
| 12 | Notes | Reviewer comments — payment evidence, multi-page hints, OCR pitfalls, etc. |

## Composition (19 unique invoices)

| Slice | Count |
|-------|-------|
| Total unique invoices | 19 |
| Source: scanned PDFs | 5 |
| Source: phone-photo JPGs | 14 (16 photos, 2 collapsed because they are duplicate views or multi-page of the same invoice) |
| Status PAID | 10 |
| Status UNPAID | 1 |
| Status UNKNOWN | 8 |
| Has explicit `Solde dû` label | 1 |
| TVA rates seen | 5,5 % / 10 % / 20 % / mixed 10+20 % |

## Rules followed while labelling

1. Values copied verbatim from the document (accents stripped where the
   source itself dropped accents — this is exactly what the extractor must
   tolerate).
2. Empty cell ≠ unknown — empty means "the document does not carry this
   field". For Payment Status that case is encoded as the literal `UNKNOWN`.
3. `Solde dû` is filled only when one of the four exact labels (`Solde dû`,
   `Reste à payer`, `Balance due`, `Montant restant`) is printed on the
   invoice. `Net à payer` and `Total TTC` are mapped to **Total Amount**, not
   Solde dû.
4. Receipts with mixed VAT rates list every rate in `TVA Percentage`
   separated by `;` and use the receipt's own VAT total as `TVA Amount`.
5. Multi-page or duplicate-photo invoices are one row, with both source
   filenames in the `File Name` cell.

## How to regenerate

```bash
python scripts/build_ground_truth.py
```

Edits the row data in that script to keep CSV and XLSX in sync.
