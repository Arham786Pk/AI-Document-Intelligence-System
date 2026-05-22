"""Generate synthetic French invoices for Milestone 2 (Task 06).

Each invoice is rendered as a clean A4 PDF containing ALL 12 entities defined in
docs/entity_schema.md (including the new consumer_name). A matching ground-truth
record is produced so the documents are training/eval ready.

Usage:
    python scripts/generate_synthetic_invoices.py --pdfs 15 --images 69

PDFs   -> data/pdf/FR_invoice_synth_###.pdf
Images -> data/images/FR_invoice_img_synth_###.png  (rendered from the same layout)
Ground truth (both sets) -> docs/synthetic_ground_truth.json
"""

import argparse
import json
import random
from pathlib import Path

import fitz  # PyMuPDF, for PDF -> PNG
from faker import Faker
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
PDF_OUT = ROOT / "data" / "pdf"
IMG_OUT = ROOT / "data" / "images"
GT_PATH = ROOT / "docs" / "synthetic_ground_truth.json"

fake = Faker("fr_FR")

LEGAL = ["SARL", "SAS", "SA", "EURL", "SCI", "SASU"]
PRODUCTS = [
    "Prestation de conseil", "Développement logiciel", "Maintenance annuelle",
    "Fourniture de matériel", "Formation professionnelle", "Hébergement web",
    "Licence logicielle", "Audit de sécurité", "Support technique",
    "Création graphique", "Rédaction de contenu", "Location d'équipement",
    "Installation réseau", "Nettoyage de locaux", "Transport de marchandises",
]
DATE_LABELS = ["Date", "Date d'émission", "Date facture"]
NUM_LABELS = ["Facture N°", "N° Facture", "Numéro de facture"]
ECH_LABELS = ["Échéance", "Date d'échéance", "Date limite de paiement"]
CLIENT_LABELS = ["Facturé à", "Client", "Destinataire"]


def fr_money(x: float) -> str:
    s = f"{x:,.2f}".replace(",", " ").replace(".", ",")
    return f"{s} €"


def norm(x: float) -> str:
    return f"{x:.2f}"


def make_company() -> str:
    return f"{fake.last_name()} {random.choice(LEGAL)}"


def make_person_or_company() -> str:
    if random.random() < 0.5:
        title = random.choice(["M.", "Mme", "M.", "Mme", ""])
        return f"{title} {fake.first_name()} {fake.last_name()}".strip()
    return make_company()


def build_invoice_data(seed: int) -> dict:
    random.seed(seed)
    Faker.seed(seed)

    supplier = make_company()
    consumer = make_person_or_company()
    while consumer == supplier:
        consumer = make_person_or_company()

    inv_date = fake.date_between(start_date="-2y", end_date="today")
    ech_date = fake.date_between(start_date=inv_date, end_date="+90d")
    siret = "".join(str(random.randint(0, 9)) for _ in range(14))
    invoice_number = f"{random.choice(['FAC', 'F', 'FC'])}-{inv_date.year}-{random.randint(1, 9999):04d}"

    tva_pct = random.choice([5.5, 10, 20, 20, 20])
    n_items = random.randint(2, 6)
    items = []
    subtotal = 0.0
    for _ in range(n_items):
        qty = random.randint(1, 50)
        unit = round(random.uniform(5, 950), 2)
        items.append({"description": random.choice(PRODUCTS),
                      "quantity": str(qty), "unit_price": norm(unit)})
        subtotal += qty * unit

    tva_amount = round(subtotal * tva_pct / 100, 2)
    total = round(subtotal + tva_amount, 2)

    paid = random.random() < 0.5
    if paid:
        payment_status = "PAID"
        solde_du = ""  # nothing outstanding
    else:
        payment_status = "UNPAID"
        solde_du = norm(total)

    return {
        "supplier_name": supplier,
        "invoice_number": invoice_number,
        "invoice_date": inv_date.strftime("%d/%m/%Y"),
        "siret": siret,
        "echeance": ech_date.strftime("%d/%m/%Y"),
        "invoice_content": items,
        "tva_percentage": str(int(tva_pct)) if tva_pct == int(tva_pct) else str(tva_pct),
        "tva_amount": norm(tva_amount),
        "total_amount": norm(total),
        "payment_status": payment_status,
        "solde_du": solde_du,
        "consumer_name": consumer,
        "_subtotal": norm(subtotal),
        "_supplier_addr": fake.address().replace("\n", ", "),
        "_consumer_addr": fake.address().replace("\n", ", "),
    }


def render_pdf(data: dict, out_path: Path):
    c = canvas.Canvas(str(out_path), pagesize=A4)
    w, h = A4
    x = 20 * mm
    y = h - 25 * mm

    # Supplier header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x, y, data["supplier_name"])
    c.setFont("Helvetica", 9)
    y -= 6 * mm
    c.drawString(x, y, data["_supplier_addr"])
    y -= 5 * mm
    c.drawString(x, y, f"SIRET : {data['siret']}")

    # Title
    c.setFont("Helvetica-Bold", 22)
    c.drawRightString(w - 20 * mm, h - 25 * mm, "FACTURE")

    # Invoice meta (right)
    c.setFont("Helvetica", 10)
    my = h - 33 * mm
    for label, key in ((random.choice(NUM_LABELS), "invoice_number"),
                       (random.choice(DATE_LABELS), "invoice_date"),
                       (random.choice(ECH_LABELS), "echeance")):
        c.drawRightString(w - 20 * mm, my, f"{label} : {data[key]}")
        my -= 5 * mm

    # Bill-to block (consumer)
    y -= 16 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, y, f"{random.choice(CLIENT_LABELS)} :")
    c.setFont("Helvetica", 10)
    y -= 5 * mm
    c.drawString(x, y, data["consumer_name"])
    y -= 5 * mm
    c.drawString(x, y, data["_consumer_addr"])

    # Line items table
    y -= 14 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x, y, "Désignation")
    c.drawString(x + 95 * mm, y, "Quantité")
    c.drawString(x + 125 * mm, y, "Prix Unitaire")
    c.drawRightString(w - 20 * mm, y, "Total")
    y -= 2 * mm
    c.line(x, y, w - 20 * mm, y)
    y -= 6 * mm
    c.setFont("Helvetica", 10)
    for it in data["invoice_content"]:
        qty = int(it["quantity"])
        unit = float(it["unit_price"])
        c.drawString(x, y, it["description"])
        c.drawString(x + 95 * mm, y, it["quantity"])
        c.drawString(x + 125 * mm, y, fr_money(unit))
        c.drawRightString(w - 20 * mm, y, fr_money(qty * unit))
        y -= 6 * mm

    # Totals
    y -= 6 * mm
    c.line(x + 90 * mm, y, w - 20 * mm, y)
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    rows = [
        ("Sous-total HT", fr_money(float(data["_subtotal"]))),
        (f"TVA {data['tva_percentage']} %", fr_money(float(data["tva_amount"]))),
        ("Total TTC", fr_money(float(data["total_amount"]))),
    ]
    for label, val in rows:
        c.drawString(x + 90 * mm, y, label)
        c.drawRightString(w - 20 * mm, y, val)
        y -= 6 * mm

    # Payment status + solde
    y -= 4 * mm
    c.setFont("Helvetica-Bold", 11)
    if data["payment_status"] == "PAID":
        c.drawString(x, y, "Statut : Payé")
        c.setFont("Helvetica", 10)
        y -= 6 * mm
        c.drawString(x, y, f"Solde dû : {fr_money(0)}")
    else:
        c.drawString(x, y, "Statut : Non payé")
        c.setFont("Helvetica", 10)
        y -= 6 * mm
        c.drawString(x, y, f"Solde dû : {fr_money(float(data['total_amount']))}")

    c.showPage()
    c.save()


def clean_gt(data: dict, file_name: str) -> dict:
    gt = {k: v for k, v in data.items() if not k.startswith("_")}
    return {"file_name": file_name, **gt}


def pdf_to_png(pdf_path: Path, png_path: Path):
    doc = fitz.open(str(pdf_path))
    pix = doc[0].get_pixmap(dpi=150)
    pix.save(str(png_path))
    doc.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdfs", type=int, default=15)
    ap.add_argument("--images", type=int, default=69)
    args = ap.parse_args()

    PDF_OUT.mkdir(parents=True, exist_ok=True)
    IMG_OUT.mkdir(parents=True, exist_ok=True)
    ground_truth = json.loads(GT_PATH.read_text(encoding="utf-8")) if GT_PATH.exists() else {}

    seed = 1000
    # PDFs
    for i in range(1, args.pdfs + 1):
        name = f"FR_invoice_synth_{i:03d}.pdf"
        data = build_invoice_data(seed); seed += 1
        render_pdf(data, PDF_OUT / name)
        ground_truth[name] = clean_gt(data, name)
    print(f"Generated {args.pdfs} synthetic PDFs")

    # Images (render from the same layout to a temp pdf, then to PNG)
    tmp = ROOT / "scripts" / "_tmp_synth.pdf"
    for i in range(1, args.images + 1):
        name = f"FR_invoice_img_synth_{i:03d}.png"
        data = build_invoice_data(seed); seed += 1
        render_pdf(data, tmp)
        pdf_to_png(tmp, IMG_OUT / name)
        ground_truth[name] = clean_gt(data, name)
    if tmp.exists():
        tmp.unlink()
    print(f"Generated {args.images} synthetic images")

    GT_PATH.write_text(json.dumps(ground_truth, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Ground truth written: {len(ground_truth)} records -> {GT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
