# Entity Schema — Milestone 1

Patterns observed across the 20 primary documents (see
[`ground_truth.csv`](ground_truth.csv)) plus the held-out real-filled
certs (NST, La Robinetterie, Dillinger, Sandvik). These patterns feed
directly into `src/extractor.py` (Task 8).

Both English and French trigger words are listed because the corpus is
bilingual. Every regex is case-insensitive and tolerant of 0–2 spaces
around separators (`:` / `=` / newline).

---

## 1. Project ID

**Definition:** Unique code that identifies the job, work order, purchase
order, certificate, or welding procedure associated with the document.
One document normally has exactly one project-level ID (plus secondary
IDs like heat / lot / cast numbers, which we capture as material
sub-fields, not project ID).

**Format / pattern:**
- **Synthetic & common operational form:** `<PREFIX>-<DIGITS>`, e.g.
  `PRJ-1234`, `WO-5678`, `JOB-2658`, `WLD-15592`, `FAB-73255`,
  `PO-1053`. Prefix is 2–4 uppercase letters, followed by `-` and 2–6
  digits.
- **Certificate number (EN 10204):** 5–9 digits, sometimes with a
  prefix like `EXP`, e.g. `134822`, `59003730`, `EXP1390198`.
- **WPS / procedure number:** `<LETTERS>-<DIGITS>[-<REV>]`, e.g.
  `SS-011`, `WPS-2023-04-R1`.

**Regex (first-pass):**
```regex
(?i)\b(?:PRJ|PROJ|WO|JOB|WLD|FAB|PO|WPS|CERT|REF)[-_ ]?\d{2,7}(?:[-_ ]?R\d+)?\b
|\b(?:EXP|CERT)\s*\d{5,9}\b
|(?<=(?:certificat|certificate|certif\.)\s*(?:n°|no\.?|number|nb|#)\s*:?\s*)\d{5,9}
```

**Trigger words (EN):** `Project`, `Project ID`, `Work Order`,
`WO #`, `Purchase Order`, `PO #`, `Job Number`, `Identification #`,
`Report No.`, `Certificate No.`, `Cert No.`, `WPS:`, `WPS No`,
`Reference`, `Ref`.

**Trigger words (FR):** `Numéro de certificat`, `N° certificat`,
`N° commande`, `N° de commande`, `Référence`, `Réf.`, `N° facture`,
`Numéro de facture`, `N° de rapport`, `Bon de commande`.

**Real examples from docs:**
| Value          | Source                                                    | Trigger on page              |
|----------------|-----------------------------------------------------------|------------------------------|
| `134822`       | `Real_MaterialCert_FR_Larobinetterie_134822.pdf`          | `Numéro de certificat : 134822` |
| `59003730`     | `Real_MaterialCert_FR_Antelis_Dillinger_32.pdf`           | `No. Certificat 59003730`    |
| `736145`       | `Real_MaterialCert_FR_Larobinetterie_160629.pdf`          | `Cert N° 736145`             |
| `409707-001`   | `Real_MaterialCert_FR_Dillinger_Antelis.pdf`              | `A03 No. Certificat 409707-001` |
| `00CD5528`     | `Real_WeldingPlan_FR_Cahier_Soudage_Filtres.pdf`          | `N° Commande / Order n° : 00CD5528` |
| `WO-98154`     | `Synthetic_WeldingPlan_FR_01.pdf`                         | `N° commande : WO-98154`     |
| `PO-39290`     | `Synthetic_MaterialCert_FR_01.pdf`                        | `N° Projet: PO-39290`        |

---

## 2. Supplier Name

**Definition:** Company or organisation that issued the document — the
material manufacturer, welding contractor, inspection body, or seller on
an invoice. **Not** the customer / buyer / consignee.

**Format / pattern:** Free text. Typically 2–6 words. Common corporate
suffixes: `Ltd`, `Ltd.`, `LLC`, `Inc.`, `Group`, `Co.`, `Corp.`,
`GmbH`, `AG`, `SA`, `SARL`, `S.A.S.`, `SAS`, `Aciéries`, `Steel Mills`.

**Regex (first-pass):** Too variable for a single regex — preferred
approach is trigger-word anchor + "capture next non-empty line
containing a corporate suffix".

```regex
(?im)^(?:supplier|vendor|from|seller|issued\ by|manufacturer|fournisseur|émis\ par|fabricant)\s*[:\-]\s*(.+)$
```
Fallback: NER-style detection on the document header block (top 20% of
page 1) combined with the corporate-suffix whitelist.

**Trigger words (EN):** `Supplier:`, `Vendor:`, `From:`, `Seller:`,
`Issued by:`, `Manufacturer:`, `Shipped from:`, `Ship from:`,
`Produced by:`.

**Trigger words (FR):** `Fournisseur :`, `Émis par :`, `Émetteur :`,
`Fabricant :`, `Producteur :`, `De :`.

**Real examples from docs:**
| Value                                  | Source                                            |
|----------------------------------------|---------------------------------------------------|
| `La Robinetterie (LRI-Sodime)`         | `Real_MaterialCert_FR_Larobinetterie_134822.pdf`  |
| `AG der Dillinger Hüttenwerke`         | `Real_MaterialCert_FR_Antelis_Dillinger_32.pdf`   |
| `SIDERINOX`                            | `Real_MaterialCert_FR_Larobinetterie_160629.pdf`  |
| `Ugitech SA`                           | `Real_MaterialCert_FR_Ugitech_Alim.pdf`           |
| `CFCE` (manufacturer)                  | `Real_WeldingPlan_FR_Cahier_Soudage_Filtres.pdf`  |
| `Bazin et Fils`                        | `Synthetic_WeldingPlan_FR_01.pdf`                 |
| `Moreau SARL`                          | `Synthetic_Invoice_FR_01.pdf`                     |
| `Aubry Aciéries`                       | `Synthetic_MaterialCert_FR_01.pdf`                |

**Edge cases to handle:**
- Customer address block often appears near supplier — extractor must
  not pick the customer name (e.g. `ANTELIS, LEUDELANGE` on Dillinger
  certs) as the supplier. Solution: prefer the company name in the
  document letterhead / top-left, or the one following `Issued by` / `Émis par`.
- Template documents (blank forms) have placeholder text like `Company
  Name` — extractor must return empty, not `Company Name`.

---

## 3. Material Type

**Definition:** The steel, alloy, polymer, or other material grade
being certified, welded, fabricated, or shipped. Often a standards
code (e.g. `SS 316`, `EN 1.4307`, `A106 Gr.B`) rather than plain text.

**Format / pattern:** Mix of:
- **Grade codes:** `SS 316`, `SS 316L`, `304L`, `1.4307`,
  `S355G10+N`, `A36`, `A106 Gr.B`, `6061-T6`, `C110`, `C-276`.
- **Plain-text descriptors:** `Carbon Steel`, `Stainless Steel`,
  `Aluminium 6061-T6`, `Duplex 2205`, `Monel 400`, `Hastelloy C-276`,
  `PVC Sch 80`, `Galvanized Steel`, `Copper C110`.
- **AWS / ISO filler codes:** `AWS A5.9 ER316LSi`,
  `E71T-1 M H4`.

**Regex (first-pass):**
```regex
(?ix)
  # Common grade codes
  \b(?:SS\s?\d{3}L?|304L|316L?|\d\.\d{4}|S\d{3}[A-Z0-9\+]+|A\d{1,3}(?:\s*Gr\.?\s*[A-Z])?|6061-T6|2205|C[-_]?276|C110)\b
  |
  # Named alloys
  \b(?:Carbon\s+Steel|Stainless\s+Steel|Duplex|Monel|Hastelloy|Inconel|Titanium|Aluminium|Aluminum|Copper|PVC\s+Sch\s*\d+|Galvanized\s+Steel)\b[^\n]*
  |
  # AWS classifications
  \bAWS\s+A\d\.\d+\s+[A-Z0-9-]+\b
```

**Trigger words (EN):** `Material:`, `Material Type:`, `Material Spec`,
`Base Material:`, `Grade:`, `Commodity:`, `Description:`,
`Filler Metal:`, `Steel:`.

**Trigger words (FR):** `Matière :`, `Matériau :`, `Type de matériau`,
`Désignation du matériau`, `Désignation`, `Nuance`,
`Désign. acier`, `Métal de base`.

**Real examples from docs:**
| Value                            | Source                                                |
|----------------------------------|-------------------------------------------------------|
| `1.4307 / 304L`                  | `Real_MaterialCert_FR_Larobinetterie_134822.pdf`      |
| `S355G10+N`                      | `Real_MaterialCert_FR_Antelis_Dillinger_32.pdf`       |
| `AISI 304/304L (EN 1.4301/1.4307)` | `Real_MaterialCert_FR_Larobinetterie_160629.pdf`    |
| `S355K2+N`                       | `Real_MaterialCert_FR_Dillinger_Antelis.pdf`          |
| `Acier inoxydable / alliage`     | `Real_MaterialCert_FR_Ugitech_Alim.pdf`               |
| `P355 NL1 / API 5L X52`          | `Real_WeldingPlan_FR_Cahier_Soudage_Filtres.pdf`      |
| `Monel 400`                      | `Synthetic_MaterialCert_FR_01.pdf`                    |
| `PVC Sch 80`                     | `Synthetic_WeldingPlan_FR_01.pdf`                     |
| `Aluminium 6061-T6`              | `Synthetic_InspectionReport_FR_01.pdf`                |

**Edge cases to handle:**
- Multiple materials on one doc (filler + base metal): capture both,
  concatenate with ` / `.
- French documents use "1.4307" style (European steel-number), English
  use "304L" style — extractor should treat both as synonyms.

---

## 4. Quantity

**Definition:** The amount of material or number of items referenced
by the document. Always a number + a unit.

**Format / pattern:** `<number>\s*<unit>`
- **Numbers:** integer or decimal, e.g. `400`, `15642`, `123.32`,
  `53.73`.
- **Units:** `pcs`, `pieces`, `units`, `kg`, `KG`, `Kgs`, `lbs`, `tons`,
  `m`, `mm`, `metres`, `pieza`.

**Regex (first-pass):**
```regex
(?i)\b\d{1,6}(?:[.,]\d{1,3})?\s*(?:pcs|pieces|units|kg|kgs|lbs|tons|tonnes|metres?|mm|m)\b
```

**Trigger words (EN):** `Quantity:`, `Qty:`, `Weight:`, `Total Weight:`,
`Gross Weight:`, `Net Weight:`, `Amount:`, `Total:`.

**Trigger words (FR):** `Quantité :`, `Qté :`, `Poids :`, `Poids net :`,
`Poids total :`, `Masse :`, `Masse théorique :`, `Masse effective :`,
`Nombre :`, `Unités :`.

**Real examples from docs:**
| Value          | Source                                            |
|----------------|---------------------------------------------------|
| `15642 KG`     | `Real_MaterialCert_FR_Antelis_Dillinger_32.pdf` — `Masse théorique 15642 KG` |
| `25434 KG`     | `Real_MaterialCert_FR_Dillinger_Antelis.pdf`      |
| `312 m`        | `Real_MaterialCert_FR_Larobinetterie_160629.pdf`  |
| `38 mm`        | `Real_MaterialCert_FR_Larobinetterie_134822.pdf`  |
| `287 pcs`      | `Synthetic_WeldingPlan_FR_01.pdf`                 |
| `381 tons`     | `Synthetic_Invoice_FR_01.pdf`                     |
| `149.58 lbs`   | `Synthetic_FabricationSheet_FR_01.pdf`            |
| `220.39 pcs`   | `Synthetic_InspectionReport_FR_01.pdf`            |

**Edge cases to handle:**
- European number format uses `,` as decimal (e.g. `15,642` in some FR
  docs); the regex should accept both separators.
- Some docs have multiple quantities (gross / net / line-item):
  prefer the one near the `Total` / `Quantity` trigger, or fall back to
  the largest value.
- WPS / procedure documents often have no quantity — return empty, do
  not hallucinate.

---

## 5. Date

**Definition:** A date referenced by the document — issue date,
inspection date, certificate date, invoice date, or welding-procedure
effective date. Documents may have 2–5 dates; prefer the "headline" date
(adjacent to `Date:` / `Issue Date:` / `Date d'émission:` trigger).

**Format / pattern:** Four common formats observed:
- **ISO:** `YYYY-MM-DD`, e.g. `2025-10-12`, `2013-11-05`.
- **European slash:** `DD/MM/YYYY`, e.g. `23/05/2019`, `18/03/2024`.
- **European dot:** `DD.MM.YYYY` or `DD.MM.YY`, e.g. `23.05.2019`,
  `26.09.18`.
- **English short:** `DD/MM/YY` or `MMM DD, YYYY`, e.g. `18/05/23`,
  `Aug 12, 2025`, `Mar 29, 2025`.

**Regex (first-pass):**
```regex
(?ix)
  \b(?:\d{4}-\d{2}-\d{2})\b                                  # ISO
  |\b(?:\d{1,2}[/.]\d{1,2}[/.]\d{2,4})\b                     # DD/MM/YYYY or DD.MM.YY
  |\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b  # Mar 29, 2025
  |\b\d{1,2}\s+(?:janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)[a-zé]*\s+\d{2,4}\b  # FR textual
```

**Trigger words (EN):** `Date:`, `Issue Date:`, `Invoice Date:`,
`Date of Sale:`, `Effective:`, `Mfg. Date:`, `Shipped:`, `Report Date:`.

**Trigger words (FR):** `Date :`, `Date d'émission :`, `Date d'expédition`,
`Date de facture :`, `Date d'essai`, `Date de fabrication :`.

**Real examples from docs:**
| Value (normalised) | Raw form in doc | Source                                    |
|--------------------|-----------------|-------------------------------------------|
| `2019-05-23`       | `23.05.2019`    | `Real_MaterialCert_FR_Larobinetterie_134822.pdf` |
| `2018-09-26`       | `26.09.18`      | `Real_MaterialCert_FR_Antelis_Dillinger_32.pdf` |
| `2024-06-26`       | `26.06.2024`    | `Real_MaterialCert_FR_Larobinetterie_160629.pdf` |
| `2015-11-26`       | `26.11.15`      | `Real_MaterialCert_FR_Dillinger_Antelis.pdf` |
| `2023-11-03`       | `03/11/2023`    | `Real_MaterialCert_FR_Ugitech_Alim.pdf`   |
| `1998-04-21`       | `21/04/98`      | `Real_WeldingPlan_FR_Cahier_Soudage_Filtres.pdf` |
| `2024-03-18`       | `18/03/2024`    | `Synthetic_WeldingPlan_FR_01.pdf`         |
| `2024-08-12`       | `12/08/2024`    | `Synthetic_Invoice_FR_01.pdf`             |

**Edge cases to handle:**
- `DD/MM/YY` vs `MM/DD/YY` ambiguity for `06/05/23` (could be 6 May or
  5 June). Resolution: prefer `DD/MM/YY` for FR docs, `MM/DD/YY` for EN
  only if `month > 12` disambiguates — otherwise flag in notes.
- Two-digit year: treat `00–49` as `20XX`, `50–99` as `19XX`.
- Normalise all extracted dates to ISO `YYYY-MM-DD` in the JSON output
  (Task 9) regardless of source format.

---

## Summary cheatsheet (for Task 8 implementation)

| Entity      | Primary anchor trigger (EN / FR)         | Best-shot regex key          | Normalise to           |
|-------------|------------------------------------------|------------------------------|------------------------|
| Project ID  | `Project` / `N° commande` / `WPS`        | `prefix-digits` code         | uppercase, no spaces   |
| Supplier    | `Supplier` / `Fournisseur` / letterhead  | line-after-trigger + suffix  | trim, collapse spaces  |
| Material    | `Material` / `Désignation du matériau`   | grade-code whitelist         | keep as written        |
| Quantity    | `Qty` / `Quantité` / `Weight` / `Poids`  | `number + unit`              | keep as written        |
| Date        | `Date` / `Issue Date` / `Date facture`   | 4-format alternation         | ISO `YYYY-MM-DD`       |

Schema reviewed against the 20 FR documents in the primary ground-truth
set (6 real-filled + 10 synthetic digital + 4 synthetic scanned). EN
trigger words and regex patterns are retained because the held-out
corpus in `data/raw/extra/` still contains EN documents that the rule-
based extractor (Task 8) must generalise to. When Task 8 starts, any
miss or false positive observed during testing is added as a new edge-
case row under the relevant entity section — this file is a living
document through Milestone 1.
