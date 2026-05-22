"""Build a combined M1-format ground_truth CSV for the full dataset.

Merges synthetic_ground_truth.json + real_ground_truth.json into the 11-field
CSV schema that src/metrics.py consumes. Excludes real records whose GT was an
M1 draft (`_source == m1_draft`) so the M1 extractor is not graded against its
own output (which would be circular / inflated).

Output: docs/ground_truth_full.csv  (trustworthy GT only)
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER = ["File Name", "Supplier Name", "Invoice Number", "Invoice Date", "SIRET",
          "Echeance", "Invoice Content", "TVA Percentage", "TVA Amount",
          "Total Amount", "Payment Status", "Solde du", "Notes"]


def to_row(rec):
    content = "; ".join(i.get("description", "") for i in rec.get("invoice_content", []) or [])
    tva = rec.get("tva_percentage", "")
    if isinstance(tva, list):
        tva = "; ".join(tva)
    return [
        rec["file_name"], rec.get("supplier_name", ""), rec.get("invoice_number", ""),
        rec.get("invoice_date", ""), rec.get("siret", ""), rec.get("echeance", ""),
        content, tva, rec.get("tva_amount", ""), rec.get("total_amount", ""),
        rec.get("payment_status", ""), rec.get("solde_du", ""),
        rec.get("_source", "synthetic"),
    ]


def main():
    syn = json.loads((ROOT / "docs" / "synthetic_ground_truth.json").read_text(encoding="utf-8"))
    real = json.loads((ROOT / "docs" / "real_ground_truth.json").read_text(encoding="utf-8"))

    rows = [to_row(r) for r in syn.values()]
    skipped = 0
    for r in real.values():
        if r.get("_source") in ("m1_draft", "non_invoice_guide"):
            skipped += 1
            continue
        rows.append(to_row(r))

    out = ROOT / "docs" / "ground_truth_full.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    print(f"{len(rows)} trustworthy GT rows -> {out.name} "
          f"({len(syn)} synthetic + {len(real) - skipped} real; {skipped} M1-draft excluded)")


if __name__ == "__main__":
    main()
