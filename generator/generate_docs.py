"""
Synthetic Industrial Document Generator
========================================
Generates realistic sample PDFs for 5 document types in English and French.
Part of Milestone 1, Task 01 of the AI Document Intelligence Project.

Document types:
    - Fabrication Sheet  / Fiche de Fabrication
    - Welding Plan       / Plan de Soudage
    - Invoice            / Facture
    - Material Certificate / Certificat Matiere (EN 10204 3.1)
    - Inspection Report  / Rapport d'Inspection

Each document contains the 5 target entities:
    Project ID, Supplier, Material Type, Quantity, Date

Outputs:
    data/raw/digital_pdfs/   - 20 clean PDFs (2 per type per language)
    data/raw/scanned_docs/   - 20 scanned-look PDFs (rotation, noise, stamps, fade)
"""

import os
import random
import json
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
import subprocess
import math

# --------------------------------------------------------------------------
# Seeded RNG so regenerations stay reproducible
# --------------------------------------------------------------------------
SEED = 42
random.seed(SEED)

# --------------------------------------------------------------------------
# Output paths
# --------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
DIGITAL_DIR = RAW / "digital_pdfs"
SCANNED_DIR = RAW / "scanned_docs"
TMP_DIR = BASE / "generator" / "_tmp"
for p in (DIGITAL_DIR, SCANNED_DIR, TMP_DIR):
    p.mkdir(parents=True, exist_ok=True)

# Map internal dtype -> project CamelCase used in filenames
DTYPE_TO_FILENAME = {
    "material_certificate": "MaterialCert",
    "welding_plan":         "WeldingPlan",
    "fabrication_sheet":    "FabricationSheet",
    "inspection_report":    "InspectionReport",
    "invoice":              "Invoice",
}


def digital_dir(lang): return DIGITAL_DIR
def scanned_dir(lang): return SCANNED_DIR

# --------------------------------------------------------------------------
# Faker locales
# --------------------------------------------------------------------------
fakers = {
    "en": Faker("en_US"),
    "fr": Faker("fr_FR"),
}
for f in fakers.values():
    f.seed_instance(SEED)

# --------------------------------------------------------------------------
# Shared entity generators
# --------------------------------------------------------------------------
MATERIALS = [
    "SS 316", "SS 304", "Carbon Steel A36", "Carbon Steel A106 Gr.B",
    "Aluminium 6061-T6", "Inconel 625", "Duplex 2205", "PVC Sch 80",
    "Hastelloy C-276", "Copper C110", "Galvanized Steel", "Monel 400",
]
UNITS = ["pcs", "kg", "m", "tons", "lbs", "units"]
PROJECT_PREFIXES = ["PRJ", "WO", "JOB", "FAB", "PO", "WLD"]


def make_project_id():
    prefix = random.choice(PROJECT_PREFIXES)
    return f"{prefix}-{random.randint(1000, 99999)}"


def make_material():
    return random.choice(MATERIALS)


def make_quantity():
    amount = random.choice([
        random.randint(5, 500),
        round(random.uniform(1.5, 250.0), 2),
    ])
    unit = random.choice(UNITS)
    return f"{amount} {unit}"


def make_date(lang: str):
    d = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 820))
    if lang == "fr":
        return d.strftime("%d/%m/%Y")
    return random.choice([d.strftime("%d/%m/%Y"), d.strftime("%Y-%m-%d"), d.strftime("%b %d, %Y")])


def make_supplier(lang: str):
    return fakers[lang].company()


# --------------------------------------------------------------------------
# Labels per language
# --------------------------------------------------------------------------
LABELS = {
    "en": {
        "fabrication_title": "FABRICATION SHEET",
        "welding_title": "WELDING PLAN",
        "invoice_title": "INVOICE",
        "cert_title": "MATERIAL TEST CERTIFICATE (EN 10204 3.1)",
        "inspection_title": "INSPECTION REPORT",
        "project_id": "Project ID",
        "supplier": "Supplier",
        "vendor": "Vendor",
        "manufacturer": "Manufacturer",
        "material": "Material",
        "quantity": "Quantity",
        "date": "Date",
        "issue_date": "Issue Date",
        "inspection_date": "Inspection Date",
        "due_date": "Due Date",
        "invoice_no": "Invoice No.",
        "po_number": "PO Number",
        "description": "Description",
        "unit_price": "Unit Price",
        "total": "Total",
        "subtotal": "Subtotal",
        "tax": "VAT 20%",
        "grand_total": "Grand Total",
        "heat_no": "Heat No.",
        "spec": "Specification",
        "grade": "Grade",
        "inspector": "Inspector",
        "result": "Result",
        "pass": "PASS",
        "fail": "FAIL",
        "remarks": "Remarks",
        "client": "Client",
        "prepared_by": "Prepared by",
        "approved_by": "Approved by",
        "reviewed_by": "Reviewed by",
        "signature": "Signature",
        "welder_id": "Welder ID",
        "process": "Welding Process",
        "filler": "Filler Metal",
        "joint": "Joint Type",
        "thickness": "Thickness",
        "page": "Page",
        "of": "of",
    },
    "fr": {
        "fabrication_title": "FICHE DE FABRICATION",
        "welding_title": "PLAN DE SOUDAGE",
        "invoice_title": "FACTURE",
        "cert_title": "CERTIFICAT MATIERE (EN 10204 3.1)",
        "inspection_title": "RAPPORT D'INSPECTION",
        "project_id": "N\u00b0 Projet",
        "supplier": "Fournisseur",
        "vendor": "Vendeur",
        "manufacturer": "Fabricant",
        "material": "Mati\u00e8re",
        "quantity": "Quantit\u00e9",
        "date": "Date",
        "issue_date": "Date d'\u00e9mission",
        "inspection_date": "Date d'inspection",
        "due_date": "Date d'\u00e9ch\u00e9ance",
        "invoice_no": "N\u00b0 Facture",
        "po_number": "N\u00b0 Commande",
        "description": "D\u00e9signation",
        "unit_price": "Prix Unitaire",
        "total": "Total",
        "subtotal": "Sous-total",
        "tax": "TVA 20%",
        "grand_total": "Total TTC",
        "heat_no": "N\u00b0 Coul\u00e9e",
        "spec": "Sp\u00e9cification",
        "grade": "Nuance",
        "inspector": "Inspecteur",
        "result": "R\u00e9sultat",
        "pass": "CONFORME",
        "fail": "NON CONFORME",
        "remarks": "Remarques",
        "client": "Client",
        "prepared_by": "Pr\u00e9par\u00e9 par",
        "approved_by": "Approuv\u00e9 par",
        "reviewed_by": "Revu par",
        "signature": "Signature",
        "welder_id": "Code Soudeur",
        "process": "Proc\u00e9d\u00e9 de Soudage",
        "filler": "M\u00e9tal d'Apport",
        "joint": "Type de Joint",
        "thickness": "\u00c9paisseur",
        "page": "Page",
        "of": "sur",
    },
}


# --------------------------------------------------------------------------
# Style helpers
# --------------------------------------------------------------------------
def base_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("TitleBig", parent=styles["Title"], fontSize=18,
                              alignment=TA_CENTER, spaceAfter=10, textColor=colors.HexColor("#1a2a4a")))
    styles.add(ParagraphStyle("H2Mid", parent=styles["Heading2"], fontSize=12,
                              spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#1a2a4a")))
    styles.add(ParagraphStyle("Small", parent=styles["Normal"], fontSize=8))
    styles.add(ParagraphStyle("BodyL", parent=styles["Normal"], fontSize=10, alignment=TA_LEFT))
    return styles


def header_banner(lang, company_name):
    L = LABELS[lang]
    return Table(
        [[company_name, ""]],
        colWidths=[120 * mm, 60 * mm],
        style=TableStyle([
            ("FONT", (0, 0), (0, 0), "Helvetica-Bold", 14),
            ("TEXTCOLOR", (0, 0), (0, 0), colors.HexColor("#1a2a4a")),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#1a2a4a")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]),
    )


# --------------------------------------------------------------------------
# Document builders -- return (path, metadata dict)
# --------------------------------------------------------------------------
def build_fabrication_sheet(out_path, lang, idx):
    L = LABELS[lang]
    styles = base_styles()
    doc = SimpleDocTemplate(str(out_path), pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    story = []
    company = fakers[lang].company() + (" Engineering" if lang == "en" else " Ing\u00e9nierie")
    pid = make_project_id()
    supplier = make_supplier(lang)
    material = make_material()
    qty = make_quantity()
    date = make_date(lang)

    story.append(header_banner(lang, company))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(L["fabrication_title"], styles["TitleBig"]))
    story.append(Spacer(1, 4*mm))

    info = [
        [f"{L['project_id']}:", pid, f"{L['date']}:", date],
        [f"{L['supplier']}:", supplier, f"{L['po_number']}:", f"PO-{random.randint(10000,99999)}"],
        [f"{L['client']}:", fakers[lang].company(), f"{L['inspector']}:", fakers[lang].name()],
    ]
    story.append(Table(info, colWidths=[30*mm, 60*mm, 30*mm, 50*mm], style=TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 9),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ])))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Bill of Materials" if lang == "en" else "Nomenclature", styles["H2Mid"]))

    header = ["Item", "Part No.", L["description"], L["material"], L["quantity"], L["spec"]] if lang == "en" else \
             ["Art.", "N\u00b0 Pi\u00e8ce", L["description"], L["material"], L["quantity"], L["spec"]]
    rows = [header]
    for i in range(1, 6):
        rows.append([
            str(i),
            f"P-{random.randint(1000,9999)}",
            fakers[lang].bs().title()[:30],
            random.choice(MATERIALS),
            f"{random.randint(1,50)} {random.choice(UNITS)}",
            f"ASTM A-{random.randint(100,900)}",
        ])
    # Put the "primary" material + qty in row 1 to match ground truth
    rows[1][3] = material
    rows[1][4] = qty

    story.append(Table(rows, colWidths=[10*mm, 20*mm, 55*mm, 32*mm, 25*mm, 30*mm], style=TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce3ee")),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        ("Notes: All materials to be inspected per procedure QA-FAB-001. "
         "Weld details refer to attached WPS.") if lang == "en" else
        ("Notes : Toutes les mati\u00e8res sont inspect\u00e9es selon la proc\u00e9dure QA-FAB-001. "
         "Les d\u00e9tails de soudage sont pr\u00e9cis\u00e9s dans le DMOS joint."),
        styles["BodyL"],
    ))

    story.append(Spacer(1, 12*mm))
    sigs = [
        [f"{L['prepared_by']}: {fakers[lang].name()}", f"{L['approved_by']}: {fakers[lang].name()}"],
        [f"{L['signature']}: ______________", f"{L['signature']}: ______________"],
    ]
    story.append(Table(sigs, colWidths=[90*mm, 90*mm], style=TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ])))

    doc.build(story)
    return {"project_id": pid, "supplier": supplier, "material": material,
            "quantity": qty, "date": date, "doc_type": "fabrication_sheet"}


def build_welding_plan(out_path, lang, idx):
    L = LABELS[lang]
    styles = base_styles()
    doc = SimpleDocTemplate(str(out_path), pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    story = []
    company = fakers[lang].company() + (" Welding Services" if lang == "en" else " Soudage SAS")
    pid = make_project_id()
    supplier = make_supplier(lang)
    material = make_material()
    qty = make_quantity()
    date = make_date(lang)

    story.append(header_banner(lang, company))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(L["welding_title"], styles["TitleBig"]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(f"WPS No.: WPS-{random.randint(100,999)}-{random.randint(10,99)}",
                           styles["BodyL"]))
    story.append(Spacer(1, 4*mm))

    info = [
        [f"{L['project_id']}:", pid, f"{L['date']}:", date],
        [f"{L['supplier']}:", supplier, f"{L['welder_id']}:", f"W-{random.randint(100,999)}"],
        [f"{L['material']}:", material, f"{L['quantity']}:", qty],
        [f"{L['process']}:", random.choice(["GTAW (TIG)", "SMAW", "GMAW (MIG)", "FCAW"]),
         f"{L['thickness']}:", f"{random.randint(3,30)} mm"],
        [f"{L['filler']}:", f"ER{random.choice(['70S-6','308L','316L','625'])}",
         f"{L['joint']}:", random.choice(["Butt", "Fillet", "Tee", "Lap"]) if lang == "en"
         else random.choice(["Bout \u00e0 bout", "Angle", "En T", "\u00e0 Clin"])],
    ]
    story.append(Table(info, colWidths=[40*mm, 55*mm, 35*mm, 50*mm], style=TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 9),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ])))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Welding Parameters" if lang == "en" else "Param\u00e8tres de Soudage",
                           styles["H2Mid"]))
    params = [
        ["Pass", "Current (A)", "Voltage (V)", "Travel (mm/min)", "Gas"],
    ] if lang == "en" else [
        ["Passe", "Courant (A)", "Tension (V)", "Vitesse (mm/min)", "Gaz"],
    ]
    for i in range(1, 5):
        params.append([
            f"P{i}",
            str(random.randint(80, 240)),
            str(random.randint(18, 32)),
            str(random.randint(80, 220)),
            random.choice(["Ar 100%", "Ar/CO2 80/20", "Ar/He 70/30", "-"]),
        ])
    story.append(Table(params, colWidths=[20*mm, 35*mm, 35*mm, 45*mm, 35*mm], style=TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce3ee")),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ])))

    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        ("Pre-heat: 100\u00b0C min. Interpass: 150\u00b0C max. PWHT as per ASME IX.") if lang == "en" else
        ("Pr\u00e9chauffage : 100\u00b0C min. Interpasse : 150\u00b0C max. TTAS selon ASME IX."),
        styles["BodyL"],
    ))
    story.append(Spacer(1, 10*mm))
    story.append(Table([
        [f"{L['approved_by']}: {fakers[lang].name()}", f"{L['date']}: {date}"],
    ], colWidths=[95*mm, 85*mm], style=TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
    ])))

    doc.build(story)
    return {"project_id": pid, "supplier": supplier, "material": material,
            "quantity": qty, "date": date, "doc_type": "welding_plan"}


def build_invoice(out_path, lang, idx):
    L = LABELS[lang]
    styles = base_styles()
    doc = SimpleDocTemplate(str(out_path), pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    story = []
    supplier_company = fakers[lang].company() + (" Ltd." if lang == "en" else " SARL")
    pid = make_project_id()
    material = make_material()
    qty = make_quantity()
    date = make_date(lang)

    story.append(header_banner(lang, supplier_company))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(L["invoice_title"], styles["TitleBig"]))
    story.append(Spacer(1, 4*mm))

    inv_no = f"INV-{random.randint(10000,99999)}"
    client = fakers[lang].company()

    info_left = [
        [f"{L['supplier']}:", supplier_company],
        [f"{L['client']}:", client],
        [fakers[lang].address().replace("\n", ", "), ""],
    ]
    info_right = [
        [f"{L['invoice_no']}:", inv_no],
        [f"{L['issue_date']}:", date],
        [f"{L['due_date']}:", make_date(lang)],
        [f"{L['project_id']}:", pid],
    ]
    combined = []
    maxlen = max(len(info_left), len(info_right))
    for i in range(maxlen):
        l = info_left[i] if i < len(info_left) else ["", ""]
        r = info_right[i] if i < len(info_right) else ["", ""]
        combined.append(l + r)

    story.append(Table(combined, colWidths=[28*mm, 60*mm, 28*mm, 50*mm], style=TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 9),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.lightgrey),
    ])))

    story.append(Spacer(1, 6*mm))
    header = ["#", L["description"], L["material"], L["quantity"], L["unit_price"], L["total"]]
    rows = [header]
    subtotal = 0.0
    for i in range(1, 5):
        up = round(random.uniform(10, 500), 2)
        q = random.randint(1, 80)
        line = round(up * q, 2)
        subtotal += line
        rows.append([
            str(i),
            fakers[lang].bs().title()[:32],
            random.choice(MATERIALS),
            f"{q} {random.choice(UNITS)}",
            f"{up:.2f} \u20ac" if lang == "fr" else f"${up:.2f}",
            f"{line:.2f} \u20ac" if lang == "fr" else f"${line:.2f}",
        ])
    # Put the primary material + qty in line 1 to match ground truth
    rows[1][2] = material
    rows[1][3] = qty

    story.append(Table(rows, colWidths=[10*mm, 65*mm, 32*mm, 25*mm, 25*mm, 25*mm], style=TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2a4a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ])))

    story.append(Spacer(1, 4*mm))
    tax = round(subtotal * 0.20, 2)
    grand = round(subtotal + tax, 2)
    cur = "\u20ac" if lang == "fr" else "$"
    totals = [
        [f"{L['subtotal']}:", f"{subtotal:.2f} {cur}"],
        [f"{L['tax']}:", f"{tax:.2f} {cur}"],
        [f"{L['grand_total']}:", f"{grand:.2f} {cur}"],
    ]
    story.append(Table(totals, colWidths=[150*mm, 30*mm], hAlign="RIGHT", style=TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 10),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ])))

    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        ("Payment terms: 30 days net. Bank transfer only. Thank you for your business.") if lang == "en" else
        ("Conditions de paiement : 30 jours net. Virement bancaire uniquement. Merci de votre confiance."),
        styles["Small"],
    ))

    doc.build(story)
    return {"project_id": pid, "supplier": supplier_company, "material": material,
            "quantity": qty, "date": date, "doc_type": "invoice"}


def build_material_certificate(out_path, lang, idx):
    L = LABELS[lang]
    styles = base_styles()
    doc = SimpleDocTemplate(str(out_path), pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    story = []
    mill = fakers[lang].company() + (" Steel Mills" if lang == "en" else " Aci\u00e9ries")
    pid = make_project_id()
    material = make_material()
    qty = make_quantity()
    date = make_date(lang)
    heat = f"H-{random.randint(100000,999999)}"

    story.append(header_banner(lang, mill))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(L["cert_title"], styles["TitleBig"]))
    story.append(Spacer(1, 4*mm))

    info = [
        [f"{L['manufacturer']}:", mill, f"{L['heat_no']}:", heat],
        [f"{L['project_id']}:", pid, f"{L['date']}:", date],
        [f"{L['material']}:", material, f"{L['quantity']}:", qty],
        [f"{L['grade']}:", random.choice(["A", "B", "C"]),
         f"{L['spec']}:", f"ASTM A{random.randint(100,900)} / EN 10025"],
    ]
    story.append(Table(info, colWidths=[40*mm, 55*mm, 30*mm, 50*mm], style=TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 9),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ])))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        "Chemical Composition (%)" if lang == "en" else "Composition Chimique (%)",
        styles["H2Mid"],
    ))
    header_chem = ["C", "Mn", "Si", "P", "S", "Cr", "Ni", "Mo"]
    row_chem = [f"{random.uniform(0.01,0.3):.3f}" for _ in header_chem]
    story.append(Table([header_chem, row_chem], colWidths=[20*mm]*8, style=TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
        ("FONT", (0, 1), (-1, 1), "Helvetica", 8),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce3ee")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ])))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Mechanical Properties" if lang == "en" else "Propri\u00e9t\u00e9s M\u00e9caniques",
        styles["H2Mid"],
    ))
    mech = [
        ["Yield (MPa)", "Tensile (MPa)", "Elongation %", "Hardness HB", "Impact (J)"],
        [str(random.randint(250, 550)), str(random.randint(400, 750)),
         f"{random.randint(18,38)}", str(random.randint(120, 260)), str(random.randint(25, 160))],
    ]
    if lang == "fr":
        mech[0] = ["Limite \u00e9lastique", "R\u00e9sistance", "Allongement %", "Duret\u00e9 HB", "R\u00e9silience (J)"]
    story.append(Table(mech, colWidths=[32*mm]*5, style=TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
        ("FONT", (0, 1), (-1, 1), "Helvetica", 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce3ee")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ])))

    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        ("We hereby certify that the material described above has been tested in accordance "
         "with the applicable specifications and complies with all requirements.") if lang == "en" else
        ("Nous certifions par la pr\u00e9sente que la mati\u00e8re d\u00e9crite ci-dessus a \u00e9t\u00e9 "
         "contr\u00f4l\u00e9e conform\u00e9ment aux sp\u00e9cifications applicables et satisfait "
         "\u00e0 toutes les exigences."),
        styles["BodyL"],
    ))

    story.append(Spacer(1, 12*mm))
    story.append(Table([
        [f"{L['inspector']}: {fakers[lang].name()}", f"{L['signature']}: ______________"],
    ], colWidths=[95*mm, 85*mm], style=TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
    ])))

    doc.build(story)
    return {"project_id": pid, "supplier": mill, "material": material,
            "quantity": qty, "date": date, "doc_type": "material_certificate"}


def build_inspection_report(out_path, lang, idx):
    L = LABELS[lang]
    styles = base_styles()
    doc = SimpleDocTemplate(str(out_path), pagesize=A4,
                            leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    story = []
    company = fakers[lang].company() + (" QA Services" if lang == "en" else " Contr\u00f4le Qualit\u00e9")
    pid = make_project_id()
    supplier = make_supplier(lang)
    material = make_material()
    qty = make_quantity()
    date = make_date(lang)

    story.append(header_banner(lang, company))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(L["inspection_title"], styles["TitleBig"]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(f"Report No.: IR-{random.randint(10000,99999)}", styles["BodyL"]))
    story.append(Spacer(1, 4*mm))

    info = [
        [f"{L['project_id']}:", pid, f"{L['inspection_date']}:", date],
        [f"{L['supplier']}:", supplier, f"{L['inspector']}:", fakers[lang].name()],
        [f"{L['material']}:", material, f"{L['quantity']}:", qty],
    ]
    story.append(Table(info, colWidths=[38*mm, 60*mm, 35*mm, 47*mm], style=TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 9),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ])))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        "Inspection Findings" if lang == "en" else "Constats d'Inspection",
        styles["H2Mid"],
    ))
    checks_en = [
        "Dimensional check per drawing",
        "Visual weld inspection (AWS D1.1)",
        "Surface finish Ra <= 3.2",
        "Coating thickness 80-120 um",
        "Leak test at 1.5x design pressure",
    ]
    checks_fr = [
        "Contr\u00f4le dimensionnel selon plan",
        "Contr\u00f4le visuel des soudures (AWS D1.1)",
        "Rugosit\u00e9 de surface Ra <= 3.2",
        "\u00c9paisseur rev\u00eatement 80-120 um",
        "Essai d'\u00e9tanch\u00e9it\u00e9 \u00e0 1,5x pression",
    ]
    checks = checks_en if lang == "en" else checks_fr

    header = ["#", L["description"], L["result"], L["remarks"]]
    rows = [header]
    for i, c in enumerate(checks, 1):
        result = random.choice([L["pass"], L["pass"], L["pass"], L["fail"]])
        remark = fakers[lang].sentence(nb_words=6)[:50] if result == L["fail"] else "-"
        rows.append([str(i), c, result, remark])

    story.append(Table(rows, colWidths=[10*mm, 78*mm, 30*mm, 62*mm], style=TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce3ee")),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])))

    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        ("Overall result: ACCEPTED pending closure of minor findings above.") if lang == "en" else
        ("R\u00e9sultat global : ACCEPT\u00c9 sous r\u00e9serve de traitement des constats mineurs ci-dessus."),
        styles["BodyL"],
    ))
    story.append(Spacer(1, 10*mm))
    story.append(Table([
        [f"{L['inspector']}: {fakers[lang].name()}", f"{L['approved_by']}: {fakers[lang].name()}"],
        [f"{L['signature']}: ______________", f"{L['signature']}: ______________"],
    ], colWidths=[90*mm, 90*mm], style=TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
    ])))

    doc.build(story)
    return {"project_id": pid, "supplier": supplier, "material": material,
            "quantity": qty, "date": date, "doc_type": "inspection_report"}


BUILDERS = {
    "fabrication_sheet": build_fabrication_sheet,
    "welding_plan": build_welding_plan,
    "invoice": build_invoice,
    "material_certificate": build_material_certificate,
    "inspection_report": build_inspection_report,
}


# --------------------------------------------------------------------------
# PDF -> degraded scanned-look PDF
# --------------------------------------------------------------------------
def degrade_to_scanned_pdf(src_pdf: Path, dst_pdf: Path, seed: int):
    """Rasterize PDF pages, apply noise/rotation/fade/stamp, rewrap to PDF."""
    rng = random.Random(seed)
    # Rasterize at moderate DPI
    subprocess.run(
        ["pdftoppm", "-r", "180", "-png", str(src_pdf), str(TMP_DIR / f"page_{seed}")],
        check=True,
    )
    pages = sorted(TMP_DIR.glob(f"page_{seed}-*.png"))
    processed = []
    for p in pages:
        img = Image.open(p).convert("RGB")
        # slight downscale to simulate scan resolution
        w, h = img.size
        img = img.resize((int(w * 0.72), int(h * 0.72)), Image.LANCZOS)

        # Rotate slightly
        angle = rng.uniform(-2.5, 2.5)
        img = img.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=(245, 242, 230))

        # Apply sepia/fade tint
        r, g, b = img.split()
        r = r.point(lambda v: min(255, int(v * rng.uniform(0.88, 0.98))))
        g = g.point(lambda v: min(255, int(v * rng.uniform(0.85, 0.95))))
        b = b.point(lambda v: min(255, int(v * rng.uniform(0.78, 0.90))))
        img = Image.merge("RGB", (r, g, b))

        # Gaussian blur (light)
        if rng.random() < 0.6:
            img = img.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.3, 1.1)))

        # Add noise
        px = img.load()
        W, H = img.size
        noise_density = rng.uniform(0.005, 0.02)
        num_noise = int(W * H * noise_density)
        for _ in range(num_noise):
            x = rng.randint(0, W - 1)
            y = rng.randint(0, H - 1)
            shade = rng.randint(50, 180)
            px[x, y] = (shade, shade, shade)

        # Add occasional coffee stain / blob
        draw = ImageDraw.Draw(img)
        if rng.random() < 0.7:
            cx = rng.randint(int(W * 0.1), int(W * 0.9))
            cy = rng.randint(int(H * 0.1), int(H * 0.9))
            rr = rng.randint(30, 90)
            draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                         fill=(190, 165, 120))
        # Add stamp (red-ish circle with text)
        if rng.random() < 0.8:
            sx = rng.randint(int(W * 0.55), int(W * 0.85))
            sy = rng.randint(int(H * 0.7), int(H * 0.9))
            r_ = rng.randint(55, 90)
            # Concentric ellipses
            for rr in (r_, r_ - 3):
                draw.ellipse([sx - rr, sy - rr, sx + rr, sy + rr],
                             outline=(180, 30, 30), width=2)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            except Exception:
                font = ImageFont.load_default()
            stamp_text = rng.choice(["APPROVED", "QC PASSED", "VISE", "RECU"])
            draw.text((sx - r_ * 0.55, sy - 8), stamp_text, fill=(180, 30, 30), font=font)

        # Fold-line shadow
        if rng.random() < 0.4:
            ly = rng.randint(int(H * 0.3), int(H * 0.7))
            for dy in range(-2, 3):
                draw.line([(0, ly + dy), (W, ly + dy)], fill=(190, 180, 170), width=1)

        # Light JPEG recompression artifacts
        tmp_jpg = TMP_DIR / f"deg_{seed}_{p.stem}.jpg"
        img.save(tmp_jpg, "JPEG", quality=rng.randint(55, 78))
        processed.append(Image.open(tmp_jpg).convert("RGB"))

    # Save processed images back into a PDF
    if processed:
        first, rest = processed[0], processed[1:]
        first.save(dst_pdf, save_all=True, append_images=rest, resolution=150.0)

    # Cleanup tmp
    for p in pages:
        try: p.unlink()
        except Exception: pass


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    ground_truth = []  # for the answer-key seed
    doc_types = list(BUILDERS.keys())
    idx_counter = 1

    for dtype in doc_types:
        dtype_cc = DTYPE_TO_FILENAME[dtype]
        for lang in ("en", "fr"):
            lang_up = lang.upper()
            # 2 clean digital
            for k in range(1, 3):
                filename = f"Synthetic_{dtype_cc}_{lang_up}_{k:02d}.pdf"
                out_path = digital_dir(lang) / filename
                meta = BUILDERS[dtype](out_path, lang, idx_counter)
                meta.update({
                    "filename": filename,
                    "language": lang,
                    "variant": "digital",
                    "path": str(out_path.relative_to(BASE)),
                })
                ground_truth.append(meta)
                idx_counter += 1

            # 2 scanned-look: build clean first, then degrade
            for k in range(1, 3):
                filename = f"Synthetic_{dtype_cc}_{lang_up}_{k:02d}.pdf"
                clean_tmp = TMP_DIR / f"clean_{dtype}_{lang}_{k}.pdf"
                out_path = scanned_dir(lang) / filename
                meta = BUILDERS[dtype](clean_tmp, lang, idx_counter)
                degrade_to_scanned_pdf(clean_tmp, out_path, seed=idx_counter)
                meta.update({
                    "filename": filename,
                    "language": lang,
                    "variant": "scanned",
                    "path": str(out_path.relative_to(BASE)),
                })
                ground_truth.append(meta)
                idx_counter += 1
                try: clean_tmp.unlink()
                except Exception: pass

    # Write ground-truth seed JSON (team can use to pre-fill Task 02 spreadsheet)
    gt_path = BASE / "generator" / "ground_truth_seed.json"
    gt_path.write_text(json.dumps(ground_truth, indent=2, ensure_ascii=False))

    # Cleanup TMP
    for f in TMP_DIR.glob("*"):
        try: f.unlink()
        except Exception: pass

    print(f"Generated {len(ground_truth)} documents.")
    print(f"  digital_pdfs: {len(list(DIGITAL_DIR.glob('Synthetic_*.pdf')))}")
    print(f"  scanned_docs: {len(list(SCANNED_DIR.glob('Synthetic_*.pdf')))}")
    print(f"Ground-truth seed: {gt_path}")


if __name__ == "__main__":
    main()
