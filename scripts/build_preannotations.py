"""Task 04 — Pre-annotate all documents with the Milestone-1 rule-based pipeline.

For every PDF in data/pdf and image in data/images:
  1. get text  (PyMuPDF for digital PDFs; Tesseract OCR fallback for scans/images)
  2. run the M1 rule-based extractor (extract_entities) + a consumer_name heuristic
  3. locate each entity value in the text and emit a Label Studio NER span
  4. write a Label Studio import file with `predictions` (auto-labels)

Output:
  label_studio/preannotations_pdf.json     (100 tasks)
  label_studio/preannotations_images.json  (100 tasks)

Import these into the Label Studio project (Import button). Person 1 then
reviews/fixes the auto-labels (Task 05) instead of labelling from scratch.
"""

import json
import re
import sys
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.extractor import extract_entities  # noqa: E402

PDF_DIR = ROOT / "data" / "pdf"
IMG_DIR = ROOT / "data" / "images"
OUT_DIR = ROOT / "label_studio"

KEY2LABEL = {
    "supplier_name": "SUPPLIER_NAME",
    "consumer_name": "CONSUMER_NAME",
    "invoice_number": "INVOICE_NUMBER",
    "invoice_date": "INVOICE_DATE",
    "siret": "SIRET",
    "echeance": "ECHEANCE",
    "tva_percentage": "TVA_PERCENTAGE",
    "tva_amount": "TVA_AMOUNT",
    "total_amount": "TOTAL_AMOUNT",
    "payment_status": "PAYMENT_STATUS",
    "solde_du": "SOLDE_DU",
}

CONSUMER_LABELS = ["destinataire", "facturé à", "facture a", "facturer a",
                   "client", "acheteur", "pour le compte de", "à l'attention de"]
PAID_WORDS = ["payé", "paye", "réglé", "regle", "acquitté", "acquittee"]
UNPAID_WORDS = ["non payé", "non paye", "impayé", "impaye", "reste à payer", "à régler"]


# ----------------------------- text extraction -----------------------------

def get_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        doc = fitz.open(str(path))
        digital = "".join(pg.get_text() for pg in doc)
        if len(digital.strip()) > 40:
            doc.close()
            return digital
        # image-only PDF -> OCR each page
        parts = []
        for pg in doc:
            pix = pg.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            parts.append(pytesseract.image_to_string(img, lang="fra+eng"))
        doc.close()
        return "\n".join(parts)
    # raster image
    return pytesseract.image_to_string(Image.open(path), lang="fra+eng")


# ----------------------------- span locating --------------------------------

def find_plain(value: str, text: str, lo: str):
    if not value:
        return None
    i = lo.find(value.lower())
    return (i, i + len(value)) if i >= 0 else None


def find_money(value: str, text: str):
    if "." in value:
        intp, dec = value.split(".", 1)
    else:
        intp, dec = value, None
    body = r"[\s .,]?".join(re.escape(d) for d in intp)
    if dec is not None:
        body += r"[.,]" + re.escape(dec)
    m = re.search(body, text)
    return (m.start(), m.end()) if m else None


def find_date(value: str, text: str):
    parts = re.split(r"[^0-9]+", value)
    parts = [p for p in parts if p]
    if len(parts) < 3:
        return find_plain(value, text, text.lower())
    pat = r"[/\-.\s]".join(re.escape(p) for p in parts)
    m = re.search(pat, text)
    return (m.start(), m.end()) if m else None


def find_consumer(text: str):
    lines = text.splitlines()
    low = [ln.lower() for ln in lines]
    for i, ln in enumerate(low):
        for lab in CONSUMER_LABELS:
            if lab in ln:
                # value after the label on same line, else next non-empty line
                after = lines[i][low[i].find(lab) + len(lab):].strip(" :=-")
                if len(after) > 1:
                    val = after.split("  ")[0].strip()
                else:
                    val = next((lines[j].strip() for j in range(i + 1, min(i + 3, len(lines)))
                                if lines[j].strip()), "")
                if val:
                    idx = text.find(val)
                    if idx >= 0:
                        return val, (idx, idx + len(val))
    return "", None


def find_status(value: str, text: str):
    low = text.lower()
    if value == "UNPAID":
        for w in UNPAID_WORDS:
            i = low.find(w)
            if i >= 0:
                return (i, i + len(w))
    elif value == "PAID":
        # avoid matching the "payé" inside "non payé"
        for m in re.finditer(r"pay[ée]|réglé|regle|acquitt[ée]e?", low):
            if not low[max(0, m.start() - 4):m.start()].endswith("non "):
                return (m.start(), m.end())
    return None


def span(start, end, text, label):
    return {
        "from_name": "label", "to_name": "text", "type": "labels",
        "value": {"start": start, "end": end, "text": text[start:end], "labels": [label]},
    }


# ----------------------------- per-document ---------------------------------

def build_results(text: str, ent: dict) -> list:
    low = text.lower()
    results = []

    def add(loc, label):
        if loc:
            results.append(span(loc[0], loc[1], text, label))

    add(find_plain(ent.get("supplier_name", ""), text, low), "SUPPLIER_NAME")
    add(find_plain(ent.get("invoice_number", ""), text, low), "INVOICE_NUMBER")
    add(find_plain(ent.get("siret", ""), text, low), "SIRET")
    add(find_date(ent.get("invoice_date", ""), text), "INVOICE_DATE")
    add(find_date(ent.get("echeance", ""), text), "ECHEANCE")
    add(find_money(ent.get("tva_amount", ""), text), "TVA_AMOUNT")
    add(find_money(ent.get("total_amount", ""), text), "TOTAL_AMOUNT")
    add(find_money(ent.get("solde_du", ""), text), "SOLDE_DU")
    add(find_status(ent.get("payment_status", ""), text), "PAYMENT_STATUS")

    tva = ent.get("tva_percentage", "")
    for v in (tva if isinstance(tva, list) else [tva]):
        if v:
            m = re.search(re.escape(v) + r"\s*%", text)
            add((m.start(), m.start() + len(v)) if m else None, "TVA_PERCENTAGE")

    for item in ent.get("invoice_content", []) or []:
        desc = item.get("description", "").strip()
        # skip junk: table headers, symbol-only or too-short fragments
        if len(desc) < 4 or not any(c.isalpha() for c in desc):
            continue
        if desc.lower() in {"quantité", "quantite", "désignation", "designation",
                             "prix unitaire", "sous-total ht", "total ttc"}:
            continue
        add(find_plain(desc, text, low), "INVOICE_CONTENT")

    _, cloc = find_consumer(text)
    add(cloc, "CONSUMER_NAME")

    # dedupe identical (start, end, label) spans
    seen, unique = set(), []
    for r in results:
        v = r["value"]
        key = (v["start"], v["end"], v["labels"][0])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def process(paths, source) -> list:
    tasks = []
    for p in paths:
        try:
            text = get_text(p)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {p.name}: text extraction failed ({exc})")
            text = ""
        ent = extract_entities(text, p.stem)
        results = build_results(text, ent) if text.strip() else []
        tasks.append({
            "data": {"text": text, "document": p.stem, "source": source},
            "predictions": [{"model_version": "m1-rule-based", "result": results}],
        })
        print(f"  {p.name}: {len(results)} auto-labels")
    return tasks


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for label, directory, pattern, source in (
        ("preannotations_pdf.json", PDF_DIR, "*.pdf", "pdf"),
        ("preannotations_images.json", IMG_DIR, "*", "image"),
    ):
        files = sorted(p for p in directory.glob(pattern) if p.is_file())
        print(f"== {source}: {len(files)} files ==")
        tasks = process(files, source)
        (OUT_DIR / label).write_text(
            json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
        with_labels = sum(1 for t in tasks if t["predictions"][0]["result"])
        total_spans = sum(len(t["predictions"][0]["result"]) for t in tasks)
        print(f"-> {label}: {len(tasks)} tasks, {with_labels} with pre-labels, "
              f"{total_spans} spans total\n")


if __name__ == "__main__":
    main()
