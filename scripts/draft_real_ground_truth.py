"""Create a DRAFT ground-truth file for the 116 real documents.

Draft sources (in priority order, best first):
  1. docs/ground_truth.csv  -> 17 docs hand-labelled in Task 2 (most trusted)
  2. M1 rule-based extractor -> everything else (to be corrected by reading)

The draft is then reviewed document-by-document and corrected in place.
Output: docs/real_ground_truth.json  (keyed by new filename, 12-entity schema)
"""

import csv
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src.extractor import extract_entities  # noqa: E402
from build_preannotations import get_text, find_consumer  # noqa: E402

PDF_DIR = ROOT / "data" / "pdf"
IMG_DIR = ROOT / "data" / "images"
OUT = ROOT / "docs" / "real_ground_truth.json"

ENTITY_KEYS = ["supplier_name", "invoice_number", "invoice_date", "siret",
               "echeance", "invoice_content", "tva_percentage", "tva_amount",
               "total_amount", "payment_status", "solde_du", "consumer_name"]


def manifest_map(path):
    m = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if r["type"] == "real":
            m[Path(r["original_path"]).name] = r["filename"]
    return m


def csv_to_record(row, fname):
    def money(s):
        s = re.sub(r"[^0-9,.\-]", "", s or "").replace(" ", "")
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", ".")
        return s
    pct = re.findall(r"\d+(?:[.,]\d+)?", row.get("TVA Percentage", "") or "")
    return {
        "file_name": fname,
        "supplier_name": row.get("Supplier Name", "").strip(),
        "invoice_number": row.get("Invoice Number", "").strip(),
        "invoice_date": row.get("Invoice Date", "").strip(),
        "siret": re.sub(r"\D", "", row.get("SIRET", "") or ""),
        "echeance": row.get("Echeance", "").strip(),
        "invoice_content": ([{"description": row.get("Invoice Content", "").strip(),
                              "quantity": "", "unit_price": ""}]
                            if row.get("Invoice Content", "").strip() else []),
        "tva_percentage": (pct[0] if len(pct) == 1 else pct) if pct else "",
        "tva_amount": money(row.get("TVA Amount", "")),
        "total_amount": money(row.get("Total Amount", "")),
        "payment_status": (row.get("Payment Status", "").strip().upper() or "UNKNOWN"),
        "solde_du": money(row.get("Solde du", "")),
        "consumer_name": "",   # not captured in Task 2 — fill on review
        "_source": "task2_csv",
        "_notes": row.get("Notes", "").strip(),
    }


def m1_record(path, fname):
    text = ""
    try:
        text = get_text(path)
    except Exception:
        pass
    ent = extract_entities(text, fname)
    cons, _ = find_consumer(text) if text else ("", None)
    rec = {"file_name": fname}
    for k in ENTITY_KEYS:
        rec[k] = ent.get(k, "") if k != "consumer_name" else cons
    rec["_source"] = "m1_draft"
    rec["_text_excerpt"] = text[:600]
    return rec


def main():
    pdf_map = manifest_map(ROOT / "data" / "pdf_manifest.csv")
    img_map = manifest_map(ROOT / "data" / "images_manifest.csv")
    orig2new = {**pdf_map, **img_map}

    csv_rows = {r["File Name"]: r for r in csv.DictReader(
        open(ROOT / "docs" / "ground_truth.csv", encoding="utf-8"))}

    out = {}
    # 1) trusted Task-2 rows
    used_csv = 0
    for orig, row in csv_rows.items():
        new = orig2new.get(orig)
        if new:
            out[new] = csv_to_record(row, new)
            used_csv += 1

    # 2) M1 draft for the rest
    real_files = (sorted(PDF_DIR.glob("FR_invoice_real_*.pdf"))
                  + sorted(p for p in IMG_DIR.glob("FR_invoice_img_real_*")))
    m1 = 0
    for p in real_files:
        if p.name not in out:
            out[p.name] = m1_record(p, p.name)
            m1 += 1

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(out)} real records -> {OUT.name} ({used_csv} from Task-2 CSV, {m1} M1 draft)")


if __name__ == "__main__":
    main()
