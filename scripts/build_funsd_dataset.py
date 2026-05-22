"""Task 07 — Export the labelled dataset in LayoutLMv3 / FUNSD token-classification
format and split 70/15/15 into train / validation / test.

For each of the 200 documents:
  1. Render to image (PDF page 1 or the raster image) and run word-level OCR
     (pytesseract image_to_data) -> words + bounding boxes.
  2. Normalise boxes to the 0-1000 LayoutLM coordinate space.
  3. Assign BIO tags by matching each ground-truth entity value to a contiguous
     run of OCR words.
  4. Emit one record per doc: {id, tokens, bboxes, ner_tags, labels, image}.

Split is by document (no document appears in more than one split).

Outputs under data/funsd/:
  train.jsonl, val.jsonl, test.jsonl, labels.txt, dataset_summary.json
Ground truth: synthetic_ground_truth.json + real_ground_truth.json
"""

import json
import random
import re
import sys
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PDF_DIR = ROOT / "data" / "pdf"
IMG_DIR = ROOT / "data" / "images"
OUT = ROOT / "data" / "funsd"

ENTITIES = ["SUPPLIER_NAME", "CONSUMER_NAME", "INVOICE_NUMBER", "INVOICE_DATE",
            "SIRET", "ECHEANCE", "INVOICE_CONTENT", "TVA_PERCENTAGE", "TVA_AMOUNT",
            "TOTAL_AMOUNT", "PAYMENT_STATUS", "SOLDE_DU"]
KEY2LABEL = {
    "supplier_name": "SUPPLIER_NAME", "consumer_name": "CONSUMER_NAME",
    "invoice_number": "INVOICE_NUMBER", "invoice_date": "INVOICE_DATE",
    "siret": "SIRET", "echeance": "ECHEANCE", "tva_percentage": "TVA_PERCENTAGE",
    "tva_amount": "TVA_AMOUNT", "total_amount": "TOTAL_AMOUNT",
    "payment_status": "PAYMENT_STATUS", "solde_du": "SOLDE_DU",
}
LABELS = ["O"] + [f"{p}-{e}" for e in ENTITIES for p in ("B", "I")]
LABEL2ID = {l: i for i, l in enumerate(LABELS)}

PAID_WORDS = ["payé", "paye", "réglé", "regle", "acquitté", "encaissé", "reçu"]
UNPAID_WORDS = ["non payé", "non paye", "impayé", "reste"]


def norm(s):
    return re.sub(r"[^0-9a-zàâäéèêëîïôöûüç]", "", str(s).lower())


def get_words(path: Path):
    """Return (words, boxes[0-1000], image_pil)."""
    if path.suffix.lower() == ".pdf":
        doc = fitz.open(str(path))
        pix = doc[0].get_pixmap(dpi=150)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        doc.close()
    else:
        img = Image.open(path).convert("RGB")
    W, H = img.size
    data = pytesseract.image_to_data(img, lang="fra+eng", output_type=pytesseract.Output.DICT)
    words, boxes = [], []
    for i, txt in enumerate(data["text"]):
        if not txt.strip():
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        words.append(txt)
        boxes.append([int(1000 * x / W), int(1000 * y / H),
                      int(1000 * (x + w) / W), int(1000 * (y + h) / H)])
    return words, boxes


def tag_value(words_norm, value, label, tags):
    """Find a contiguous run of words matching `value`; set B/I tags. One match."""
    target = norm(value)
    if len(target) < 2:
        return
    n = len(words_norm)
    for i in range(n):
        if tags[i] != "O":
            continue
        acc = ""
        for j in range(i, min(i + 12, n)):
            acc += words_norm[j]
            if acc == target or (len(target) >= 4 and target in acc and len(acc) <= len(target) + 3):
                for k in range(i, j + 1):
                    tags[k] = ("B-" if k == i else "I-") + label
                return
            if len(acc) > len(target) + 3:
                break


def tag_status(words, value, tags):
    low = [w.lower() for w in words]
    wl = UNPAID_WORDS if value == "UNPAID" else PAID_WORDS if value == "PAID" else []
    for i, w in enumerate(low):
        if tags[i] != "O":
            continue
        if any(t.split()[0] in w for t in wl):
            tags[i] = "B-PAYMENT_STATUS"
            return


def build_record(path, gt):
    words, boxes = get_words(path)
    if not words:
        return None
    wn = [norm(w) for w in words]
    tags = ["O"] * len(words)

    for key, label in KEY2LABEL.items():
        if key == "payment_status":
            continue
        val = gt.get(key, "")
        if isinstance(val, list):
            for v in val:
                tag_value(wn, v, label, tags)
        elif val:
            tag_value(wn, val, label, tags)
    for it in gt.get("invoice_content", []) or []:
        d = it.get("description", "")
        if len(d) >= 4:
            tag_value(wn, d, "INVOICE_CONTENT", tags)
    tag_status(words, gt.get("payment_status", ""), tags)

    return {
        "id": path.stem,
        "tokens": words,
        "bboxes": boxes,
        "ner_tags": [LABEL2ID[t] for t in tags],
        "labels": tags,
        "image": str(path.relative_to(ROOT)).replace("\\", "/"),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    syn = json.loads((ROOT / "docs" / "synthetic_ground_truth.json").read_text(encoding="utf-8"))
    real = json.loads((ROOT / "docs" / "real_ground_truth.json").read_text(encoding="utf-8"))
    gt = {Path(k).stem: v for k, v in {**syn, **real}.items()}

    files = sorted(PDF_DIR.glob("*.pdf")) + sorted(p for p in IMG_DIR.glob("*") if p.is_file())
    records = []
    for i, p in enumerate(files, 1):
        if p.stem not in gt:
            continue
        rec = build_record(p, gt[p.stem])
        if rec:
            records.append(rec)
        if i % 25 == 0:
            print(f"  processed {i}/{len(files)}", flush=True)

    random.seed(42)
    random.shuffle(records)
    n = len(records)
    n_tr, n_va = int(n * 0.70), int(n * 0.15)
    splits = {"train": records[:n_tr], "val": records[n_tr:n_tr + n_va], "test": records[n_tr + n_va:]}

    for name, recs in splits.items():
        with open(OUT / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (OUT / "labels.txt").write_text("\n".join(LABELS), encoding="utf-8")

    # verify no overlap
    ids = {k: {r["id"] for r in v} for k, v in splits.items()}
    overlap = (ids["train"] & ids["val"]) | (ids["train"] & ids["test"]) | (ids["val"] & ids["test"])
    summary = {
        "total_docs": n, "train": len(splits["train"]), "val": len(splits["val"]),
        "test": len(splits["test"]), "labels": len(LABELS), "split_overlap": len(overlap),
        "avg_tokens": round(sum(len(r["tokens"]) for r in records) / n, 1),
        "tagged_token_ratio": round(
            sum(1 for r in records for t in r["labels"] if t != "O") /
            sum(len(r["tokens"]) for r in records), 3),
    }
    (OUT / "dataset_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
