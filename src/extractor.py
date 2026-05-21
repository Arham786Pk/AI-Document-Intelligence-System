"""Task 8 — Rule-based entity extractor for French invoices.

Extracts 11 entity fields from OCR text using regex patterns with full French
synonym tolerance and OCR error handling.

Per Milestone 1 spec:
  * 11 fields: supplier_name, invoice_number, invoice_date, siret, echeance,
    invoice_content, tva_percentage, tva_amount, total_amount, payment_status, solde_du
  * Accent-tolerant regex patterns
  * OCR error handling (missing accents, confused glyphs)
  * Multi-page support via page break markers
  * Output: one JSON per invoice with all 11 fields (empty string if not found)
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import regex

# ---------------------------------------------------------------------------
# Accent-tolerant helper
# ---------------------------------------------------------------------------

def make_accent_tolerant(text: str) -> str:
    replacements = {
        'e': '[eéèê]', 'a': '[aàâ]', 'i': '[iîï]',
        'o': '[oôö]',  'u': '[uùûü]', 'c': '[cç]',
        'E': '[EÉÈÊ]', 'A': '[AÀÂ]',  'I': '[IÎÏ]',
        'O': '[OÔÖ]',  'U': '[UÙÛ]',  'C': '[CÇ]',
    }
    result = text
    for char, pattern in replacements.items():
        result = result.replace(char, pattern)
    return result

SYNONYMS = {
    "supplier_name":  ["fournisseur", "societe", "société", "entreprise", "vendor", "emetteur", "émetteur"],
    "invoice_number": ["n° de facture", "numero de facture", "numéro de facture",
                       "n facture", "no facture", "ref facture", "référence facture",
                       "n° facture", "recu n°", "reçu n°", "transaction n°", "ticket n°"],
    "invoice_date":   ["date facture", "date d'émission", "date d'emission", "emise le",
                       "émise le", "facture le", "date de consommation", "date d'impression",
                       "date", "le"],
    "siret":          ["siret", "n siret", "n° siret", "identifiant siret"],
    "echeance":       ["échéance", "echeance", "date limite de paiement",
                       "date d'échéance", "date d'echeance",
                       "à payer avant", "a payer avant",
                       "à régler avant", "a regler avant", "due date"],
    "invoice_content":["désignation", "designation", "description",
                       "prestations", "articles", "produits et services", "ref article"],
    "tva_percentage": ["tva", "taux tva", "taxe tva", "% tva", "vat rate"],
    "tva_amount":     ["montant tva", "total tva", "vat amount", "mt tva"],
    "total_amount":   ["total ttc", "net a payer", "net à payer", "montant total",
                       "total facture", "total du", "total dû", "total à payer",
                       "montant ttc", "net a pa"],
    "solde_du":       ["solde dû", "solde du", "reste à payer", "reste a payer",
                       "balance due", "montant restant"],
}

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ExtractedEntities:
    file_name: str
    supplier_name: str = ""
    invoice_number: str = ""
    invoice_date: str = ""
    siret: str = ""
    echeance: str = ""
    invoice_content: list[dict[str, str]] = field(default_factory=list)
    tva_percentage: str | list[str] = ""
    tva_amount: str = ""
    total_amount: str = ""
    payment_status: str = "UNKNOWN"
    solde_du: str = ""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_money(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[€EUR\s]', '', text, flags=re.IGNORECASE)
    text = text.replace(',', '.')
    parts = text.split('.')
    if len(parts) > 2:
        text = ''.join(parts[:-1]) + '.' + parts[-1]
    return text.strip()

def normalize_date(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'\s+', '', text).strip()

def build_label_pattern(synonyms: list[str]) -> str:
    return '|'.join(make_accent_tolerant(s) for s in synonyms)

# ---------------------------------------------------------------------------
# 1. Supplier Name
# ---------------------------------------------------------------------------

def extract_supplier_name(text: str) -> str:
    lines = text.split('\n')

    # Try labelled match first
    label_pat = build_label_pattern(SYNONYMS["supplier_name"])
    m = regex.search(rf'(?i)({label_pat})\s*[:=\-–]?\s*([^\n]+)', text)
    if m:
        name = re.sub(r'[,;.]+$', '', m.group(2).strip())
        name = re.split(r'\b\d{{5}}\b', name)[0].strip()
        if name and len(name) > 2:
            return name

    # Company legal form keywords
    for line in lines[:20]:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        if re.search(r'\b(SARL|SAS|EURL|SA\b|SCI|SASU|SCOP|GmbH|Ltd|EURL)\b', line, re.IGNORECASE):
            name = re.sub(r'\s*[|]+\s*$', '', line).strip()
            name = re.sub(r'[,;.]+$', '', name)
            name = re.split(r'\b\d{5}\b', name)[0].strip()
            if name and len(name) > 2:
                return name

    # First meaningful line on page
    skip = [
        r'(?i)^(facture|siret|tva|n°|n[o°]|date|destinataire|adresse|page|tel|fax|email|www)',
        r'\d{14}', r'FR\d{11}',
        r'(?i)^(bon pour|penalite|conditions|poids|iban|bic|rcs|ape)',
    ]
    for line in lines[:15]:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        if any(re.search(p, line) for p in skip):
            continue
        name = re.sub(r'\s*[|]+\s*$', '', line).strip()
        name = re.sub(r'[,;.]+$', '', name)
        name = re.split(r'\b\d{5}\b', name)[0].strip()
        if name and len(name) > 2:
            return name

    return ""

# ---------------------------------------------------------------------------
# 2. Invoice Number  (FIXED — 9 patterns covering all observed OCR formats)
# ---------------------------------------------------------------------------

def extract_invoice_number(text: str) -> str:
    """
    Patterns derived from real OCR output analysis:
      P1  N° : CDS-2024-0345  /  N° : CCR-2024-0423  (structured invoices)
      P2  Facture N° ACR-2023-1205  /  Facture N° EFM-2023-0412
      P3  N° de facture 4330739666  (Würth)
      P4  Transaction N° : 25557  (parking)
      P5  Ticket N°134 788  /  N Ticket : T108200  (restaurant/receipt)
      P6  FC20251175 | 28/04/2025 |  (table-row invoice number)
      P7  reçu N° 2023-1205  (receipt)
      P8  00031 00 02 00550383  (fuel ticket — after "ticket")
      P9  Generic: any alphanumeric code after N°
    """

    # P1: "N° : ALPHA-NUM" — structured invoices
    m = re.search(
        r'(?<![A-Z])N[°o\.]\s*[:\-–]\s*([A-Z]{2,5}[-\s]?\d{4}[-\s]\d{2,6})\b',
        text, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # P2: "Facture N°" or "Facture N " followed by code
    m = re.search(
        r'(?i)facture\s+n[°o]?\s*[:\-–]?\s*([A-Z][A-Z0-9\-/]{3,25})',
        text)
    if m:
        val = m.group(1).split('\n')[0].split('  ')[0].strip()
        if val and not val.upper().startswith('FR'):
            return val

    # P3: "N° de facture DIGITS" (Würth style)
    m = re.search(r'(?i)n[°o]\s+(?:de\s+)?facture\s+(\d{5,15})', text)
    if m:
        return m.group(1).strip()

    # P4: "Transaction N° : 25557" (parking ticket)
    m = re.search(r'(?i)transaction\s+n[°o]\s*[:\-–]?\s*(\d{4,12})', text)
    if m:
        return m.group(1).strip()

    # P5: "Ticket N°134 788" / "N Ticket : T108200" (restaurant)
    m = re.search(r'(?i)(?:n\s+ticket|ticket\s+n[°o]?)\s*[:\-–]?\s*([A-Z]?\d{4,12})', text)
    if m:
        return m.group(1).strip().replace(' ', '')

    # P6: Table row — alphanumeric code at line start followed by pipe and date
    m = re.search(r'(?m)^([A-Z]{2,4}\d{6,12})\s+[|l]?\s*\d{1,2}/\d{1,2}/\d{4}', text)
    if m:
        return m.group(1).strip()

    # P7: "reçu N° 2023-1205"
    m = re.search(r'(?i)re[çc]u\s+n[°o]?\s*[:\-–]?\s*([A-Z0-9][A-Z0-9\-/]{3,20})', text)
    if m:
        return m.group(1).strip()

    # P8: Fuel receipt ticket number (long numeric)
    m = re.search(r'(?i)ticket\s+(?:mo|n[°o]?)[:\s]+(\d[\d\s]{6,20}\d)', text)
    if m:
        return m.group(1).strip().replace(' ', '')

    # P9: Generic "N° : ALPHANUMERIC" fallback
    m = re.search(r'(?<!\w)N[°o\.]\s*[:\-–]\s*([A-Z][A-Z0-9\-/]{3,25})', text, re.IGNORECASE)
    if m:
        val = m.group(1).strip()
        if not val.upper().startswith('FR'):
            return val

    return ""

# ---------------------------------------------------------------------------
# 3. Invoice Date
# ---------------------------------------------------------------------------

def extract_invoice_date(text: str) -> str:
    date_pat = r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})\b'
    label_pat = build_label_pattern(SYNONYMS["invoice_date"])
    m = regex.search(rf'(?i)({label_pat})\s*[:=\-–]?\s*{date_pat}', text)
    if m:
        return normalize_date(f"{m.group(2)}/{m.group(3)}/{m.group(4)}")
    lines = text.split('\n')
    top = '\n'.join(lines[:len(lines)//2])
    m = re.search(date_pat, top)
    if m:
        return normalize_date(f"{m.group(1)}/{m.group(2)}/{m.group(3)}")
    return ""

# ---------------------------------------------------------------------------
# 4. SIRET
# ---------------------------------------------------------------------------

def extract_siret(text: str) -> str:
    pat = r'\b(\d{3})\s?(\d{3})\s?(\d{3})\s?(\d{5})\b'
    label_pat = build_label_pattern(SYNONYMS["siret"])
    m = regex.search(rf'(?i)({label_pat})\s*[:=\-–]?\s*{pat}', text)
    if m:
        return m.group(2) + m.group(3) + m.group(4) + m.group(5)
    m = re.search(pat, text)
    if m:
        ctx = text[max(0, m.start()-10):m.start()]
        if not re.search(r'(?i)tva|fr', ctx):
            return m.group(1) + m.group(2) + m.group(3) + m.group(4)
    return ""

# ---------------------------------------------------------------------------
# 5. Echeance
# ---------------------------------------------------------------------------

def extract_echeance(text: str) -> str:
    date_pat = r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})\b'
    label_pat = build_label_pattern(SYNONYMS["echeance"])
    m = regex.search(rf'(?i)({label_pat})\s*[:=\-–]?\s*{date_pat}', text)
    if m:
        return normalize_date(f"{m.group(2)}/{m.group(3)}/{m.group(4)}")
    return ""

# ---------------------------------------------------------------------------
# 6. Invoice Content
# ---------------------------------------------------------------------------

def extract_invoice_content(text: str) -> list[dict[str, str]]:
    items = []
    label_pat = build_label_pattern(SYNONYMS["invoice_content"])
    hdr = regex.search(rf'(?i)({label_pat})', text)
    if not hdr:
        return items

    remaining = text[hdr.end():]
    end_pos = len(remaining)
    for marker in [r'(?i)montant\s+ht', r'(?i)total\s+ht', r'(?i)total\s+ttc', r'(?i)sous\s*total']:
        m2 = re.search(marker, remaining)
        if m2:
            end_pos = min(end_pos, m2.start())

    for line in remaining[:end_pos].split('\n'):
        line = line.strip()
        if not line or len(line) < 3:
            continue
        if regex.match(r'(?i)(qte|quantite|quantity|prix|price|total)', line):
            continue
        numbers = re.findall(r'[\d,\.]+', line)
        desc = line
        qty = ""
        price = ""
        if numbers:
            for n in numbers:
                desc = desc.replace(n, '', 1)
            desc = re.sub(r'[x*×]', '', desc).strip()
            desc = re.sub(r'\s+', ' ', desc)
            if len(numbers) >= 2:
                qty = numbers[-2]
                price = normalize_money(numbers[-1])
            elif numbers:
                price = normalize_money(numbers[0])
        if desc:
            items.append({"description": desc.strip(), "quantity": qty, "unit_price": price})
    return items

# ---------------------------------------------------------------------------
# 7. TVA Percentage  (any rate — NOT hardcoded to 20%)
# ---------------------------------------------------------------------------

def extract_tva_percentage(text: str) -> str | list[str]:
    pct = r'(\d{1,2}(?:[,\.]?\d{0,2})?)\s*%'
    rates: set[str] = set()

    for m in re.finditer(rf'(?i)tva\s+{pct}', text):
        r = m.group(1).replace(',', '.')
        try:
            if float(r) <= 100:
                rates.add(r)
        except ValueError:
            pass

    for line in text.split('\n'):
        if regex.search(r'(?i)tva', line):
            for m in re.finditer(pct, line):
                r = m.group(1).replace(',', '.')
                try:
                    if float(r) <= 100:
                        rates.add(r)
                except ValueError:
                    pass

    for m in re.finditer(rf'(?i)(?:taux|taxe)\s+tva\s*[:\-–]?\s*{pct}', text):
        r = m.group(1).replace(',', '.')
        try:
            if float(r) <= 100:
                rates.add(r)
        except ValueError:
            pass

    lst = sorted(list(rates), key=lambda x: float(x))
    if not lst:
        return ""
    return lst[0] if len(lst) == 1 else lst

# ---------------------------------------------------------------------------
# 8. TVA Amount
# ---------------------------------------------------------------------------

def extract_tva_amount(text: str) -> str:
    money = r'(\d{1,3}(?:[\s.]\d{3})*(?:[,.]\d{2})?)\s*(?:EUR|€)?'
    label_pat = build_label_pattern(SYNONYMS["tva_amount"])
    m = regex.search(rf'(?i)({label_pat})\s*[:=\-–]?\s*{money}', text)
    if m:
        return normalize_money(m.group(2))
    m = re.search(rf'(?i)tva\s+\d+[,.]?\d*\s*%\s*[:=\-–]?\s*{money}', text)
    if m:
        return normalize_money(m.group(1))
    return ""

# ---------------------------------------------------------------------------
# 9. Total Amount
# ---------------------------------------------------------------------------

def extract_total_amount(text: str) -> str:
    money = r'(\d{1,3}(?:[\s.]\d{3})*(?:[,.]\d{2})?)\s*(?:EUR|€)?'
    label_pat = build_label_pattern(SYNONYMS["total_amount"])
    m = regex.search(rf'(?i)({label_pat})\s*[:=\-–]?\s*{money}', text)
    if m:
        return normalize_money(m.group(2))
    return ""

# ---------------------------------------------------------------------------
# 10. Payment Status  (FIXED — card name anywhere = PAID, no context needed)
# ---------------------------------------------------------------------------

def extract_payment_status(text: str) -> str:
    """
    4-signal detection:
    1. Card brand name anywhere in text = PAID (fixed: no strict context required)
    2. French paid keywords (Payé, Réglé, Soldé, Espèces reçues) = PAID
    3. French unpaid keywords (Non payé, En attente, Impayé) = UNPAID
    4. Conditions de règlement = UNKNOWN
    """
    # Signal 1: card brand anywhere = PAID
    if re.search(r'(?i)\b(visa|mastercard|cb\b|carte\s*bleue|american\s*express|amex|carte\s*bancaire)\b', text):
        return "PAID"

    # Signal 2: paid keywords
    if regex.search(r'(?i)\b(pay[eé]|r[eé]gl[eé]|sold[eé]\s+pay[eé]|esp[eè]ces\s+re[çc]ues)\b', text):
        return "PAID"

    # Signal 3: unpaid keywords
    if regex.search(r'(?i)\b(non\s+pay[eé]|en\s+attente|impay[eé])\b', text):
        return "UNPAID"

    # Signal 4: payment conditions mentioned
    if regex.search(r'(?i)conditions\s+de\s+r[eè]glement', text):
        return "UNKNOWN"

    return "UNKNOWN"

# ---------------------------------------------------------------------------
# 11. Solde Du
# ---------------------------------------------------------------------------

def extract_solde_du(text: str) -> str:
    money = r'(\d{1,3}(?:[\s.]\d{3})*(?:[,.]\d{2})?)\s*(?:EUR|€)?'
    label_pat = build_label_pattern(SYNONYMS["solde_du"])
    m = regex.search(rf'(?i)({label_pat})\s*[:=\-–]?\s*{money}', text)
    if m:
        return normalize_money(m.group(2))
    return ""

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def extract_entities(ocr_text: str, file_name: str) -> dict[str, Any]:
    """Extract all 11 entities from OCR text."""
    text = ocr_text.replace("--- PAGE BREAK ---", "\n")
    e = ExtractedEntities(
        file_name=file_name,
        supplier_name=extract_supplier_name(text),
        invoice_number=extract_invoice_number(text),
        invoice_date=extract_invoice_date(text),
        siret=extract_siret(text),
        echeance=extract_echeance(text),
        invoice_content=extract_invoice_content(text),
        tva_percentage=extract_tva_percentage(text),
        tva_amount=extract_tva_amount(text),
        total_amount=extract_total_amount(text),
        payment_status=extract_payment_status(text),
        solde_du=extract_solde_du(text),
    )
    return asdict(e)

def extract_from_ocr_folder(ocr_dir: str | Path, output_dir: str | Path) -> list[dict]:
    ocr_dir = Path(ocr_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    json_files = sorted(f for f in ocr_dir.glob("*.json") if f.name != "ocr_manifest.json")
    if not json_files:
        print(f"[WARNING] No OCR JSON files found in {ocr_dir}")
        return results
    print(f"Found {len(json_files)} OCR files to process...")
    for jf in json_files:
        print(f"Extracting {jf.name}...", end=" ")
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            ocr_text = data.get("full_text", "")
            file_name = data.get("invoice_name", jf.stem)
            entities = extract_entities(ocr_text, file_name)
            results.append(entities)
            (output_dir / jf.name).write_text(
                json.dumps(entities, indent=2, ensure_ascii=False), encoding="utf-8")
            filled = len([k for k, v in entities.items() if v and k != 'file_name'])
            print(f"OK ({filled}/11 fields extracted)")
        except Exception as exc:
            print(f"ERROR: {exc}")
    return results

def _cli() -> None:
    parser = argparse.ArgumentParser(description="Extract 11 entity fields from French invoice OCR text.")
    parser.add_argument("--input", default="outputs/ocr_results")
    parser.add_argument("--output", default="outputs/extracted")
    args = parser.parse_args()
    results = extract_from_ocr_folder(args.input, args.output)
    print(f"\n{'='*60}\nExtraction Complete\n{'='*60}")
    print(f"  Total invoices: {len(results)}\n  Output: {args.output}\n{'='*60}")

if __name__ == "__main__":
    _cli()
