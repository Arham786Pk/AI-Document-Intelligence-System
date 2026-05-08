"""Build ground truth CSV and XLSX for the 19 French invoices.

Reads the labelled rows below (manually populated from each invoice photo/PDF) and
writes ``docs/ground_truth.csv`` and ``docs/ground_truth.xlsx``.
"""
from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DOCS.mkdir(parents=True, exist_ok=True)

COLUMNS = [
    "File Name",
    "Supplier Name",
    "Invoice Number",
    "Invoice Date",
    "SIRET",
    "Echeance",
    "Invoice Content",
    "TVA Percentage",
    "TVA Amount",
    "Total Amount",
    "Payment Status",
    "Solde du",
    "Notes",
]

ROWS: list[dict[str, str]] = [
    {
        "File Name": "IMG-20260507-WA0143.jpg",
        "Supplier Name": "AOYAMA",
        "Invoice Number": "T109200",
        "Invoice Date": "31/03/2026",
        "SIRET": "44418819700016",
        "Echeance": "",
        "Invoice Content": "1 Repas complet",
        "TVA Percentage": "10%; 20%",
        "TVA Amount": "3,40 EUR",
        "Total Amount": "33,90 EUR",
        "Payment Status": "PAID",
        "Solde du": "",
        "Notes": "Justificatif de paiement; CB 33,90 EUR",
    },
    {
        "File Name": "IMG-20260507-WA0144.jpg",
        "Supplier Name": "Hyper Carrefour Chalon",
        "Invoice Number": "00031 00 02 00550383",
        "Invoice Date": "31/03/2026",
        "SIRET": "99269214500012",
        "Echeance": "",
        "Invoice Content": "Gazole 24,03 L @ 2,279 EUR/L",
        "TVA Percentage": "20%",
        "TVA Amount": "9,13 EUR",
        "Total Amount": "54,76 EUR",
        "Payment Status": "PAID",
        "Solde du": "",
        "Notes": "Carte bancaire Visa - debit",
    },
    {
        "File Name": "IMG-20260507-WA0145.jpg",
        "Supplier Name": "Orano Le Prisme",
        "Invoice Number": "002-001-305604",
        "Invoice Date": "31/03/2026",
        "SIRET": "",
        "Echeance": "",
        "Invoice Content": "Petit pain individuel; Conte AOP; Beurre portion x2; Eminence de boeuf",
        "TVA Percentage": "10%; 20%",
        "TVA Amount": "1,07 EUR",
        "Total Amount": "12,84 EUR",
        "Payment Status": "UNKNOWN",
        "Solde du": "",
        "Notes": "Cantine - badge interne; 'Solde 10,19' = solde du badge, pas de la facture",
    },
    {
        "File Name": "IMG-20260507-WA0146.jpg",
        "Supplier Name": "Le Creusot Gare TGV (Effia)",
        "Invoice Number": "25557",
        "Invoice Date": "31/03/2026",
        "SIRET": "",
        "Echeance": "",
        "Invoice Content": "Stationnement Tarif 5 (Entree 17:31 / Paiement 22:31)",
        "TVA Percentage": "20%",
        "TVA Amount": "0,73 EUR",
        "Total Amount": "4,40 EUR",
        "Payment Status": "PAID",
        "Solde du": "",
        "Notes": "Visa sans contact",
    },
    {
        "File Name": "IMG-20260507-WA0147.jpg",
        "Supplier Name": "La Boucherie Restaurant",
        "Invoice Number": "134788",
        "Invoice Date": "29/03/2026",
        "SIRET": "85214583800029",
        "Echeance": "",
        "Invoice Content": "1664 33CL; Tresor Louchebem; Garniture supplement; Supp sauce",
        "TVA Percentage": "10%; 20%",
        "TVA Amount": "4,39 EUR",
        "Total Amount": "43,50 EUR",
        "Payment Status": "PAID",
        "Solde du": "",
        "Notes": "CB sans contact",
    },
    {
        "File Name": "IMG-20260507-WA0148.jpg",
        "Supplier Name": "Studio Photo Lumiere & Art",
        "Invoice Number": "SPL-2024-0198",
        "Invoice Date": "19/04/2024",
        "SIRET": "77789012300234",
        "Echeance": "04/05/2024",
        "Invoice Content": "Seance photo mariage (4h); Retouches numeriques (x80); Album photo 30x30 cm",
        "TVA Percentage": "20%",
        "TVA Amount": "270,00 EUR",
        "Total Amount": "1 620,00 EUR",
        "Payment Status": "UNKNOWN",
        "Solde du": "",
        "Notes": "Conditions de reglement: Virement bancaire sous 15 jours",
    },
    {
        "File Name": "IMG-20260507-WA0149.jpg",
        "Supplier Name": "Clinique Dentaire Sourire",
        "Invoice Number": "CDS-2024-0345",
        "Invoice Date": "16/04/2024",
        "SIRET": "44456789100223",
        "Echeance": "01/05/2024",
        "Invoice Content": "Detartrage complet; Soin carie molaire; Radiographie panoramique",
        "TVA Percentage": "20%",
        "TVA Amount": "59,00 EUR",
        "Total Amount": "354,00 EUR",
        "Payment Status": "PAID",
        "Solde du": "",
        "Notes": "Paye par Carte Bleue **** 2231 le 16/04/2024",
    },
    {
        "File Name": "IMG-20260507-WA0150.jpg",
        "Supplier Name": "Chauffage & Climatisation Roux",
        "Invoice Number": "CCR-2024-0423",
        "Invoice Date": "25/04/2024",
        "SIRET": "99956789200267",
        "Echeance": "25/05/2024",
        "Invoice Content": "Installation climatisation reversible; Mise en service et reglages; Garantie extension 3 ans",
        "TVA Percentage": "10%",
        "TVA Amount": "225,00 EUR",
        "Total Amount": "2 475,00 EUR",
        "Payment Status": "UNKNOWN",
        "Solde du": "",
        "Notes": "Conditions: 40% commande, 60% reception - Virement ou cheque",
    },
    {
        "File Name": "IMG-20260507-WA0151.jpg",
        "Supplier Name": "Fleuriste Jardin d'Eden",
        "Invoice Number": "FJE-2024-0087",
        "Invoice Date": "23/04/2024",
        "SIRET": "66623456700256",
        "Echeance": "08/05/2024",
        "Invoice Content": "Bouquet mariee rose & pivoine; Decoration florale tables (x8); Composition entree salle",
        "TVA Percentage": "10%",
        "TVA Amount": "82,00 EUR",
        "Total Amount": "902,00 EUR",
        "Payment Status": "PAID",
        "Solde du": "",
        "Notes": "Solde paye par American Express **** 8872 le 23/04/2024",
    },
    {
        "File Name": "IMG-20260507-WA0152.jpg + IMG-20260507-WA0157.jpg",
        "Supplier Name": "(non lisible - facture SCA010)",
        "Invoice Number": "FC20251175",
        "Invoice Date": "28/04/2025",
        "SIRET": "",
        "Echeance": "28/05/2025",
        "Invoice Content": "AUDIT INITIAL ISO 19443 Etape 1 & Etape 2; Certification ISO 9001 version 2015",
        "TVA Percentage": "20%",
        "TVA Amount": "672,41 EUR",
        "Total Amount": "4 034,46 EUR",
        "Payment Status": "UNPAID",
        "Solde du": "4 034,46 EUR",
        "Notes": "Mode VIREMENT 30j net; N TVA intracom FR33845175751; deux photos = meme facture",
    },
    {
        "File Name": "IMG-20260507-WA0153.jpg",
        "Supplier Name": "Informatique Solutions Pro",
        "Invoice Number": "ISP-2024-0512",
        "Invoice Date": "21/04/2024",
        "SIRET": "33390123400245",
        "Echeance": "21/05/2024",
        "Invoice Content": "Remplacement disque SSD 1To; Reinstallation Windows 11; Sauvegarde donnees (2h); Antivirus licence 1 an",
        "TVA Percentage": "20%",
        "TVA Amount": "78,80 EUR",
        "Total Amount": "472,80 EUR",
        "Payment Status": "PAID",
        "Solde du": "",
        "Notes": "Paye par Visa **** 4491 le 22/04/2024",
    },
    {
        "File Name": "IMG-20260507-WA0154.jpg + IMG-20260507-WA0158.jpg",
        "Supplier Name": "(non lisible - fournisseur SCAI Systems)",
        "Invoice Number": "",
        "Invoice Date": "",
        "SIRET": "",
        "Echeance": "15/11/2025",
        "Invoice Content": "Scie radiale 1800W D355MM MKAS35 +2 lames; Lame scie D355x25,4x2,2mm 66 dts acier (x9); Lame scie supplementaire (x1)",
        "TVA Percentage": "20%",
        "TVA Amount": "419,80 EUR",
        "Total Amount": "2 518,81 EUR",
        "Payment Status": "UNKNOWN",
        "Solde du": "",
        "Notes": "Facture multi-pages; Mode Virement; Cde 08/09/2025; livre a SCAI Systems Le Creusot",
    },
    {
        "File Name": "IMG-20260507-WA0155.jpg",
        "Supplier Name": "Fers et Metaux du Chalonnais",
        "Invoice Number": "",
        "Invoice Date": "",
        "SIRET": "",
        "Echeance": "31/03/2026",
        "Invoice Content": "Corniere S235 JR 120x120x12; Poutrelle S275 JR IPE 270; Rond serrurier S235 JR Diam18; Corniere 25x25x3; TAC tole a chaud 1000x2000x15; Poutrelle UPN 100; Transport; Corniere 80x80x8",
        "TVA Percentage": "20%",
        "TVA Amount": "1 309,13 EUR",
        "Total Amount": "7 854,77 EUR",
        "Payment Status": "UNKNOWN",
        "Solde du": "",
        "Notes": "Conditions de reglement: le 31/03/26; Acompte 0,00; Net a payer 7 854,77; Virement",
    },
    {
        "File Name": "IMG-20260507-WA0156.jpg",
        "Supplier Name": "Wurth Proxi Shop Le Creusot",
        "Invoice Number": "4330739666",
        "Invoice Date": "",
        "SIRET": "",
        "Echeance": "25/12/2024",
        "Invoice Content": "Disques a meuler MEULE EBARBER ZIRCO+ 230x6.4x22.2; Niveau digital IP65 61CM Zebra; Briquet USB electrique (offert); Coupon cadeau",
        "TVA Percentage": "20%",
        "TVA Amount": "136,50 EUR",
        "Total Amount": "818,98 EUR",
        "Payment Status": "UNKNOWN",
        "Solde du": "",
        "Notes": "Page 2/3 seulement; Conditions 30 jours; Mode Traite directe / Virement",
    },
    {
        "File Name": "Invoice_FR_016_scanned_260508_103316.pdf",
        "Supplier Name": "Epicerie Fine Marchand",
        "Invoice Number": "EFM-2023-0412",
        "Invoice Date": "12/11/2023",
        "SIRET": "12378945600178",
        "Echeance": "27/11/2023",
        "Invoice Content": "Foie gras mi-cuit (4 boites) x6; Confiture artisanale (x12) x12; Huile d'olive AOC (4 flacons) x4",
        "TVA Percentage": "5,5%",
        "TVA Amount": "19,24 EUR",
        "Total Amount": "369,04 EUR",
        "Payment Status": "PAID",
        "Solde du": "",
        "Notes": "Paye par Visa **** 4712 le 13/11/2023",
    },
    {
        "File Name": "Invoice_FR_017_scanned_260508_103241.pdf",
        "Supplier Name": "Atelier Couture & Retouches Blondel",
        "Invoice Number": "ACR-2023-1205",
        "Invoice Date": "05/12/2023",
        "SIRET": "55534567900169",
        "Echeance": "20/12/2023",
        "Invoice Content": "Retouche robe de mariee; Ourlet pantalon (x3); Remplacement fermeture eclair",
        "TVA Percentage": "20%",
        "TVA Amount": "50,00 EUR",
        "Total Amount": "300,00 EUR",
        "Payment Status": "PAID",
        "Solde du": "",
        "Notes": "Especes recues - recu N 2023-1205",
    },
    {
        "File Name": "Invoice_FR_018_scanned_260508_103257.pdf",
        "Supplier Name": "Garage Mecanique Verdier",
        "Invoice Number": "GMV-2023-0789",
        "Invoice Date": "28/10/2023",
        "SIRET": "88801234600190",
        "Echeance": "12/11/2023",
        "Invoice Content": "Vidange + filtre huile; Remplacement plaquettes frein AV; Main d'oeuvre revision (3h); Pneumatiques 195/65 R15 (x2)",
        "TVA Percentage": "20%",
        "TVA Amount": "121,20 EUR",
        "Total Amount": "727,20 EUR",
        "Payment Status": "UNKNOWN",
        "Solde du": "",
        "Notes": "Conditions de reglement: Cheque a l'ordre de Garage Verdier sous 15 jours",
    },
    {
        "File Name": "Invoice_FR_019_scanned_260508_103345.pdf",
        "Supplier Name": "Ecole de Musique Harmonie",
        "Invoice Number": "EMH-2024-0023",
        "Invoice Date": "08/01/2024",
        "SIRET": "33345678900201",
        "Echeance": "08/02/2024",
        "Invoice Content": "Cours de piano - trimestre 1 (x12 seances); Location salle de repetition (x4h); Partition recueil Bach",
        "TVA Percentage": "20%",
        "TVA Amount": "127,70 EUR",
        "Total Amount": "766,20 EUR",
        "Payment Status": "PAID",
        "Solde du": "",
        "Notes": "Reglement par CB Mastercard **** 3308 accepte le 09/01/2024",
    },
    {
        "File Name": "Invoice_FR_020_scanned_260508_103334.pdf",
        "Supplier Name": "Paysagiste Terrain Vert EURL",
        "Invoice Number": "PTV-2024-0156",
        "Invoice Date": "22/02/2024",
        "SIRET": "66612890100212",
        "Echeance": "08/03/2024",
        "Invoice Content": "Tonte pelouse + ramassage (x4 passages); Taille haies et arbustes; Plantation massif fleuri (x15 plants); Evacuation dechets verts",
        "TVA Percentage": "10%",
        "TVA Amount": "73,50 EUR",
        "Total Amount": "808,50 EUR",
        "Payment Status": "UNKNOWN",
        "Solde du": "",
        "Notes": "Conditions de reglement: Virement IBAN FR76 3000 6228 3700 0100 0000 - a regler avant le 08/03/2024",
    },
]


def write_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in ROWS:
            writer.writerow({c: row.get(c, "") for c in COLUMNS})


def write_xlsx(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Ground Truth"
    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(bold=True, color="FFFFFF")
    for col_idx, col in enumerate(COLUMNS, 1):
        cell = ws.cell(row=1, column=col_idx, value=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for r_idx, row in enumerate(ROWS, 2):
        for c_idx, col in enumerate(COLUMNS, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=row.get(col, ""))
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    widths = {
        "File Name": 38,
        "Supplier Name": 28,
        "Invoice Number": 18,
        "Invoice Date": 14,
        "SIRET": 18,
        "Echeance": 14,
        "Invoice Content": 55,
        "TVA Percentage": 12,
        "TVA Amount": 14,
        "Total Amount": 16,
        "Payment Status": 14,
        "Solde du": 16,
        "Notes": 50,
    }
    for col_idx, col in enumerate(COLUMNS, 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = widths.get(col, 18)
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "B2"
    wb.save(path)


if __name__ == "__main__":
    csv_path = DOCS / "ground_truth.csv"
    xlsx_path = DOCS / "ground_truth.xlsx"
    write_csv(csv_path)
    write_xlsx(xlsx_path)
    print(f"Wrote {csv_path} and {xlsx_path} ({len(ROWS)} rows)")
