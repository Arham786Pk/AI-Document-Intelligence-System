"""Task 05 — Build completed annotations for every document.

Strategy (honest about quality):
  * Synthetic docs (we hold exact ground truth in docs/synthetic_ground_truth.json)
    -> labels located from the TRUE values = correct. Any field garbled by image
       OCR falls back to the M1 prediction span so no label is lost.
  * Real docs (no ground truth exists) -> the validated M1 auto-labels are
    accepted as the annotation (best an automated process can do).

Reads the per-task text + M1 predictions already produced by
build_preannotations.py, so offsets are guaranteed to match the task text.

Output (Label Studio import format with `annotations`):
  label_studio/annotations_pdf.json     (100 completed tasks)
  label_studio/annotations_images.json  (100 completed tasks)
"""

import json
import re
from pathlib import Path

from build_preannotations import (  # same folder
    find_consumer, find_date, find_money, find_plain, find_status, span,
)

ROOT = Path(__file__).resolve().parents[1]
LS = ROOT / "label_studio"
GT_PATH = ROOT / "docs" / "synthetic_ground_truth.json"

SKIP_DESC = {"quantité", "quantite", "désignation", "designation",
             "prix unitaire", "sous-total ht", "total ttc"}


def dedupe(results):
    seen, out = set(), []
    for r in results:
        v = r["value"]
        key = (v["start"], v["end"], v["labels"][0])
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def gt_spans(text: str, gt: dict) -> list:
    low = text.lower()
    res = []

    def add(loc, label):
        if loc:
            res.append(span(loc[0], loc[1], text, label))

    add(find_plain(gt.get("supplier_name", ""), text, low), "SUPPLIER_NAME")
    add(find_plain(gt.get("consumer_name", ""), text, low), "CONSUMER_NAME")
    add(find_plain(gt.get("invoice_number", ""), text, low), "INVOICE_NUMBER")
    add(find_plain(gt.get("siret", ""), text, low), "SIRET")
    add(find_date(gt.get("invoice_date", ""), text), "INVOICE_DATE")
    add(find_date(gt.get("echeance", ""), text), "ECHEANCE")
    add(find_money(gt.get("tva_amount", ""), text), "TVA_AMOUNT")
    add(find_money(gt.get("total_amount", ""), text), "TOTAL_AMOUNT")
    if gt.get("solde_du"):
        add(find_money(gt["solde_du"], text), "SOLDE_DU")
    add(find_status(gt.get("payment_status", ""), text), "PAYMENT_STATUS")

    tva = gt.get("tva_percentage", "")
    for v in (tva if isinstance(tva, list) else [tva]):
        if v:
            m = re.search(re.escape(v) + r"\s*%", text)
            add((m.start(), m.start() + len(v)) if m else None, "TVA_PERCENTAGE")

    for it in gt.get("invoice_content", []) or []:
        desc = it.get("description", "").strip()
        if len(desc) >= 4 and any(c.isalpha() for c in desc) and desc.lower() not in SKIP_DESC:
            add(find_plain(desc, text, low), "INVOICE_CONTENT")

    return dedupe(res)


def merge_missing(primary: list, fallback: list) -> list:
    """Add fallback spans for any LABEL not represented in primary."""
    have = {r["value"]["labels"][0] for r in primary}
    extra = [r for r in fallback if r["value"]["labels"][0] not in have]
    return dedupe(primary + extra)


def main():
    gt = json.loads(GT_PATH.read_text(encoding="utf-8"))
    gt_by_stem = {Path(k).stem: v for k, v in gt.items()}
    # also use the verified real-doc ground truth (Task 05 complete)
    real_path = ROOT / "docs" / "real_ground_truth.json"
    if real_path.exists():
        real = json.loads(real_path.read_text(encoding="utf-8"))
        for k, v in real.items():
            gt_by_stem[Path(k).stem] = v

    for src, out in (("preannotations_pdf.json", "annotations_pdf.json"),
                     ("preannotations_images.json", "annotations_images.json")):
        tasks = json.loads((LS / src).read_text(encoding="utf-8"))
        out_tasks, n_synth, n_real = [], 0, 0
        for t in tasks:
            text = t["data"]["text"]
            stem = t["data"]["document"]
            pred = t["predictions"][0]["result"]
            if stem in gt_by_stem:
                results = merge_missing(gt_spans(text, gt_by_stem[stem]), pred)
                n_synth += 1
            else:
                results = pred
                n_real += 1
            out_tasks.append({
                "data": t["data"],
                "annotations": [{"result": results}],
            })
        (LS / out).write_text(json.dumps(out_tasks, ensure_ascii=False, indent=2),
                              encoding="utf-8")
        spans = sum(len(x["annotations"][0]["result"]) for x in out_tasks)
        print(f"-> {out}: {len(out_tasks)} tasks "
              f"({n_synth} synthetic/ground-truth, {n_real} real/M1), {spans} labels")


if __name__ == "__main__":
    main()
