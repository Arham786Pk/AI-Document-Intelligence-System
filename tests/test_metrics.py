"""Tests for Task 10 — Metrics and summary report module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.metrics import (
    calculate_metrics,
    compare_date,
    compare_field,
    compare_invoice_number,
    compare_money,
    compare_payment_status,
    compare_siret,
    compare_supplier_name,
    compare_tva_percentage,
    generate_report,
    load_ground_truth,
    normalize_date,
    normalize_money,
    normalize_text,
)


# ---------------------------------------------------------------------------
# Normalization tests
# ---------------------------------------------------------------------------

def test_normalize_text():
    """Test text normalization."""
    assert normalize_text("  Hello  World  ") == "hello world"
    assert normalize_text("Test, Inc.") == "test inc"
    assert normalize_text("UPPERCASE") == "uppercase"
    assert normalize_text("") == ""


def test_normalize_money():
    """Test money normalization."""
    assert normalize_money("1 234,56 EUR") == "1234.56"
    assert normalize_money("1234.56") == "1234.56"
    # Note: French format uses comma as decimal, so "1,234.56" is ambiguous
    assert normalize_money("€100") == "100.00"
    assert normalize_money("") == ""


def test_normalize_date():
    """Test date normalization."""
    assert normalize_date("12/11/2023") == "12/11/2023"
    assert normalize_date("12-11-2023") == "12/11/2023"
    assert normalize_date("12.11.2023") == "12/11/2023"
    assert normalize_date("") == ""


# ---------------------------------------------------------------------------
# Comparison tests
# ---------------------------------------------------------------------------

def test_compare_supplier_name():
    """Test supplier name comparison."""
    # Exact match
    assert compare_supplier_name("AOYAMA", "AOYAMA") == True
    
    # Case insensitive
    assert compare_supplier_name("aoyama", "AOYAMA") == True
    
    # Partial match
    assert compare_supplier_name("Epicerie Fine Marchand", "Epicerie Fine") == True
    
    # Word overlap (50% threshold)
    assert compare_supplier_name("Company A", "Company B") == True  # "Company" matches
    assert compare_supplier_name("ABC Corp", "XYZ Inc") == False  # No overlap
    
    # Empty values
    assert compare_supplier_name("", "") == True
    assert compare_supplier_name("Test", "") == False


def test_compare_invoice_number():
    """Test invoice number comparison."""
    assert compare_invoice_number("EFM-2023-0412", "EFM-2023-0412") == True
    assert compare_invoice_number("EFM-2023-0412", "efm-2023-0412") == True  # Case insensitive
    assert compare_invoice_number("ABC123", "XYZ789") == False
    assert compare_invoice_number("", "") == True


def test_compare_date():
    """Test date comparison."""
    assert compare_date("12/11/2023", "12/11/2023") == True
    assert compare_date("12-11-2023", "12/11/2023") == True
    assert compare_date("12.11.2023", "12/11/2023") == True
    assert compare_date("01/01/2023", "02/02/2023") == False
    assert compare_date("", "") == True


def test_compare_siret():
    """Test SIRET comparison."""
    assert compare_siret("12378945600178", "12378945600178") == True
    assert compare_siret("123 789 456 00178", "12378945600178") == True
    assert compare_siret("12345678901234", "98765432109876") == False
    assert compare_siret("", "") == True


def test_compare_money():
    """Test money comparison."""
    assert compare_money("369,04 EUR", "369.04") == True
    assert compare_money("1 234,56", "1234.56") == True
    assert compare_money("100", "200") == False
    assert compare_money("", "") == True


def test_compare_tva_percentage():
    """Test TVA percentage comparison."""
    # Single rate
    assert compare_tva_percentage("20", "20%") == True
    assert compare_tva_percentage("5.5", "5,5%") == True
    
    # Multiple rates
    assert compare_tva_percentage(["10", "20"], "10%; 20%") == True
    assert compare_tva_percentage(["20", "10"], "10%; 20%") == True
    
    # No match
    assert compare_tva_percentage("10", "20%") == False
    assert compare_tva_percentage("", "") == True


def test_compare_payment_status():
    """Test payment status comparison."""
    assert compare_payment_status("PAID", "PAID") == True
    assert compare_payment_status("paid", "PAID") == True
    assert compare_payment_status("UNPAID", "UNPAID") == True
    assert compare_payment_status("UNKNOWN", "UNKNOWN") == True
    assert compare_payment_status("PAID", "UNPAID") == False


# ---------------------------------------------------------------------------
# Ground truth loading tests
# ---------------------------------------------------------------------------

def test_load_ground_truth(tmp_path):
    """Test loading ground truth from CSV."""
    # Create test CSV
    csv_content = """File Name,Supplier Name,Invoice Number,Invoice Date,SIRET,Echeance,Invoice Content,TVA Percentage,TVA Amount,Total Amount,Payment Status,Solde du,Notes
Test_Invoice.pdf,Test Company,INV-001,01/01/2023,12345678901234,15/01/2023,Item 1; Item 2,20%,100.00 EUR,600.00 EUR,PAID,,Test note
"""
    csv_path = tmp_path / "test_ground_truth.csv"
    csv_path.write_text(csv_content, encoding='utf-8')
    
    # Load ground truth
    gt = load_ground_truth(csv_path)
    
    assert len(gt) == 1
    assert "Test_Invoice" in gt
    assert gt["Test_Invoice"]["supplier_name"] == "Test Company"
    assert gt["Test_Invoice"]["invoice_number"] == "INV-001"
    assert gt["Test_Invoice"]["total_amount"] == "600.00 EUR"


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

def test_calculate_metrics_basic(tmp_path):
    """Test basic metrics calculation."""
    # Create test ground truth - use .json extension to match file name
    csv_content = """File Name,Supplier Name,Invoice Number,Invoice Date,SIRET,Echeance,Invoice Content,TVA Percentage,TVA Amount,Total Amount,Payment Status,Solde du,Notes
Test_001,Test Company,INV-001,01/01/2023,12345678901234,15/01/2023,Item 1,20%,100.00 EUR,600.00 EUR,PAID,,
"""
    gt_path = tmp_path / "ground_truth.csv"
    gt_path.write_text(csv_content, encoding='utf-8')
    
    # Create test extracted entity
    extracted_dir = tmp_path / "extracted"
    extracted_dir.mkdir()
    
    extracted_data = {
        "file_name": "Test_001",
        "supplier_name": "Test Company",
        "invoice_number": "INV-001",
        "invoice_date": "01/01/2023",
        "siret": "12345678901234",
        "echeance": "15/01/2023",
        "invoice_content": [{"description": "Item 1", "quantity": "1", "unit_price": "100"}],
        "tva_percentage": "20",
        "tva_amount": "100.00",
        "total_amount": "600.00",
        "payment_status": "PAID",
        "solde_du": ""
    }
    
    extracted_path = extracted_dir / "Test_001.json"
    extracted_path.write_text(json.dumps(extracted_data, indent=2), encoding='utf-8')
    
    # Calculate metrics
    metrics = calculate_metrics(extracted_dir, gt_path)
    
    assert metrics.total_invoices == 1
    assert metrics.overall_accuracy > 80.0  # Should be high for perfect match
    assert len(metrics.field_metrics) == 11
    assert len(metrics.invoice_comparisons) == 1


def test_generate_report(tmp_path):
    """Test report generation."""
    # Create minimal metrics report
    from src.metrics import FieldMetrics, InvoiceComparison, MetricsReport
    
    metrics = MetricsReport(
        total_invoices=1,
        overall_accuracy=90.0,
        field_metrics=[
            FieldMetrics(
                field_name="supplier_name",
                total_invoices=1,
                correct=1,
                incorrect=0,
                missing_in_extracted=0,
                missing_in_ground_truth=0,
                precision=100.0,
                recall=100.0,
                f1_score=100.0,
                accuracy=100.0
            )
        ],
        invoice_comparisons=[
            InvoiceComparison(
                file_name="Test_001",
                matched_fields=9,
                total_fields=10,
                accuracy=90.0,
                field_details={}
            )
        ],
        summary={
            'total_invoices_compared': 1,
            'total_fields_compared': 10,
            'total_fields_matched': 9,
            'overall_accuracy': 90.0,
            'invoices_with_matches': 1,
            'perfect_matches': 0
        }
    )
    
    output_dir = tmp_path / "output"
    generate_report(metrics, output_dir)
    
    # Check that files were created
    assert (output_dir / "metrics_report.json").exists()
    assert (output_dir / "metrics_summary.txt").exists()
    assert (output_dir / "detailed_comparison.csv").exists()


# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
