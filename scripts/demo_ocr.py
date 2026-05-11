"""Demo script for Task 7 OCR engine.

Demonstrates OCR functionality on a sample preprocessed invoice image.
This script can be used to verify Tesseract installation and French language pack.

Usage:
    python scripts/demo_ocr.py
"""
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ocr_engine import ocr_page, ocr_invoice


def demo_single_page():
    """Demo OCR on a single page."""
    print("=" * 60)
    print("Task 7 OCR Engine Demo - Single Page")
    print("=" * 60)
    
    # Find first available preprocessed image
    processed_dir = Path("data/processed")
    
    if not processed_dir.exists():
        print(f"❌ Preprocessed directory not found: {processed_dir}")
        print("   Run Task 6 preprocessor first:")
        print("   python -m src.preprocessor --input data/Images      --output data/processed")
        print("   python -m src.preprocessor --input data/Scanned_PDF --output data/processed")
        return
    
    # Look for any PNG file
    png_files = list(processed_dir.glob("*.png"))
    if not png_files:
        print(f"❌ No PNG files found in {processed_dir}")
        return
    
    sample_image = png_files[0]
    print(f"\n📄 Processing: {sample_image.name}")
    print(f"   Path: {sample_image}")
    
    try:
        result = ocr_page(sample_image, page_index=0)
        
        print(f"\n✅ OCR Complete!")
        print(f"   Engine: {result.engine}")
        print(f"   Confidence: {result.confidence:.1%}")
        print(f"   Characters: {result.char_count:,}")
        print(f"   Words: {result.word_count:,}")
        print(f"   Fallback triggered: {result.fallback_triggered}")
        
        print(f"\n📝 Extracted text (first 500 chars):")
        print("-" * 60)
        print(result.text[:500])
        if len(result.text) > 500:
            print(f"... ({len(result.text) - 500} more characters)")
        print("-" * 60)
        
    except Exception as e:
        print(f"\n❌ OCR failed: {e}")
        print("\nPossible causes:")
        print("  1. Tesseract not installed")
        print("  2. French language pack (fra) not installed")
        print("  3. Image file corrupted")
        print("\nSee README.md Task 5 for installation instructions.")


def demo_invoice_directory():
    """Demo OCR on a complete invoice directory."""
    print("\n" + "=" * 60)
    print("Task 7 OCR Engine Demo - Complete Invoice")
    print("=" * 60)
    
    processed_dir = Path("data/processed")
    
    # Look for invoice directories (subdirectories with page_*.png files)
    invoice_dirs = [
        d for d in processed_dir.iterdir()
        if d.is_dir() and list(d.glob("page_*.png"))
    ]
    
    if not invoice_dirs:
        print(f"\n⚠️  No invoice directories found in {processed_dir}")
        print("   Expected structure: data/processed/<invoice_name>/page_01.png")
        print("   Run Task 6 preprocessor to create this structure.")
        return
    
    sample_invoice = invoice_dirs[0]
    print(f"\n📁 Processing invoice: {sample_invoice.name}")
    
    try:
        result = ocr_invoice(sample_invoice)
        
        if result.error:
            print(f"\n❌ Error: {result.error}")
            return
        
        print(f"\n✅ OCR Complete!")
        print(f"   Pages: {result.page_count}")
        print(f"   Mean confidence: {result.mean_confidence:.1%}")
        print(f"   Total characters: {result.total_char_count:,}")
        print(f"   Total words: {result.total_word_count:,}")
        print(f"   Low quality pages: {len(result.low_quality_pages)}")
        
        print(f"\n📄 Per-page breakdown:")
        for page in result.pages:
            status = "⚠️ LOW" if page.page_index in result.low_quality_pages else "✓"
            fallback = " [PaddleOCR]" if page.fallback_triggered else ""
            print(f"   Page {page.page_index + 1}: {page.confidence:.1%} confidence, "
                  f"{page.char_count:,} chars {status}{fallback}")
        
        print(f"\n📝 Full text (first 800 chars):")
        print("-" * 60)
        print(result.full_text[:800])
        if len(result.full_text) > 800:
            print(f"... ({len(result.full_text) - 800} more characters)")
        print("-" * 60)
        
    except Exception as e:
        print(f"\n❌ OCR failed: {e}")


def check_tesseract():
    """Check if Tesseract is installed with French language pack."""
    print("=" * 60)
    print("Tesseract Installation Check")
    print("=" * 60)
    
    try:
        import pytesseract
        
        # Check Tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")
        
        # Check available languages
        langs = pytesseract.get_languages()
        print(f"✅ Available languages: {', '.join(langs)}")
        
        if 'fra' in langs:
            print("✅ French language pack (fra) is installed")
        else:
            print("❌ French language pack (fra) is NOT installed")
            print("   This is REQUIRED for French invoice OCR")
            print("   See README.md Task 5 for installation instructions")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Tesseract check failed: {e}")
        print("   Tesseract may not be installed or not in PATH")
        return False


if __name__ == "__main__":
    print("\n🚀 Task 7 OCR Engine Demo\n")
    
    # Check Tesseract installation
    if not check_tesseract():
        print("\n⚠️  Please install Tesseract with French language pack before continuing.")
        sys.exit(1)
    
    print("\n")
    
    # Demo single page OCR
    demo_single_page()
    
    # Demo complete invoice OCR
    demo_invoice_directory()
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run full OCR on all invoices:")
    print("     python -m src.ocr_engine --input data/processed --output outputs/ocr")
    print("  2. Proceed to Task 8 (rule-based extractor)")
    print("=" * 60)
