# Entity Schema — French Invoice Extractor (Milestone 1)

This is the contract between the **Task 8 rule-based extractor** and the rest of
the pipeline. Eleven fields per invoice, accent-tolerant, accepting every
synonym variation listed below. If a synonym is missing from the regex bank,
the extractor will silently miss the field — **add it here first**.

> Output JSON shape is the same for every invoice. A missing value is the empty
> string (`""`) — never `null`, never absent. Multi-page invoices return one
> JSON, never one per page.

---

## 1. Output JSON contract

```json
{
  "file_name": "Invoice_FR_016_scanned_260508_103316.pdf",
  "supplier_name": "Epicerie Fine Marchand",
  "invoice_number": "EFM-2023-0412",
  "invoice_date": "12/11/2023",
  "siret": "12378945600178",
  "echeance": "27/11/2023",
  "invoice_content": [
    {"description": "Foie gras mi-cuit", "quantity": "6", "unit_price": "28.50"},
    {"description": "Confiture artisanale", "quantity": "12", "unit_price": "8.90"},
    {"description": "Huile d'olive AOC", "quantity": "4", "unit_price": "18.00"}
  ],
  "tva_percentage": "5.5",
  "tva_amount": "19.24",
  "total_amount": "369.04",
  "payment_status": "PAID",
  "solde_du": ""
}
```

`tva_percentage` for mixed-rate invoices is a list, e.g. `["10", "20"]`.
`payment_status` is one of `"PAID"`, `"UNPAID"`, `"UNKNOWN"`.

---

## 2. Universal OCR tolerance rules

These apply to **every** field below.

| Concern | Rule |
|---------|------|
| Accents | Patterns must match accented and non-accented forms. Build with `regex` lib using `[eéè]`, `[uû]`, `[aàâ]`, `[oô]`, `[cç]`, etc. Tesseract often drops accents on noisy scans (`Echeance` instead of `Échéance`). |
| Casing | All matches case-insensitive (`(?i)`). |
| Whitespace | Allow any run of spaces / non-breaking spaces / tabs (`\s+`) between label and value, including line breaks. |
| Punctuation between label and value | Optional `:`, `-`, `–`, `•`, `=`, or none. |
| Decimal separator | Accept both `,` and `.` (`[,.]`); normalise to `.` in output. |
| Thousand separator | Accept space, non-breaking space, or `.` (`[\s. ]?`). |
| Currency symbol | Accept `€`, `EUR`, `eur` after, before, or absent. |
| Confused glyphs | `O`/`0`, `I`/`1`/`l`, `Q`/`0`, `S`/`5`, `B`/`8` — for numeric fields, normalise digits before matching when the surrounding context guarantees a numeric token. |

---

## 3. The 11 entities

### Entity 1 — Supplier Name

| Item | Value |
|------|-------|
| Output key | `supplier_name` |
| What it is | Company that issued the invoice. |
| Trigger labels | `Fournisseur`, `Société`, `Entreprise`, `Vendor`, `Émetteur`, `Émis par`, or the **page-1 header / logo line** when no label is present. |
| Format | Free-form business name; may include `SARL`, `EURL`, `SAS`, `SA`, `SCI`. |
| Capture rule | If a labelled match exists, take the value after the label up to the line break. Otherwise take the first non-empty line of page 1 that is not the word `FACTURE`. |
| OCR notes | Drop trailing punctuation. Strip address tail when it follows on the same line (split at digit run that looks like a postal code). |
| Examples seen | `Épicerie Fine Marchand`, `Atelier Couture & Retouches Blondel`, `Garage Mécanique Verdier`, `Studio Photo Lumière & Art`, `Fleuriste Jardin d'Éden`. |

### Entity 2 — Invoice Number

| Item | Value |
|------|-------|
| Output key | `invoice_number` |
| What it is | Unique invoice reference. |
| Trigger labels | `Facture N°`, `Numéro de facture`, `N° Facture`, `No Facture`, `Réf. Facture`, `Référence`, `N° de facture`, `Numéro`. |
| Format | Alphanumeric with optional `-` / `/` / space; typically 6–20 chars. Pattern: `[A-Z0-9][A-Z0-9\-/ ]{4,20}`. |
| Capture rule | Take the token immediately after the label (after optional `:` / `°` / `N`). Stop at first whitespace longer than two spaces or end of line. |
| OCR notes | The `°` character is often dropped or misread as `o`/`0`; treat both `N°`, `No`, `N` as the same trigger. |
| Examples seen | `EFM-2023-0412`, `ACR-2023-1205`, `GMV-2023-0789`, `CCR-2024-0423`, `FC20251175`, `4330739666`. |

### Entity 3 — Invoice Date

| Item | Value |
|------|-------|
| Output key | `invoice_date` |
| What it is | Date the invoice was issued. |
| Trigger labels | `Date`, `Date facture`, `Date d'émission`, `Émise le`, `Facture le`, `Le`, `Date d'impression`, `Date de consommation`. |
| Format | `DD/MM/YYYY`, `DD/MM/YY`, `DD-MM-YYYY`, `DD.MM.YYYY`, or French long-form `DD <mois> YYYY`. |
| Capture rule | Prefer the labelled match. If none, take the first date token in the top half of the document. Ignore dates inside the `Conditions` block. |
| OCR notes | Tesseract sometimes splits the day/month with a space. French months: `janvier février mars avril mai juin juillet août septembre octobre novembre décembre` (also accept abbreviations `janv. févr. ...`). |
| Examples seen | `12/11/2023`, `28/04/2025`, `19/04/2024`, `31/03/2026`, `31/03/26`. |

### Entity 4 — SIRET

| Item | Value |
|------|-------|
| Output key | `siret` |
| What it is | French business identifier — **always 14 digits**. |
| Trigger labels | `SIRET`, `N° SIRET`, `Siret`, `Identifiant SIRET`, `Siret :`. |
| Format | `\d{3}\s?\d{3}\s?\d{3}\s?\d{5}` — exactly 14 digits, with optional single spaces grouping `3 3 3 5`. |
| Capture rule | Match strictly 14 digits. If the OCR returns 15 or 13, do **not** accept it as SIRET — flag instead. Strip internal whitespace in the output. |
| OCR notes | Distinguish from `N° TVA` (starts with `FR` + 11 digits) and from RCS / NAF codes. Beware confusion of `O`↔`0` in OCR — for SIRET treat any letter inside the 14-char window as a digit candidate. |
| Examples seen | `12378945600178`, `99956789200267`, `33390123400245`, `66623456700256`. |

### Entity 5 — Échéance

| Item | Value |
|------|-------|
| Output key | `echeance` |
| What it is | Payment due date. |
| Trigger labels | `Échéance`, `Echeance` (no accent), `Date limite de paiement`, `Date d'échéance`, `À payer avant le`, `À régler avant le`, `Due Date`, `Date d'échéance`. |
| Format | Same date formats as Entity 3. |
| Capture rule | Prefer labelled match. For `Conditions de règlement: 30 jours` (no explicit date), do **not** synthesise a date — leave empty. The exception is `À régler avant le DD/MM/YYYY` inside the conditions block, which **is** an échéance. |
| OCR notes | `Échéance` ↔ `Echeance` is the most common accent miss — pattern must accept both. |
| Examples seen | `27/11/2023`, `01/05/2024`, `28/05/2025`, `15/11/2025`, `25/12/2024`. |

### Entity 6 — Invoice Content

| Item | Value |
|------|-------|
| Output key | `invoice_content` (list of objects) |
| What it is | Line items — products, prestations, quantities, unit prices. |
| Trigger labels (column header) | `Désignation`, `Designation`, `Description`, `Prestations`, `Articles`, `Produits et Services`, `Réf. Article`, `Référence`. |
| Format | Each item is `{description, quantity, unit_price}`; quantity and unit_price are strings (because they may be empty). |
| Capture rule | Detect the line-items table by the header row (any one of the trigger labels). Walk lines downward until a totals block (`Montant HT`, `Total HT`, `TOTAL TTC`, `Sous total`) or a blank-line gap of two or more lines. For each line, take the leading description, then a numeric run for `Qté`, then the next numeric run for `P.U.`. |
| OCR notes | Bounding-box-aware reading order helps; fall back to whitespace splitting when boxes overlap. For receipts (no table grid) the line-item block lives between the header `Qté Article` / `Qté Intitulé` and a `Total` line. |
| Examples seen | `Foie gras mi-cuit`, `Détartrage complet`, `Tonte pelouse + ramassage`, `LAME SCIE D355X25,4X2,2MM 66 DTS ACIER`. |

### Entity 7 — TVA Percentage

| Item | Value |
|------|-------|
| Output key | `tva_percentage` (string or list of strings) |
| What it is | VAT rate(s) applied — **any** numeric rate, never hardcoded to 20 %. |
| Trigger labels | `TVA <num>%`, `TVA <num>,<num>%`, `Taux TVA`, `Taxe TVA`, `% TVA`, `VAT Rate`. |
| Format | Number with optional decimal (`,` or `.`), followed by `%`. Pattern: `(\d{1,2}(?:[,\.]\d{1,2})?)\s*%`. |
| Capture rule | Find every distinct rate that appears next to or in a `TVA` row. Deduplicate. If only one rate is present, return as a string; otherwise as a sorted list of strings. |
| OCR notes | The `%` is often eaten by border lines — fall back to "rate is the number on a row labelled `Taux TVA` even without `%`". The 5,5 % and 10 % rates are the most-missed cases. |
| Examples seen | `5,5`, `10`, `20`, `0`, `["10", "20"]` (mixed receipt). |

### Entity 8 — TVA Amount

| Item | Value |
|------|-------|
| Output key | `tva_amount` |
| What it is | Euro amount of VAT charged (sum across rates if mixed). |
| Trigger labels | `Montant TVA`, `TVA`, `Total TVA`, `Taxe`, `VAT Amount`, `Mt TVA`. |
| Format | Decimal money — `\d{1,3}(?:[\s .]\d{3})*(?:[,.]\d{2})?` followed by optional `EUR` / `€`. |
| Capture rule | Prefer the totals block (bottom-right). For multi-rate receipts, sum every per-rate TVA cell. |
| OCR notes | A row labelled exactly `TVA` may be either the rate (`TVA 20 %`) or the amount (`TVA : 24,00 EUR`) — disambiguate by the presence of `%` on the same line. |
| Examples seen | `19,24 EUR`, `672,41 EUR`, `78,80 EUR`, `1 309,13 EUR`. |

### Entity 9 — Total Amount

| Item | Value |
|------|-------|
| Output key | `total_amount` |
| What it is | Final total amount on the invoice. |
| Trigger labels | `Total TTC`, `Net à payer`, `NET A PAYER`, `Montant total`, `Total facture`, `Total dû`, `Total à payer`, `Montant TTC`, `TOTAL TTC en EUR`. |
| Format | Same as TVA Amount. |
| Capture rule | Prefer the row exactly equal to `Total TTC`. Otherwise fall back through the synonym list in order. **Do not** match the per-rate `Total HT` row. |
| OCR notes | `Total dû` ↔ `Total du` (without accent) is common. Avoid the `Sous total` line. |
| Examples seen | `369,04 EUR`, `4 034,46 EUR`, `2 518,81 EUR`, `7 854,77 EUR`. |

### Entity 10 — Payment Status

| Item | Value |
|------|-------|
| Output key | `payment_status` |
| Allowed values | `"PAID"` / `"UNPAID"` / `"UNKNOWN"` |

Detection runs over the **full invoice text**, in the following order. The first signal that fires wins.

| Priority | Signal | Pattern | Verdict |
|----------|--------|---------|---------|
| 1 | Card brand names | `(?i)\b(visa|mastercard|cb|carte\s*bleue|american\s*express|amex|carte\s*bancaire)\b` | `PAID` |
| 2 | French paid keywords | `(?i)\b(pay[eé]|r[eé]gl[eé]|sold[eé]\s+pay[eé])\b` | `PAID` |
| 3 | French unpaid keywords | `(?i)\b(non\s+pay[eé]|en\s+attente|impay[eé])\b` | `UNPAID` |
| 4 | "Conditions de règlement" block | `(?i)conditions\s+de\s+r[eè]glement` | extract block text into `notes`; verdict `UNKNOWN` unless overridden by 1–3 |
| Else | — | — | `UNKNOWN` |

Notes:
- "Solde" alone is not a paid signal — it must be `Soldé` / `Solde payé`. Bare `Solde` or `Solde dû` is **not** evidence of payment (see Entity 11).
- Do not treat a card brand name in the bank coordinates / IBAN block as evidence of payment — it is metadata about the supplier's bank, not a payment record. Apply Signal 1 only when the brand co-occurs with a `RÈGLEMENT` / `PAIEMENT` / `Payé par` context line.

### Entity 11 — Solde dû *(new in this milestone)*

| Item | Value |
|------|-------|
| Output key | `solde_du` |
| What it is | **Remaining outstanding balance.** Different from Total Amount: this is what is still owed *after* any deposit / partial payment. |
| Trigger labels | `Solde dû`, `Solde du`, `Reste à payer`, `Reste a payer`, `Balance due`, `Montant restant`. |
| Format | Same money pattern as Entity 8/9. |
| Capture rule | Match label → take next money token on the same or next line. Empty when none of the four labels appears, regardless of payment status. |
| Disambiguation | `Net à payer` is **Total Amount**, not Solde dû — even though they're often equal. `Solde` standalone (e.g. on cantine receipts where it means card balance) is **not** Solde dû. |
| Examples seen | `4 034,46 EUR` (one invoice in the dataset uses the explicit `Solde dû` label). |

---

## 4. Synonym master table (drop-in for the regex bank)

```python
SYNONYMS = {
    "supplier_name":  ["fournisseur", "societe", "société", "entreprise", "vendor", "emetteur", "émetteur"],
    "invoice_number": ["facture n", "numero de facture", "numéro de facture", "n facture", "no facture", "ref facture", "référence", "n° de facture", "numéro"],
    "invoice_date":   ["date facture", "date d'émission", "date d'emission", "emise le", "émise le", "facture le", "date de consommation", "date d'impression", "date :", "le "],
    "siret":          ["siret", "n siret", "n° siret", "identifiant siret"],
    "echeance":       ["échéance", "echeance", "date limite de paiement", "date d'échéance", "date d'echeance", "à payer avant", "a payer avant", "à régler avant", "a regler avant", "due date"],
    "invoice_content":["désignation", "designation", "description", "prestations", "articles", "produits et services", "ref article", "référence"],
    "tva_percentage": ["tva %", "taux tva", "taxe tva", "% tva", "vat rate"],
    "tva_amount":     ["montant tva", "total tva", "taxe", "vat amount", "mt tva"],
    "total_amount":   ["total ttc", "net a payer", "net à payer", "montant total", "total facture", "total du", "total dû", "total à payer", "montant ttc"],
    "payment_status": [],  # detection logic, not label-based
    "solde_du":       ["solde dû", "solde du", "reste à payer", "reste a payer", "balance due", "montant restant"],
}
```

The list is **closed for Milestone 1**: every example in the ground-truth
dataset is covered by these labels. Adding a new layout in Milestone 2 should
extend this table first, then the regex bank.
