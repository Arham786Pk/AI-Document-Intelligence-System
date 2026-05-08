# AI French Invoice Extraction

Rule-based pipeline that takes a **French invoice PDF or photo**, runs French OCR,
extracts **11 entity fields** with full synonym tolerance, detects payment
status, and writes one structured JSON per invoice.

> Repository: <https://github.com/Arham786Pk/AI-Document-Intelligence-System>
> Client: Muhammad Ahmed · Milestone 1 of 4 · 11 entities · No model training in this milestone

---

## Scope (updated 2026-05-08)

The project scope has been rewritten. Previous multi-document-type scaffolding
(fabrication sheets, welding plans, material certs, inspection reports, English
invoices) was removed. The system now works **only on French invoices** and
the entity count moved from 10 → **11** with the addition of `solde_du`.

| Old scope (removed) | New scope (active) |
|---------------------|--------------------|
| 5 document types | French invoices only |
| 10 entities | 11 entities (added `solde_du`) |
| English + French + synthetic | Real French only — 19 unique invoices |

The full task brief is `Milestone1_Simple_Final.docx` (kept locally — not committed).

---

## The 11 entities

| # | Field | Label / synonyms (short) |
|---|-------|--------------------------|
| 1 | `supplier_name` | Header / `Fournisseur` / `Société` / `Entreprise` |
| 2 | `invoice_number` | `Facture N°` / `Numéro de facture` / `Réf. Facture` |
| 3 | `invoice_date` | `Date` / `Date facture` / `Émise le` |
| 4 | `siret` | `SIRET` (14 digits) |
| 5 | `echeance` | `Échéance` / `Date limite de paiement` / `À régler avant` |
| 6 | `invoice_content` | `Désignation` / `Description` / `Prestations` (line items) |
| 7 | `tva_percentage` | Any rate — `0 %`, `5,5 %`, `10 %`, `20 %`, etc. |
| 8 | `tva_amount` | `Montant TVA` / `Total TVA` |
| 9 | `total_amount` | `Total TTC` / `Net à payer` / `Montant total` |
| 10 | `payment_status` | `PAID` / `UNPAID` / `UNKNOWN` (4-signal detector) |
| 11 | `solde_du` | `Solde dû` / `Reste à payer` / `Balance due` / `Montant restant` |

Full synonym matrix and OCR-tolerance rules: [`docs/entity_schema.md`](docs/entity_schema.md).

---

## Repository layout

```
.
├── data/
│   ├── raw/french_invoices/        ← 19 real French invoices (NOT committed)
│   │   └── MANIFEST.md             ← inventory of source files
│   └── processed/                  ← cleaned images (NOT committed)
├── docs/
│   ├── entity_schema.md            ← contract for the extractor + synonyms
│   ├── ground_truth.csv            ← labelled answer key, 19 × 11 fields
│   ├── ground_truth.xlsx           ← formatted Excel for the client
│   └── ground_truth_README.md      ← labelling rules
├── outputs/extracted/              ← one JSON per invoice (NOT committed)
├── scripts/
│   └── build_ground_truth.py       ← regenerates CSV + XLSX from labelled rows
├── src/                            ← Tasks 6–9 will populate this
├── tests/                          ← Tasks 6–9 will populate this
├── requirements.txt
└── README.md
```

`data/raw/french_invoices/` and `outputs/extracted/` are **gitignored** — see
`.gitignore`. Real client invoices stay on the local machine.

---

## Task progress

| Task | Description | Status |
|------|-------------|--------|
| 01 | Collect 15–20 French invoices (`data/raw/french_invoices/`) | ✅ Done — 19 unique invoices (5 PDFs, 16 photos collapsed to 14 unique) |
| 02 | Ground-truth spreadsheet with 11 fields | ✅ Done — `docs/ground_truth.csv` + `.xlsx` |
| 03 | Entity schema with full French synonyms | ✅ Done — `docs/entity_schema.md` |
| 04 | GitHub repository setup | ✅ Done — repo refactored to French-invoice-only |
| 05 | Python environment with French OCR | ✅ Done — `requirements.txt` + setup notes below |
| 06 | Preprocessing module (`src/preprocessor.py`) | ⬜ Pending |
| 07 | OCR text extraction in French (`src/ocr_engine.py`) | ⬜ Pending |
| 08 | Rule-based extractor for 11 fields (`src/extractor.py`) | ⬜ Pending |
| 09 | Full pipeline (`src/pipeline.py`, `src/run.py`) | ⬜ Pending |
| 10 | Metrics + summary report | ⬜ Pending |

---

## Task 5 — Environment setup

### 1. Python deps

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### 2. Tesseract + French language pack

The system **requires** Tesseract OCR with the `fra` language pack — without it,
accented characters come back as `?` or wrong glyphs and every entity except
SIRET silently fails.

**Windows**

1. Install Tesseract from <https://github.com/UB-Mannheim/tesseract/wiki>.
2. During the installer, tick **Additional language data → French (fra)**.
3. Confirm `tesseract --version` works in a fresh shell.
4. Confirm the language pack is installed:

   ```bash
   tesseract --list-langs
   ```

   `fra` must appear in the output. If it does not, download
   [`fra.traineddata`](https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata)
   into `C:\Program Files\Tesseract-OCR\tessdata\`.

**macOS**

```bash
brew install tesseract tesseract-lang
```

**Linux (Debian/Ubuntu)**

```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-fra
```

### 3. Smoke test

```bash
python -c "import pytesseract; from PIL import Image; \
  print(pytesseract.image_to_string(Image.open('data/raw/french_invoices/IMG-20260507-WA0148.jpg'), lang='fra')[:300])"
```

The output must contain accented words like `Échéance`, `règlement`,
`numériques`. If accents are wrong/missing, the `fra` pack is not installed
correctly — re-do step 2.

### 4. Optional: PaddleOCR fallback

PaddleOCR is the fallback for low-confidence Tesseract pages (Task 7). The
French model downloads on first use:

```bash
python -c "from paddleocr import PaddleOCR; PaddleOCR(lang='fr', use_angle_cls=True)"
```

---

## Quick rebuild commands

```bash
# Regenerate ground truth files
python scripts/build_ground_truth.py
```

Pipeline commands (Tasks 6–9) will be added as those modules land.
