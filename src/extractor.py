"""Rule-based entity extractor for Milestone 1.

Extracts 5 structured fields (project_id, supplier, material, quantity, date)
from OCR text using regex patterns and keyword triggers defined in
docs/entity_schema.md.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

log = logging.getLogger(__name__)

# Entity field types
EntityType = Literal["project_id", "supplier", "material", "quantity", "date"]


@dataclass
class ExtractedEntity:
    """Single extracted entity with metadata."""
    field: EntityType
    value: str
    confidence: float  # 0.0-1.0
    source: str  # which pattern/trigger matched
    raw_text: str  # original text before normalization


@dataclass
class ExtractionResult:
    """Complete extraction result for one document."""
    document_name: str
    project_id: str | None
    supplier: str | None
    material: str | None
    quantity: str | None
    date: str | None
    entities: list[ExtractedEntity]  # all candidates found
    notes: list[str]  # warnings, ambiguities


# ============================================================================
# PROJECT ID PATTERNS
# ============================================================================

PROJECT_ID_PATTERNS = [
    # Certificate numbers (EN 10204) - with trigger words (French and English)
    (r'(?i)(?:numéro\s+de\s+certificat|certificat|certificate|certif\.?)\s*(?:n°|no\.?|number|nb|#)?\s*:?\s*(\d{5,9})', 0.95, "cert_trigger"),
    
    # Certificate numbers standalone
    (r'\b(?:EXP|CERT)\s*\d{5,9}\b', 0.9, "cert_number"),
    
    # Standard project codes
    (r'\b(?:PRJ|PROJ|WO|JOB|WLD|FAB|PO)[-_ ]?\d{2,7}\b', 0.85, "project_code"),
    
    # WPS / procedure numbers
    (r'\b(?:WPS|SS)[-_ ]?\d{2,5}(?:[-_ ]?R\d+)?\b', 0.8, "wps_code"),
    
    # Generic reference numbers
    (r'(?i)(?:reference|ref\.?|réf\.?|n°\s*commande)\s*:?\s*([A-Z]{2,4}[-_ ]?\d{2,7})', 0.75, "ref_trigger"),
]


# ============================================================================
# SUPPLIER PATTERNS
# ============================================================================

SUPPLIER_TRIGGERS_EN = [
    "supplier", "vendor", "from", "seller", "issued by", "manufacturer",
    "shipped from", "ship from", "produced by"
]

SUPPLIER_TRIGGERS_FR = [
    "fournisseur", "émis par", "émetteur", "fabricant", "producteur", "de"
]

CORPORATE_SUFFIXES = [
    "Ltd", "Ltd.", "LLC", "Inc.", "Group", "Co.", "Corp.", "GmbH", "AG",
    "SA", "SARL", "S.A.S.", "SAS", "Aciéries", "Steel Mills", "Pvt.",
    "Private Limited", "et Fils", "Industries", "Industrial"
]


# ============================================================================
# MATERIAL PATTERNS
# ============================================================================

MATERIAL_PATTERNS = [
    # AWS filler codes
    (r'\bAWS\s+A\d\.\d+\s+[A-Z0-9-]+\b', 0.9, "aws_code"),
    
    # Common steel grades
    (r'\b(?:SS\s?\d{3}L?|304L?|316L?|2205|S\d{3}[A-Z0-9\+]+)\b', 0.85, "steel_grade"),
    
    # European steel numbers
    (r'\b1\.\d{4}\b', 0.85, "eu_steel_number"),
    
    # ASTM grades
    (r'\bA\d{1,3}(?:\s*Gr\.?\s*[A-Z0-9]+)?\b', 0.8, "astm_grade"),
    
    # Aluminum grades
    (r'\b6061-T6\b', 0.9, "aluminum_grade"),
    
    # Named alloys
    (r'\b(?:Duplex|Monel|Hastelloy|Inconel|Hardox)\s*\d{3,4}\b', 0.85, "named_alloy"),
    
    # Material descriptors
    (r'\b(?:Carbon\s+Steel|Stainless\s+Steel|Galvanized\s+Steel|Copper|PVC\s+Sch\s*\d+|Inox\s+\d{3}L?)\b', 0.75, "material_descriptor"),
]

MATERIAL_TRIGGERS_EN = [
    "material", "material type", "material spec", "base material", "grade",
    "commodity", "description", "filler metal", "steel", "designation"
]

MATERIAL_TRIGGERS_FR = [
    "matière", "matériau", "type de matériau", "désignation du matériau",
    "désignation", "nuance", "désign. acier", "métal de base"
]


# ============================================================================
# QUANTITY PATTERNS
# ============================================================================

QUANTITY_PATTERN = r'\b(\d{1,6}(?:[.,]\d{1,3})?)\s*(pcs|pieces|units|kg|kgs|lbs|tons|tonnes|metres?|mm|m)\b'

QUANTITY_TRIGGERS_EN = [
    "quantity", "qty", "weight", "total weight", "gross weight", "net weight",
    "amount", "total", "masse"
]

QUANTITY_TRIGGERS_FR = [
    "quantité", "qté", "poids", "poids net", "poids total", "masse",
    "masse théorique", "masse effective", "nombre", "unités"
]


# ============================================================================
# DATE PATTERNS
# ============================================================================

DATE_PATTERNS = [
    # ISO format: YYYY-MM-DD
    (r'\b(\d{4})-(\d{2})-(\d{2})\b', 0.95, "iso"),
    
    # ISO-like with dots: YYYY.MM.DD
    (r'\b(\d{4})\.(\d{2})\.(\d{2})\b', 0.95, "iso_dot"),
    
    # European dot: DD.MM.YYYY or DD.MM.YY
    (r'\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b', 0.85, "eu_dot"),
    
    # Slash format: DD/MM/YYYY or DD/MM/YY
    (r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b', 0.8, "slash"),
    
    # English textual: Mar 29, 2025
    (r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{2,4})\b', 0.9, "en_textual"),
    
    # French textual: 29 mars 2025
    (r'\b(\d{1,2})\s+(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)[a-zé]*\s+(\d{2,4})\b', 0.9, "fr_textual"),
]

DATE_TRIGGERS_EN = [
    "date", "issue date", "invoice date", "date of sale", "effective",
    "mfg. date", "shipped", "report date"
]

DATE_TRIGGERS_FR = [
    "date", "date d'émission", "date d'expédition", "date de facture",
    "date d'essai", "date de fabrication"
]

MONTH_MAP_EN = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

MONTH_MAP_FR = {
    "janv": 1, "févr": 2, "mars": 3, "avr": 4, "mai": 5, "juin": 6,
    "juil": 7, "août": 8, "sept": 9, "oct": 10, "nov": 11, "déc": 12
}


# ============================================================================
# EXTRACTION FUNCTIONS
# ============================================================================

def extract_project_id(text: str) -> list[ExtractedEntity]:
    """Extract project ID / certificate number."""
    candidates = []
    text_lower = text.lower()
    
    for pattern, confidence, source in PROJECT_ID_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = match.group(1) if match.lastindex else match.group(0)
            value = value.strip().upper()
            
            # Skip if it looks like a year or phone number
            if re.match(r'^\d{4}$', value) or len(value) > 15:
                continue
            
            candidates.append(ExtractedEntity(
                field="project_id",
                value=value,
                confidence=confidence,
                source=source,
                raw_text=match.group(0)
            ))
    
    return candidates


def extract_supplier(text: str) -> list[ExtractedEntity]:
    """Extract supplier name."""
    candidates = []
    lines = text.split('\n')
    
    # Look for trigger words
    all_triggers = SUPPLIER_TRIGGERS_EN + SUPPLIER_TRIGGERS_FR
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        for trigger in all_triggers:
            if trigger in line_lower:
                # Check next few lines for company name
                for j in range(i, min(i + 3, len(lines))):
                    candidate_line = lines[j].strip()
                    
                    # Skip the trigger line itself if it's just the label
                    if candidate_line.lower() == trigger or len(candidate_line) < 3:
                        continue
                    
                    # Look for corporate suffixes
                    for suffix in CORPORATE_SUFFIXES:
                        if suffix in candidate_line:
                            # Clean up the name
                            value = candidate_line.strip()
                            value = re.sub(r'\s+', ' ', value)  # collapse spaces
                            
                            candidates.append(ExtractedEntity(
                                field="supplier",
                                value=value,
                                confidence=0.8,
                                source=f"trigger_{trigger}",
                                raw_text=candidate_line
                            ))
                            break
    
    # Fallback: look for company names in first 20% of text (letterhead)
    header_text = ' '.join(lines[:max(5, len(lines) // 5)])
    for suffix in CORPORATE_SUFFIXES:
        pattern = rf'\b([A-Z][A-Za-z\s,\.&-]+{re.escape(suffix)}\.?)\b'
        for match in re.finditer(pattern, header_text):
            value = match.group(1).strip()
            value = re.sub(r'\s+', ' ', value)
            
            # Skip if it's a customer name (common false positive)
            if any(x in value.lower() for x in ["customer", "client", "watanabe", "trading co"]):
                continue
            
            candidates.append(ExtractedEntity(
                field="supplier",
                value=value,
                confidence=0.6,
                source="letterhead",
                raw_text=match.group(0)
            ))
    
    return candidates


def extract_material(text: str) -> list[ExtractedEntity]:
    """Extract material type / grade."""
    candidates = []
    
    # Pattern-based extraction
    for pattern, confidence, source in MATERIAL_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = match.group(0).strip()
            
            # Normalize spacing
            value = re.sub(r'\s+', ' ', value)
            
            candidates.append(ExtractedEntity(
                field="material",
                value=value,
                confidence=confidence,
                source=source,
                raw_text=match.group(0)
            ))
    
    # Trigger-based extraction
    all_triggers = MATERIAL_TRIGGERS_EN + MATERIAL_TRIGGERS_FR
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        for trigger in all_triggers:
            if trigger in line_lower:
                # Extract value after trigger
                parts = re.split(r'[:=\-]', line, maxsplit=1)
                if len(parts) == 2:
                    value = parts[1].strip()
                    # Take first meaningful token
                    value = re.split(r'[,;\n]', value)[0].strip()
                    
                    if len(value) > 2 and len(value) < 100:
                        candidates.append(ExtractedEntity(
                            field="material",
                            value=value,
                            confidence=0.7,
                            source=f"trigger_{trigger}",
                            raw_text=line
                        ))
    
    return candidates


def extract_quantity(text: str) -> list[ExtractedEntity]:
    """Extract quantity with unit."""
    candidates = []
    
    # Pattern-based extraction
    for match in re.finditer(QUANTITY_PATTERN, text, re.IGNORECASE):
        number = match.group(1).replace(',', '.')  # normalize decimal
        unit = match.group(2).lower()
        value = f"{number} {unit}"
        
        # Check if near a trigger word (within 50 chars)
        context_start = max(0, match.start() - 50)
        context = text[context_start:match.end()].lower()
        
        confidence = 0.7
        source = "pattern"
        
        all_triggers = QUANTITY_TRIGGERS_EN + QUANTITY_TRIGGERS_FR
        for trigger in all_triggers:
            if trigger in context:
                confidence = 0.85
                source = f"trigger_{trigger}"
                break
        
        candidates.append(ExtractedEntity(
            field="quantity",
            value=value,
            confidence=confidence,
            source=source,
            raw_text=match.group(0)
        ))
    
    return candidates


def normalize_date(day: int, month: int, year: int) -> str:
    """Normalize date to ISO format YYYY-MM-DD."""
    # Handle 2-digit years
    if year < 50:
        year += 2000
    elif year < 100:
        year += 1900
    
    try:
        dt = datetime(year, month, day)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return f"{year:04d}-{month:02d}-{day:02d}"  # return as-is if invalid


def extract_date(text: str, language: str = "EN") -> list[ExtractedEntity]:
    """Extract and normalize dates."""
    candidates = []
    
    for pattern, confidence, source in DATE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                if source == "iso":
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    value = normalize_date(day, month, year)
                
                elif source == "iso_dot":
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    value = normalize_date(day, month, year)
                
                elif source in ["eu_dot", "slash"]:
                    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    value = normalize_date(day, month, year)
                
                elif source == "en_textual":
                    month_str = match.group(1).lower()[:3]
                    month = MONTH_MAP_EN.get(month_str, 1)
                    day = int(match.group(2))
                    year = int(match.group(3))
                    value = normalize_date(day, month, year)
                
                elif source == "fr_textual":
                    day = int(match.group(1))
                    month_str = match.group(2).lower()[:4]
                    month = MONTH_MAP_FR.get(month_str, 1)
                    year = int(match.group(3))
                    value = normalize_date(day, month, year)
                
                else:
                    continue
                
                # Check if near a trigger word
                context_start = max(0, match.start() - 30)
                context = text[context_start:match.end()].lower()
                
                all_triggers = DATE_TRIGGERS_EN + DATE_TRIGGERS_FR
                for trigger in all_triggers:
                    if trigger in context:
                        confidence = min(confidence + 0.1, 1.0)
                        break
                
                candidates.append(ExtractedEntity(
                    field="date",
                    value=value,
                    confidence=confidence,
                    source=source,
                    raw_text=match.group(0)
                ))
            
            except (ValueError, IndexError) as e:
                log.debug("failed to parse date %s: %s", match.group(0), e)
                continue
    
    return candidates


def select_best_candidate(candidates: list[ExtractedEntity]) -> ExtractedEntity | None:
    """Select the best candidate from a list based on confidence."""
    if not candidates:
        return None
    
    # Remove duplicates (same value)
    seen = {}
    for c in candidates:
        if c.value not in seen or c.confidence > seen[c.value].confidence:
            seen[c.value] = c
    
    unique_candidates = list(seen.values())
    
    # Sort by confidence
    unique_candidates.sort(key=lambda x: x.confidence, reverse=True)
    
    return unique_candidates[0]


def extract_entities(text: str, language: str = "EN") -> ExtractionResult:
    """Extract all 5 entities from OCR text.
    
    Args:
        text: Full OCR text from document (all pages concatenated)
        language: Document language (EN or FR) for language-specific patterns
    
    Returns:
        ExtractionResult with best candidate for each field
    """
    # Extract all candidates
    project_id_candidates = extract_project_id(text)
    supplier_candidates = extract_supplier(text)
    material_candidates = extract_material(text)
    quantity_candidates = extract_quantity(text)
    date_candidates = extract_date(text, language)
    
    # Select best for each field
    best_project_id = select_best_candidate(project_id_candidates)
    best_supplier = select_best_candidate(supplier_candidates)
    best_material = select_best_candidate(material_candidates)
    best_quantity = select_best_candidate(quantity_candidates)
    best_date = select_best_candidate(date_candidates)
    
    # Collect all entities
    all_entities = (
        project_id_candidates +
        supplier_candidates +
        material_candidates +
        quantity_candidates +
        date_candidates
    )
    
    # Generate notes
    notes = []
    if len(project_id_candidates) > 1:
        notes.append(f"Multiple project IDs found ({len(project_id_candidates)}), selected highest confidence")
    if len(supplier_candidates) > 1:
        notes.append(f"Multiple suppliers found ({len(supplier_candidates)}), selected highest confidence")
    if not best_project_id:
        notes.append("No project ID found")
    if not best_supplier:
        notes.append("No supplier found")
    
    return ExtractionResult(
        document_name="",  # filled by caller
        project_id=best_project_id.value if best_project_id else None,
        supplier=best_supplier.value if best_supplier else None,
        material=best_material.value if best_material else None,
        quantity=best_quantity.value if best_quantity else None,
        date=best_date.value if best_date else None,
        entities=all_entities,
        notes=notes
    )
