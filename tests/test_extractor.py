"""Smoke test for entity extractor — tests on known examples."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from extractor import extract_entities  # noqa: E402


def test_material_cert_en():
    """Test extraction on Real_MaterialCert_EN_NST_Inspection."""
    text = """
    INSPECTION CERTIFICATE EN 10204 3.1
    WATANABE TRADING CO., LTD.
    AWS A5.9 ER316LSi
    Norsk Sveiseteknikk as
    P.O. Box 171, 3371 Vikersund, Norway
    Issue Date: 2013.11.05
    Certificate No. EXP1390198
    WEIGHT: 400 Kgs.
    Kuang Tai Metal Industrial Co., Ltd.
    """
    
    result = extract_entities(text, language="EN")
    
    print("Test: Material Certificate EN")
    print(f"  Project ID: {result.project_id}")
    print(f"  Supplier: {result.supplier}")
    print(f"  Material: {result.material}")
    print(f"  Quantity: {result.quantity}")
    print(f"  Date: {result.date}")
    
    assert result.project_id == "EXP1390198", f"Expected EXP1390198, got {result.project_id}"
    assert result.material and "316" in result.material, f"Expected 316 in material, got {result.material}"
    assert result.quantity and "400" in result.quantity, f"Expected 400 in quantity, got {result.quantity}"
    assert result.date == "05/11/2013", f"Expected 05/11/2013, got {result.date}"
    
    print("  ✓ PASS\n")


def test_material_cert_fr():
    """Test extraction on French material certificate."""
    text = """
    Certificat de Réception 3.1 NF EN 10204
    Numéro de certificat : 134822
    La Robinetterie (LRI-Sodime)
    Désignation du matériau: 1.4307 / 304L
    Date d'émission : 23.05.2019
    Article 8185X.38 (TE SMS 38 INOX 304L)
    Dimension: 38 mm
    """
    
    result = extract_entities(text, language="FR")
    
    print("Test: Material Certificate FR")
    print(f"  Project ID: {result.project_id}")
    print(f"  Supplier: {result.supplier}")
    print(f"  Material: {result.material}")
    print(f"  Quantity: {result.quantity}")
    print(f"  Date: {result.date}")
    
    assert result.project_id == "134822", f"Expected 134822, got {result.project_id}"
    assert result.material and ("304" in result.material or "1.4307" in result.material), f"Expected 304 or 1.4307 in material, got {result.material}"
    assert result.date == "23/05/2019", f"Expected 23/05/2019, got {result.date}"
    
    print("  ✓ PASS\n")


def test_synthetic_welding_plan():
    """Test extraction on synthetic welding plan."""
    text = """
    Welding Procedure Specification
    Project: WO-98154
    Supplier: Bazin et Fils
    Material: PVC Sch 80
    Quantity: 287 pcs
    Date: 18/03/2024
    """
    
    result = extract_entities(text, language="FR")
    
    print("Test: Synthetic Welding Plan FR")
    print(f"  Project ID: {result.project_id}")
    print(f"  Supplier: {result.supplier}")
    print(f"  Material: {result.material}")
    print(f"  Quantity: {result.quantity}")
    print(f"  Date: {result.date}")
    
    assert result.project_id == "WO-98154", f"Expected WO-98154, got {result.project_id}"
    assert result.material and "PVC" in result.material, f"Expected PVC in material, got {result.material}"
    assert result.quantity and "287" in result.quantity, f"Expected 287 in quantity, got {result.quantity}"
    assert result.date == "18/03/2024", f"Expected 18/03/2024, got {result.date}"
    
    print("  ✓ PASS\n")


def test_date_formats():
    """Test various date format parsing."""
    test_cases = [
        ("Date: 2025-10-12", "12/10/2025", "ISO"),
        ("Date: 23.05.2019", "23/05/2019", "EU dot"),
        ("Date: 18/03/2024", "18/03/2024", "Slash"),
        ("Date: Mar 29, 2025", "29/03/2025", "EN textual"),
        ("Date: 26.09.18", "26/09/2018", "2-digit year"),
    ]
    
    print("Test: Date Format Parsing")
    for text, expected, format_name in test_cases:
        result = extract_entities(text, language="EN")
        assert result.date == expected, f"{format_name}: Expected {expected}, got {result.date}"
        print(f"  ✓ {format_name}: {text} → {result.date}")
    
    print("  ✓ PASS\n")


def test_quantity_formats():
    """Test quantity extraction with various units."""
    test_cases = [
        ("Weight: 400 Kgs", "400", "kg"),
        ("Quantity: 287 pcs", "287", "pcs"),
        ("Total: 15642 KG", "15642", "kg"),
        ("Amount: 149.58 lbs", "149.58", "lbs"),
        ("Length: 123.32 m", "123.32", "m"),
    ]
    
    print("Test: Quantity Extraction")
    for text, expected_num, expected_unit in test_cases:
        result = extract_entities(text, language="EN")
        assert result.quantity is not None, f"No quantity found in: {text}"
        assert expected_num in result.quantity, f"Expected {expected_num} in {result.quantity}"
        assert expected_unit in result.quantity.lower(), f"Expected {expected_unit} in {result.quantity}"
        print(f"  ✓ {text} → {result.quantity}")
    
    print("  ✓ PASS\n")


if __name__ == "__main__":
    try:
        test_material_cert_en()
        test_material_cert_fr()
        test_synthetic_welding_plan()
        test_date_formats()
        test_quantity_formats()
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
