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

Usage:
    from src.extractor import extract_entities

    entities = extract_entities(ocr_text, "Invoice_FR_016")
    print(entities["supplier_name"])
    print(entities["total_amount"])

    # CLI:
    #   python -m src.extractor --input outputs/ocr_results --output outputs/extracted
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Use regex library for better Unicode support
import regex

# ---------------------------------------------------------------------------
# Synonym patterns (accent-tolerant)
# ---------------------------------------------------------------------------

def make_accent_tolerant(text: str) -> str:
    """Convert text to accent-tolerant regex pattern."""
    replacements = {
        'e': '[eéèê]',
        'a': '[aàâ]',
        'i': '[iîï]',
        'o': '[oôö]',
        'u': '[uùûü]',
        'c': '[cç]',
        'E': '[EÉÈÊ]',
        'A': '[AÀÂ]',
        'I': '[IÎÏ]',
        'O': '[OÔÖ]',
        'U': '[UÙÛ]',
        'C': '[CÇ]',
    }
    result = text
    for char, pattern in replacements.items():
        result = result.replace(char, pattern)
    return result


# Synonym patterns for each entity
SYNONYMS = {
    "supplier_name": ["fournisseur", "societe", "société", "entreprise", "vendor", "emetteur", "émetteur"],
    "invoice_number": ["facture n", "numero de facture", "numéro de facture", "n facture", "no facture", 
                      "ref facture", "référence", "n° de facture", "numéro"],
    "invoice_date": ["date facture", "date d'émission", "date d'emission", "emise le", "émise le", 
                    "facture le", "date de consommation", "date d'impression", "date", "le"],
    "siret": ["siret", "n siret", "n° siret", "identifiant siret"],
    "echeance": ["échéance", "echeance", "date limite de paiement", "date d'échéance", "date d'echeance",
                "à payer avant", "a payer avant", "à régler avant", "a regler avant", "due date"],
    "invoice_content": ["désignation", "designation", "description", "prestations", "articles",
                       "produits et services", "ref article", "référence"],
    "tva_percentage": ["tva", "taux tva", "taxe tva", "% tva", "vat rate"],
    "tva_amount": ["montant tva", "total tva", "taxe", "vat amount", "mt tva"],
    "total_amount": ["total ttc", "net a payer", "net à payer", "montant total", "total facture",
                    "total du", "total dû", "total à payer", "montant ttc"],
    "solde_du": ["solde dû", "solde du", "reste à payer", "reste a payer", "balance due", "montant restant"],
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class LineItem:
    """Single line item from invoice content."""
    description: str
    quantity: str = ""
    unit_price: str = ""


@dataclass
class ExtractedEntities:
    """Extracted entities from a French invoice."""
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
# Helper functions
# ---------------------------------------------------------------------------

def normalize_money(text: str) -> str:
    """Normalize money amount: remove spaces, convert comma to dot."""
    if not text:
        return ""
    # Remove currency symbols and spaces
    text = re.sub(r'[€EUR\s]', '', text, flags=re.IGNORECASE)
    # Convert comma to dot
    text = text.replace(',', '.')
    # Remove thousand separators (dots in French format)
    parts = text.split('.')
    if len(parts) > 2:
        # Multiple dots - last one is decimal separator
        text = ''.join(parts[:-1]) + '.' + parts[-1]
    return text.strip()


def normalize_date(text: str) -> str:
    """Normalize date format."""
    if not text:
        return ""
    # Remove extra spaces
    text = re.sub(r'\s+', '', text)
    return text.strip()


def build_label_pattern(synonyms: list[str]) -> str:
    """Build regex pattern from synonym list (accent-tolerant, case-insensitive)."""
    patterns = [make_accent_tolerant(syn) for syn in synonyms]
    return '|'.join(patterns)


# ---------------------------------------------------------------------------
# Entity extractors
# ---------------------------------------------------------------------------

def extract_supplier_name(text: str) -> str:
    """Extract supplier name from invoice text."""
    # Try labeled match first
    label_pattern = build_label_pattern(SYNONYMS["supplier_name"])
    pattern = rf'(?i)({label_pattern})\s*[:=\-–]?\s*([^\n]+)'
    match = regex.search(pattern, text)
    if match:
        name = match.group(2).strip()
        # Clean up: remove trailing punctuation and address
        name = re.sub(r'[,;.]+$', '', name)
        # Remove postal code and everything after
        name = re.split(r'\b\d{5}\b', name)[0].strip()
        if name and len(name) > 2:
            return name
    
    # Fallback: take first non-empty line that's not "FACTURE" or contains SIRET/TVA
    lines = text.split('\n')
    for line in lines[:15]:  # Check first 15 lines
        line = line.strip()
        # Skip if empty, too short, or contains keywords we want to avoid
        if not line or len(line) < 3:
            continue
        if regex.match(r'(?i)^(facture|siret|tva|n°|date|destinataire)', line):
            continue
        if re.search(r'\d{14}', line):  # Skip lines with SIRET
            continue
        if re.search(r'FR\d{11}', line):  # Skip lines with TVA number
            continue
        
        # Clean up
        line = re.sub(r'[,;.]+$', '', line)
        line = re.split(r'\b\d{5}\b', line)[0].strip()
        if line and len(line) > 2:
            return line
    
    return ""


def extract_invoice_number(text: str) -> str:
    """Extract invoice number."""
    label_pattern = build_label_pattern(SYNONYMS["invoice_number"])
    # Pattern: label followed by alphanumeric code
    # More flexible to catch various formats
    pattern = rf'(?i)({label_pattern})\s*[°:=\-–\s]?\s*([A-Z0-9][A-Z0-9\-/\s]{{3,25}})'
    match = regex.search(pattern, text)
    if match:
        number = match.group(2).strip()
        # Remove excessive whitespace
        number = re.sub(r'\s+', ' ', number)
        # Stop at newline or excessive space
        number = number.split('\n')[0].split('  ')[0]
        return number.strip()
    
    # Try without label - look for patterns like "N° XXXXX" or "Facture XXXXX"
    pattern2 = r'(?i)\b(facture|n°|no|ref)\s+([A-Z0-9][A-Z0-9\-/]{3,20})\b'
    match = re.search(pattern2, text)
    if match:
        return match.group(2).strip()
    
    return ""


def extract_invoice_date(text: str) -> str:
    """Extract invoice date."""
    # Date patterns: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, DD/MM/YY
    date_pattern = r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})\b'
    
    # Try labeled match first
    label_pattern = build_label_pattern(SYNONYMS["invoice_date"])
    pattern = rf'(?i)({label_pattern})\s*[:=\-–]?\s*{date_pattern}'
    match = regex.search(pattern, text)
    if match:
        date = f"{match.group(2)}/{match.group(3)}/{match.group(4)}"
        return normalize_date(date)
    
    # Fallback: first date in top half of document
    lines = text.split('\n')
    top_half = '\n'.join(lines[:len(lines)//2])
    match = re.search(date_pattern, top_half)
    if match:
        date = f"{match.group(1)}/{match.group(2)}/{match.group(3)}"
        return normalize_date(date)
    
    return ""


def extract_siret(text: str) -> str:
    """Extract SIRET (14 digits)."""
    # Pattern: exactly 14 digits with optional spaces in groups of 3-3-3-5
    pattern = r'\b(\d{3})\s?(\d{3})\s?(\d{3})\s?(\d{5})\b'
    
    # Try labeled match first
    label_pattern = build_label_pattern(SYNONYMS["siret"])
    full_pattern = rf'(?i)({label_pattern})\s*[:=\-–]?\s*{pattern}'
    match = regex.search(full_pattern, text)
    if match:
        siret = match.group(2) + match.group(3) + match.group(4) + match.group(5)
        return siret
    
    # Fallback: any 14-digit sequence
    match = re.search(pattern, text)
    if match:
        siret = match.group(1) + match.group(2) + match.group(3) + match.group(4)
        # Verify it's not a TVA number (which starts with FR)
        context = text[max(0, match.start()-10):match.start()]
        if not re.search(r'(?i)tva|fr', context):
            return siret
    
    return ""


def extract_echeance(text: str) -> str:
    """Extract payment due date (échéance)."""
    date_pattern = r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})\b'
    
    label_pattern = build_label_pattern(SYNONYMS["echeance"])
    pattern = rf'(?i)({label_pattern})\s*[:=\-–]?\s*{date_pattern}'
    match = regex.search(pattern, text)
    if match:
        date = f"{match.group(2)}/{match.group(3)}/{match.group(4)}"
        return normalize_date(date)
    
    return ""


def extract_invoice_content(text: str) -> list[dict[str, str]]:
    """Extract line items from invoice."""
    items = []
    
    # Find the line items section
    label_pattern = build_label_pattern(SYNONYMS["invoice_content"])
    header_match = regex.search(rf'(?i)({label_pattern})', text)
    
    if not header_match:
        return items
    
    # Get text after header
    start_pos = header_match.end()
    remaining_text = text[start_pos:]
    
    # Find end of line items (totals section)
    end_markers = [r'(?i)montant\s+ht', r'(?i)total\s+ht', r'(?i)total\s+ttc', r'(?i)sous\s*total']
    end_pos = len(remaining_text)
    for marker in end_markers:
        match = re.search(marker, remaining_text)
        if match:
            end_pos = min(end_pos, match.start())
    
    items_text = remaining_text[:end_pos]
    lines = items_text.split('\n')
    
    # Extract items from lines
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        
        # Skip lines that look like headers or totals
        if regex.match(r'(?i)(qte|quantite|quantity|prix|price|total)', line):
            continue
        
        # Try to extract description, quantity, and price
        # Pattern: description followed by optional quantity and price
        # Quantity: number possibly with x or *
        # Price: number with decimal
        
        # Simple extraction: take the line as description
        # Look for numbers that might be quantity or price
        numbers = re.findall(r'[\d,\.]+', line)
        
        description = line
        quantity = ""
        unit_price = ""
        
        # If we have numbers, try to identify quantity and price
        if numbers:
            # Remove numbers from description
            for num in numbers:
                description = description.replace(num, '', 1)
            description = re.sub(r'[x*×]', '', description).strip()
            description = re.sub(r'\s+', ' ', description)
            
            # Last number is likely the price, second-to-last is quantity
            if len(numbers) >= 2:
                quantity = numbers[-2]
                unit_price = normalize_money(numbers[-1])
            elif len(numbers) == 1:
                unit_price = normalize_money(numbers[0])
        
        if description:
            items.append({
                "description": description.strip(),
                "quantity": quantity,
                "unit_price": unit_price
            })
    
    return items


def extract_tva_percentage(text: str) -> str | list[str]:
    """Extract TVA percentage(s)."""
    # Pattern: number followed by %
    pattern = r'(\d{1,2}(?:[,\.]\d{1,2})?)\s*%'
    
    # Find all TVA percentages
    rates = set()
    
    # Look for "TVA X%" patterns
    tva_pattern = rf'(?i)tva\s+{pattern}'
    for match in re.finditer(tva_pattern, text):
        rate = match.group(1).replace(',', '.')
        rates.add(rate)
    
    # Also look for standalone percentages near "TVA" keyword
    lines = text.split('\n')
    for line in lines:
        if regex.search(r'(?i)tva', line):
            for match in re.finditer(pattern, line):
                rate = match.group(1).replace(',', '.')
                rates.add(rate)
    
    rates_list = sorted(list(rates))
    
    if len(rates_list) == 0:
        return ""
    elif len(rates_list) == 1:
        return rates_list[0]
    else:
        return rates_list


def extract_tva_amount(text: str) -> str:
    """Extract TVA amount."""
    # Money pattern
    money_pattern = r'(\d{1,3}(?:[\s.]\d{3})*(?:[,.]\d{2})?)\s*(?:EUR|€)?'
    
    label_pattern = build_label_pattern(SYNONYMS["tva_amount"])
    pattern = rf'(?i)({label_pattern})\s*[:=\-–]?\s*{money_pattern}'
    match = regex.search(pattern, text)
    if match:
        amount = match.group(2)
        return normalize_money(amount)
    
    # Try simpler pattern: "TVA X.X% : amount"
    pattern2 = rf'(?i)tva\s+\d+[,.]?\d*\s*%\s*[:=\-–]?\s*{money_pattern}'
    match = re.search(pattern2, text)
    if match:
        amount = match.group(1)
        return normalize_money(amount)
    
    return ""


def extract_total_amount(text: str) -> str:
    """Extract total amount (TTC)."""
    money_pattern = r'(\d{1,3}(?:[\s.]\d{3})*(?:[,.]\d{2})?)\s*(?:EUR|€)?'
    
    label_pattern = build_label_pattern(SYNONYMS["total_amount"])
    pattern = rf'(?i)({label_pattern})\s*[:=\-–]?\s*{money_pattern}'
    match = regex.search(pattern, text)
    if match:
        amount = match.group(2)
        return normalize_money(amount)
    
    return ""


def extract_payment_status(text: str) -> str:
    """Extract payment status (PAID/UNPAID/UNKNOWN)."""
    # Priority 1: Card brand names
    card_pattern = r'(?i)\b(visa|mastercard|cb|carte\s*bleue|american\s*express|amex|carte\s*bancaire)\b'
    if re.search(card_pattern, text):
        # Check if it's in a payment context (not just bank details)
        context_pattern = rf'(?i)(r[eé]glement|paiement|pay[eé]\s+par|sold[eé])\s+.*{card_pattern}'
        if regex.search(context_pattern, text):
            return "PAID"
    
    # Priority 2: French paid keywords
    paid_pattern = r'(?i)\b(pay[eé]|r[eé]gl[eé]|sold[eé]\s+pay[eé])\b'
    if regex.search(paid_pattern, text):
        return "PAID"
    
    # Priority 3: French unpaid keywords
    unpaid_pattern = r'(?i)\b(non\s+pay[eé]|en\s+attente|impay[eé])\b'
    if regex.search(unpaid_pattern, text):
        return "UNPAID"
    
    # Priority 4: Check for "Conditions de règlement"
    conditions_pattern = r'(?i)conditions\s+de\s+r[eè]glement'
    if regex.search(conditions_pattern, text):
        return "UNKNOWN"
    
    return "UNKNOWN"


def extract_solde_du(text: str) -> str:
    """Extract remaining balance (solde dû)."""
    money_pattern = r'(\d{1,3}(?:[\s.]\d{3})*(?:[,.]\d{2})?)\s*(?:EUR|€)?'
    
    label_pattern = build_label_pattern(SYNONYMS["solde_du"])
    pattern = rf'(?i)({label_pattern})\s*[:=\-–]?\s*{money_pattern}'
    match = regex.search(pattern, text)
    if match:
        amount = match.group(2)
        return normalize_money(amount)
    
    return ""


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------

def extract_entities(ocr_text: str, file_name: str) -> dict[str, Any]:
    """Extract all 11 entities from OCR text.
    
    Args:
        ocr_text: Full OCR text from invoice (may include page break markers)
        file_name: Original invoice file name
    
    Returns:
        Dictionary with all 11 extracted fields
    """
    # Remove page break markers for unified extraction
    text = ocr_text.replace("--- PAGE BREAK ---", "\n")
    
    entities = ExtractedEntities(
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
    
    return asdict(entities)


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def extract_from_ocr_folder(ocr_dir: str | Path, output_dir: str | Path) -> list[dict]:
    """Extract entities from all OCR JSON files.
    
    Args:
        ocr_dir: Directory containing OCR JSON files (outputs/ocr_results/)
        output_dir: Directory to write extracted entity JSON files
    
    Returns:
        List of extracted entity dictionaries
    """
    ocr_dir = Path(ocr_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    json_files = sorted(ocr_dir.glob("*.json"))
    
    # Skip manifest file
    json_files = [f for f in json_files if f.name != "ocr_manifest.json"]
    
    if not json_files:
        print(f"[WARNING] No OCR JSON files found in {ocr_dir}")
        return results
    
    print(f"Found {len(json_files)} OCR files to process...")
    
    for json_file in json_files:
        print(f"Extracting {json_file.name}...", end=" ")
        
        try:
            # Load OCR result
            ocr_data = json.loads(json_file.read_text(encoding="utf-8"))
            ocr_text = ocr_data.get("full_text", "")
            file_name = ocr_data.get("invoice_name", json_file.stem)
            
            # Extract entities
            entities = extract_entities(ocr_text, file_name)
            results.append(entities)
            
            # Write output
            output_file = output_dir / json_file.name
            output_file.write_text(
                json.dumps(entities, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            
            print(f"OK (extracted {len([k for k, v in entities.items() if v and k != 'file_name'])} fields)")
            
        except Exception as e:
            print(f"ERROR: {e}")
    
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Extract 11 entity fields from French invoice OCR text."
    )
    parser.add_argument(
        "--input",
        default="outputs/ocr_results",
        help="Folder of OCR JSON files (output from Task 7)."
    )
    parser.add_argument(
        "--output",
        default="outputs/extracted",
        help="Folder to write extracted entity JSON files."
    )
    args = parser.parse_args()
    
    results = extract_from_ocr_folder(args.input, args.output)
    
    print(f"\n{'='*60}")
    print(f"Extraction Complete")
    print(f"{'='*60}")
    print(f"  Total invoices: {len(results)}")
    print(f"  Output directory: {args.output}")
    print(f"{'='*60}")


if __name__ == "__main__":
    _cli()
