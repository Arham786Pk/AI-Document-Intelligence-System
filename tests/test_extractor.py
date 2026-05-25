"""Tests for Task 8 — Entity extractor.

Smoke tests for the French invoice entity extractor. Tests cover:
  * Individual entity extraction functions
  * Accent tolerance
  * OCR error handling
  * Full entity extraction
  * Batch processing

Run:
    python -m pytest tests/test_extractor.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.extractor import (
    extract_echeance,
    extract_entities,
    extract_from_ocr_folder,
    extract_invoice_date,
    extract_invoice_number,
    extract_payment_status,
    extract_siret,
    extract_solde_du,
    extract_supplier_name,
    extract_total_amount,
    extract_tva_amount,
    extract_tva_percentage,
    make_accent_tolerant,
    normalize_money,
)

# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

def test_make_accent_tolerant():
    """Test accent-tolerant pattern generation."""
    pattern = make_accent_tolerant("échéance")
    assert "[eéèê]" in pattern
    assert "h" in pattern
    
    pattern = make_accent_tolerant("société")
    assert "[oôö]" in pattern
    assert "ci" in pattern or "[eéèê]" in pattern


def test_normalize_money():
    """Test money normalization."""
    assert normalize_money("1 234,56 EUR") == "1234.56"
    assert normalize_money("1.234,56€") == "1234.56"
    assert normalize_money("123,45") == "123.45"
    assert normalize_money("1234.56") == "1234.56"
    assert normalize_money("") == ""


# ---------------------------------------------------------------------------
# Entity extraction tests
# ---------------------------------------------------------------------------

def test_extract_siret():
    """Test SIRET extraction."""
    text = "SIRET : 123 789 456 00178"
    assert extract_siret(text) == "12378945600178"
    
    text = "N° SIRET: 99956789200267"
    assert extract_siret(text) == "99956789200267"
    
    # Without label
    text = "Company info: 33390123400245 - Paris"
    assert extract_siret(text) == "33390123400245"


def test_extract_invoice_date():
    """Test invoice date extraction."""
    text = "Date facture : 12/11/2023"
    assert extract_invoice_date(text) == "12/11/2023"
    
    text = "Émise le 28/04/2025"
    assert extract_invoice_date(text) == "28/04/2025"
    
    # Without accent
    text = "Emise le 19-04-2024"
    assert extract_invoice_date(text) == "19/04/2024"


def test_extract_echeance():
    """Test échéance extraction."""
    text = "Échéance : 27/11/2023"
    assert extract_echeance(text) == "27/11/2023"
    
    # Without accent
    text = "Echeance: 01/05/2024"
    assert extract_echeance(text) == "01/05/2024"
    
    text = "À régler avant le 15/11/2025"
    assert extract_echeance(text) == "15/11/2025"


def test_extract_tva_percentage():
    """Test TVA percentage extraction."""
    text = "TVA 20%"
    result = extract_tva_percentage(text)
    assert result == "20" or result == "20.0"
    
    text = "TVA 5,5%"
    result = extract_tva_percentage(text)
    assert "5.5" in str(result)
    
    # Multiple rates
    text = "TVA 10% : 50 EUR\nTVA 20% : 100 EUR"
    result = extract_tva_percentage(text)
    assert isinstance(result, list)
    assert len(result) == 2


def test_extract_tva_amount():
    """Test TVA amount extraction."""
    text = "Montant TVA : 19,24 EUR"
    assert extract_tva_amount(text) == "19.24"
    
    text = "TVA 5.5% : 672,41€"
    assert extract_tva_amount(text) == "672.41"
    
    text = "Total TVA: 1 309,13"
    assert extract_tva_amount(text) == "1309.13"


def test_extract_total_amount():
    """Test total amount extraction."""
    text = "TOTAL TTC : 369,04 EUR"
    assert extract_total_amount(text) == "369.04"
    
    text = "Net à payer: 4 034,46€"
    assert extract_total_amount(text) == "4034.46"
    
    text = "Montant total : 2.518,81"
    assert extract_total_amount(text) == "2518.81"


def test_extract_payment_status():
    """Test payment status detection."""
    # PAID - card brand
    text = "Payé par Visa **** 1234"
    assert extract_payment_status(text) == "PAID"
    
    text = "Règlement par Carte Bleue"
    assert extract_payment_status(text) == "PAID"
    
    # PAID - keywords
    text = "Facture payée le 12/11/2023"
    assert extract_payment_status(text) == "PAID"
    
    # UNPAID
    text = "Facture non payée"
    assert extract_payment_status(text) == "UNPAID"
    
    # UNKNOWN
    text = "Conditions de règlement: 30 jours"
    assert extract_payment_status(text) == "UNKNOWN"


def test_extract_solde_du():
    """Test solde dû extraction."""
    text = "Solde dû : 4 034,46 EUR"
    assert extract_solde_du(text) == "4034.46"
    
    text = "Reste à payer: 1.500,00€"
    assert extract_solde_du(text) == "1500.00"
    
    # No solde dû
    text = "Total TTC : 369,04 EUR"
    assert extract_solde_du(text) == ""


def test_extract_supplier_name():
    """Test supplier name extraction."""
    text = "Épicerie Fine Marchand\nSIRET: 123456"
    name = extract_supplier_name(text)
    assert "picerie" in name or "Marchand" in name
    
    # With label
    text = "Fournisseur: Garage Mécanique Verdier"
    name = extract_supplier_name(text)
    assert "Garage" in name or "Verdier" in name


def test_extract_invoice_number():
    """Test invoice number extraction."""
    text = "Facture N° EFM-2023-0412"
    number = extract_invoice_number(text)
    assert "EFM" in number or "2023" in number or "0412" in number
    
    text = "N° Facture: ACR-2023-1205"
    number = extract_invoice_number(text)
    assert "ACR" in number or "2023" in number or "1205" in number


# ---------------------------------------------------------------------------
# Full extraction test
# ---------------------------------------------------------------------------

def test_extract_entities_basic():
    """Test full entity extraction on sample text."""
    sample_text = """
    Épicerie Fine Marchand
    SIRET : 12378945600178
    
    Facture N° EFM-2023-0412
    Date : 12/11/2023
    Échéance : 27/11/2023
    
    DÉSIGNATION
    Foie gras mi-cuit
    Confiture artisanale
    
    Montant HT : 349,80 EUR
    TVA 5.5% : 19,24 EUR
    TOTAL TTC : 369,04 EUR
    
    Payé par Visa
    """
    
    entities = extract_entities(sample_text, "test_invoice")
    
    assert entities["file_name"] == "test_invoice"
    assert entities["siret"] == "12378945600178"
    assert "12/11/2023" in entities["invoice_date"]
    assert "27/11/2023" in entities["echeance"]
    assert "5.5" in str(entities["tva_percentage"])
    assert entities["tva_amount"] == "19.24"
    assert entities["total_amount"] == "369.04"
    assert entities["payment_status"] == "PAID"


def test_extract_entities_missing_fields():
    """Test extraction with missing fields."""
    sample_text = """
    Some Company
    Date : 12/11/2023
    Total : 100 EUR
    """
    
    entities = extract_entities(sample_text, "test_invoice")
    
    # Should have all 11 fields, even if empty
    assert "file_name" in entities
    assert "supplier_name" in entities
    assert "invoice_number" in entities
    assert "invoice_date" in entities
    assert "siret" in entities
    assert "echeance" in entities
    assert "invoice_content" in entities
    assert "tva_percentage" in entities
    assert "tva_amount" in entities
    assert "total_amount" in entities
    assert "payment_status" in entities
    assert "solde_du" in entities
    
    # Empty fields should be empty strings, not None
    assert entities["siret"] == ""
    assert entities["echeance"] == ""
    assert entities["payment_status"] in ["PAID", "UNPAID", "UNKNOWN"]


# ---------------------------------------------------------------------------
# Batch processing test
# ---------------------------------------------------------------------------

def test_extract_from_ocr_folder():
    """Test batch extraction from OCR folder."""
    ocr_dir = Path("outputs/ocr_results")
    
    if not ocr_dir.exists():
        pytest.skip(f"OCR results not found: {ocr_dir}")
    
    # Check if there are OCR files
    json_files = [f for f in ocr_dir.glob("*.json") if f.name != "ocr_manifest.json"]
    if not json_files:
        pytest.skip(f"No OCR JSON files in {ocr_dir}")
    
    # Test extraction (use a temp directory)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        results = extract_from_ocr_folder(ocr_dir, tmp_dir)
        
        assert len(results) > 0
        assert all(isinstance(r, dict) for r in results)
        assert all("file_name" in r for r in results)
        
        # Check that output files were created
        output_files = list(Path(tmp_dir).glob("*.json"))
        assert len(output_files) == len(results)


# ---------------------------------------------------------------------------
# Accent tolerance test
# ---------------------------------------------------------------------------

def test_accent_tolerance():
    """Test that extraction works with and without accents."""
    # With accents
    text1 = "Échéance : 27/11/2023"
    result1 = extract_echeance(text1)
    
    # Without accents
    text2 = "Echeance : 27/11/2023"
    result2 = extract_echeance(text2)
    
    assert result1 == result2 == "27/11/2023"
    
    # Mixed
    text3 = "Échéance: 27/11/2023"
    text4 = "Echeance: 27/11/2023"
    assert extract_echeance(text3) == extract_echeance(text4)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_text():
    """Test extraction from empty text."""
    entities = extract_entities("", "empty_invoice")
    
    assert entities["file_name"] == "empty_invoice"
    assert entities["supplier_name"] == ""
    assert entities["siret"] == ""
    assert entities["payment_status"] == "UNKNOWN"


def test_multipage_text():
    """Test extraction from multi-page text with page break markers."""
    text = """
    Page 1 content
    SIRET: 12378945600178
    
    --- PAGE BREAK ---
    
    Page 2 content
    Total TTC: 369,04 EUR
    """
    
    entities = extract_entities(text, "multipage_invoice")
    
    # Should extract from both pages
    assert entities["siret"] == "12378945600178"
    assert entities["total_amount"] == "369.04"
