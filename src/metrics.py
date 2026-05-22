"""Task 10 — Metrics and summary report for French invoice extraction.

Compares extracted entities against ground truth and calculates accuracy metrics:
  * Field-level precision, recall, F1 scores
  * Overall accuracy across all invoices
  * Detailed per-invoice comparison
  * Summary report with statistics

Per Milestone 1 spec:
  * Compare all 11 entity fields
  * Handle partial matches (e.g., supplier name variations)
  * Generate comprehensive accuracy report
  * Export results to JSON and human-readable formats

Usage:
    from src.metrics import calculate_metrics, generate_report

    metrics = calculate_metrics(
        extracted_dir="outputs/extracted",
        ground_truth_file="docs/ground_truth.csv"
    )
    
    generate_report(metrics, output_dir="outputs")

    # CLI:
    #   python -m src.metrics --extracted outputs/extracted --ground-truth docs/ground_truth.csv --output outputs
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import regex


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FieldMetrics:
    """Metrics for a single entity field."""
    field_name: str
    total_invoices: int
    correct: int
    incorrect: int
    missing_in_extracted: int
    missing_in_ground_truth: int
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0


@dataclass
class InvoiceComparison:
    """Comparison result for a single invoice."""
    file_name: str
    matched_fields: int
    total_fields: int
    accuracy: float
    field_details: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class MetricsReport:
    """Complete metrics report."""
    total_invoices: int
    overall_accuracy: float
    field_metrics: list[FieldMetrics] = field(default_factory=list)
    invoice_comparisons: list[InvoiceComparison] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Comparison functions
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, remove extra spaces, punctuation)."""
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower().strip()
    # Remove extra whitespace
    text = regex.sub(r'\s+', ' ', text)
    # Remove common punctuation
    text = regex.sub(r'[,;.!?|]', '', text)
    return text


def normalize_money(value: str) -> str:
    """Normalize money values for comparison."""
    if not value:
        return ""
    # Remove spaces, currency symbols
    value = regex.sub(r'[\s€EUR]', '', value, flags=regex.IGNORECASE)
    # Ensure decimal point
    value = value.replace(',', '.')
    try:
        # Convert to float and back to standardize format
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return value


def normalize_date(value: str) -> str:
    """Normalize date values for comparison."""
    if not value:
        return ""
    # Remove spaces and standardize separators
    value = regex.sub(r'\s+', '', value)
    value = value.replace('-', '/').replace('.', '/')
    return value


def compare_supplier_name(extracted: str, ground_truth: str) -> bool:
    """Compare supplier names with fuzzy matching."""
    if not extracted or not ground_truth:
        return extracted == ground_truth
    
    # Normalize both
    ext_norm = normalize_text(extracted)
    gt_norm = normalize_text(ground_truth)
    
    # Exact match
    if ext_norm == gt_norm:
        return True
    
    # Check if one contains the other (for partial matches)
    if ext_norm in gt_norm or gt_norm in ext_norm:
        return True
    
    # Check word overlap (at least 50% of words match)
    ext_words = set(ext_norm.split())
    gt_words = set(gt_norm.split())
    
    if not ext_words or not gt_words:
        return False
    
    overlap = len(ext_words & gt_words)
    min_words = min(len(ext_words), len(gt_words))
    
    return overlap / min_words >= 0.5


def compare_invoice_number(extracted: str, ground_truth: str) -> bool:
    """Compare invoice numbers."""
    if not extracted or not ground_truth:
        return extracted == ground_truth
    
    # Normalize: remove spaces, lowercase
    ext_norm = normalize_text(extracted).replace(' ', '')
    gt_norm = normalize_text(ground_truth).replace(' ', '')
    
    return ext_norm == gt_norm


def compare_date(extracted: str, ground_truth: str) -> bool:
    """Compare dates."""
    if not extracted or not ground_truth:
        return extracted == ground_truth
    
    ext_norm = normalize_date(extracted)
    gt_norm = normalize_date(ground_truth)
    
    return ext_norm == gt_norm


def compare_siret(extracted: str, ground_truth: str) -> bool:
    """Compare SIRET numbers."""
    if not extracted or not ground_truth:
        return extracted == ground_truth
    
    # Remove spaces
    ext_norm = extracted.replace(' ', '')
    gt_norm = ground_truth.replace(' ', '')
    
    return ext_norm == gt_norm


def compare_money(extracted: str, ground_truth: str) -> bool:
    """Compare money amounts."""
    if not extracted or not ground_truth:
        return extracted == ground_truth
    
    ext_norm = normalize_money(extracted)
    gt_norm = normalize_money(ground_truth)
    
    return ext_norm == gt_norm


def compare_tva_percentage(extracted: str | list, ground_truth: str) -> bool:
    """Compare TVA percentages (can be single value or list)."""
    if not extracted or not ground_truth:
        return extracted == ground_truth
    
    # Normalize ground truth
    gt_rates = set()
    if ';' in ground_truth:
        # Multiple rates in ground truth
        for rate in ground_truth.split(';'):
            rate = rate.strip().replace('%', '').replace(',', '.')
            gt_rates.add(rate)
    else:
        rate = ground_truth.strip().replace('%', '').replace(',', '.')
        gt_rates.add(rate)
    
    # Normalize extracted
    ext_rates = set()
    if isinstance(extracted, list):
        for rate in extracted:
            rate = str(rate).strip().replace('%', '').replace(',', '.')
            ext_rates.add(rate)
    else:
        rate = str(extracted).strip().replace('%', '').replace(',', '.')
        ext_rates.add(rate)
    
    return ext_rates == gt_rates


def compare_payment_status(extracted: str, ground_truth: str) -> bool:
    """Compare payment status."""
    if not extracted or not ground_truth:
        return extracted == ground_truth
    
    return extracted.upper() == ground_truth.upper()


def compare_invoice_content(extracted: list, ground_truth: str) -> bool:
    """Compare invoice content (simplified - checks if items were extracted)."""
    # Ground truth format: "Item 1; Item 2; Item 3"
    if not ground_truth or ground_truth.strip() == "":
        return len(extracted) == 0
    
    # Count expected items
    gt_items = [item.strip() for item in ground_truth.split(';') if item.strip()]
    
    # If we extracted roughly the same number of items, consider it a match
    # (detailed line item comparison is complex and out of scope for Milestone 1)
    if len(extracted) == 0 and len(gt_items) > 0:
        return False
    
    # Allow some tolerance (within 50% of expected count)
    if len(gt_items) > 0:
        ratio = len(extracted) / len(gt_items)
        return 0.5 <= ratio <= 2.0
    
    return True


# ---------------------------------------------------------------------------
# Field comparison dispatcher
# ---------------------------------------------------------------------------

FIELD_COMPARATORS = {
    "supplier_name": compare_supplier_name,
    "invoice_number": compare_invoice_number,
    "invoice_date": compare_date,
    "siret": compare_siret,
    "echeance": compare_date,
    "invoice_content": compare_invoice_content,
    "tva_percentage": compare_tva_percentage,
    "tva_amount": compare_money,
    "total_amount": compare_money,
    "payment_status": compare_payment_status,
    "solde_du": compare_money,
}


def compare_field(field_name: str, extracted_value: Any, ground_truth_value: str) -> bool:
    """Compare a single field using the appropriate comparator."""
    comparator = FIELD_COMPARATORS.get(field_name)
    if not comparator:
        # Default: exact match
        return str(extracted_value) == str(ground_truth_value)
    
    return comparator(extracted_value, ground_truth_value)


# ---------------------------------------------------------------------------
# Ground truth loading
# ---------------------------------------------------------------------------

def load_ground_truth(csv_path: str | Path) -> dict[str, dict[str, str]]:
    """Load ground truth from CSV file.
    
    Args:
        csv_path: Path to ground_truth.csv
    
    Returns:
        Dictionary mapping file names to field values
    """
    csv_path = Path(csv_path)
    ground_truth = {}
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            file_name = row.get('File Name', '').strip()
            if not file_name:
                continue
            
            # Normalize file name (remove extension)
            for _ext in ('.jpeg', '.jpg', '.png', '.pdf'):
                file_name = file_name.replace(_ext, '')
            
            # Handle merged invoices (e.g., "IMG-20260507-WA0152.jpg + IMG-20260507-WA0157.jpg")
            if '+' in file_name:
                # Use first file name
                file_name = file_name.split('+')[0].strip()
            
            ground_truth[file_name] = {
                'supplier_name': row.get('Supplier Name', '').strip(),
                'invoice_number': row.get('Invoice Number', '').strip(),
                'invoice_date': row.get('Invoice Date', '').strip(),
                'siret': row.get('SIRET', '').strip(),
                'echeance': row.get('Echeance', '').strip(),
                'invoice_content': row.get('Invoice Content', '').strip(),
                'tva_percentage': row.get('TVA Percentage', '').strip(),
                'tva_amount': row.get('TVA Amount', '').strip(),
                'total_amount': row.get('Total Amount', '').strip(),
                'payment_status': row.get('Payment Status', '').strip(),
                'solde_du': row.get('Solde du', '').strip(),
            }
    
    return ground_truth


# ---------------------------------------------------------------------------
# Metrics calculation
# ---------------------------------------------------------------------------

def compare_invoice(extracted: dict, ground_truth: dict) -> InvoiceComparison:
    """Compare extracted entities with ground truth for a single invoice.
    
    Args:
        extracted: Extracted entity dictionary
        ground_truth: Ground truth dictionary
    
    Returns:
        InvoiceComparison with detailed results
    """
    file_name = extracted.get('file_name', 'unknown')
    field_details = {}
    matched_fields = 0
    total_fields = 0
    
    # Compare each field
    for field_name in FIELD_COMPARATORS.keys():
        extracted_value = extracted.get(field_name, "")
        gt_value = ground_truth.get(field_name, "")
        
        # Skip if both are empty
        if not extracted_value and not gt_value:
            continue
        
        total_fields += 1
        is_match = compare_field(field_name, extracted_value, gt_value)
        
        if is_match:
            matched_fields += 1
        
        field_details[field_name] = {
            'extracted': extracted_value,
            'ground_truth': gt_value,
            'match': is_match
        }
    
    accuracy = (matched_fields / total_fields * 100) if total_fields > 0 else 0.0
    
    return InvoiceComparison(
        file_name=file_name,
        matched_fields=matched_fields,
        total_fields=total_fields,
        accuracy=accuracy,
        field_details=field_details
    )


def calculate_field_metrics(invoice_comparisons: list[InvoiceComparison]) -> list[FieldMetrics]:
    """Calculate per-field metrics across all invoices.
    
    Args:
        invoice_comparisons: List of invoice comparison results
    
    Returns:
        List of FieldMetrics for each field
    """
    field_stats = {}
    
    # Initialize stats for each field
    for field_name in FIELD_COMPARATORS.keys():
        field_stats[field_name] = {
            'correct': 0,
            'incorrect': 0,
            'missing_in_extracted': 0,
            'missing_in_ground_truth': 0,
            'total': 0
        }
    
    # Aggregate stats
    for comparison in invoice_comparisons:
        for field_name, details in comparison.field_details.items():
            stats = field_stats[field_name]
            stats['total'] += 1
            
            extracted = details['extracted']
            ground_truth = details['ground_truth']
            is_match = details['match']
            
            if is_match:
                stats['correct'] += 1
            else:
                stats['incorrect'] += 1
                
                if not extracted and ground_truth:
                    stats['missing_in_extracted'] += 1
                elif extracted and not ground_truth:
                    stats['missing_in_ground_truth'] += 1
    
    # Calculate metrics
    metrics = []
    for field_name, stats in field_stats.items():
        total = stats['total']
        correct = stats['correct']
        incorrect = stats['incorrect']
        
        # True Positives: correct matches
        tp = correct
        # False Positives: extracted but wrong
        fp = stats['incorrect'] - stats['missing_in_extracted']
        # False Negatives: missing in extracted
        fn = stats['missing_in_extracted']
        
        # Calculate precision, recall, F1
        precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        accuracy = (correct / total * 100) if total > 0 else 0.0
        
        metrics.append(FieldMetrics(
            field_name=field_name,
            total_invoices=total,
            correct=correct,
            incorrect=incorrect,
            missing_in_extracted=stats['missing_in_extracted'],
            missing_in_ground_truth=stats['missing_in_ground_truth'],
            precision=precision * 100,
            recall=recall * 100,
            f1_score=f1_score * 100,
            accuracy=accuracy
        ))
    
    return metrics


def calculate_metrics(extracted_dir: str | Path, ground_truth_file: str | Path) -> MetricsReport:
    """Calculate metrics by comparing extracted entities with ground truth.
    
    Args:
        extracted_dir: Directory containing extracted entity JSON files
        ground_truth_file: Path to ground_truth.csv
    
    Returns:
        MetricsReport with complete metrics
    """
    extracted_dir = Path(extracted_dir)
    
    print("\n" + "="*70)
    print("CALCULATING METRICS")
    print("="*70)
    
    # Load ground truth
    print(f"Loading ground truth from {ground_truth_file}...")
    ground_truth = load_ground_truth(ground_truth_file)
    print(f"  Loaded {len(ground_truth)} ground truth entries")
    
    # Load extracted entities
    print(f"\nLoading extracted entities from {extracted_dir}...")
    json_files = sorted(extracted_dir.glob("*.json"))
    
    if not json_files:
        print(f"[WARNING] No extracted JSON files found in {extracted_dir}")
        return MetricsReport(total_invoices=0, overall_accuracy=0.0)
    
    print(f"  Found {len(json_files)} extracted files")
    
    # Compare each invoice
    print("\nComparing invoices...")
    invoice_comparisons = []
    matched_count = 0
    
    for json_file in json_files:
        extracted = json.loads(json_file.read_text(encoding='utf-8'))
        file_name = extracted.get('file_name', json_file.stem)
        
        # Find matching ground truth
        gt = ground_truth.get(file_name)
        
        if not gt:
            print(f"  [WARNING] No ground truth found for {file_name}")
            continue
        
        comparison = compare_invoice(extracted, gt)
        invoice_comparisons.append(comparison)
        
        if comparison.matched_fields > 0:
            matched_count += 1
        
        print(f"  {file_name}: {comparison.matched_fields}/{comparison.total_fields} fields matched ({comparison.accuracy:.1f}%)")
    
    # Calculate field-level metrics
    print("\nCalculating field-level metrics...")
    field_metrics = calculate_field_metrics(invoice_comparisons)
    
    # Calculate overall accuracy
    total_matched = sum(c.matched_fields for c in invoice_comparisons)
    total_fields = sum(c.total_fields for c in invoice_comparisons)
    overall_accuracy = (total_matched / total_fields * 100) if total_fields > 0 else 0.0
    
    # Create summary
    summary = {
        'total_invoices_compared': len(invoice_comparisons),
        'total_fields_compared': total_fields,
        'total_fields_matched': total_matched,
        'overall_accuracy': overall_accuracy,
        'invoices_with_matches': matched_count,
        'perfect_matches': sum(1 for c in invoice_comparisons if c.accuracy == 100.0),
    }
    
    report = MetricsReport(
        total_invoices=len(invoice_comparisons),
        overall_accuracy=overall_accuracy,
        field_metrics=field_metrics,
        invoice_comparisons=invoice_comparisons,
        summary=summary
    )
    
    print("\n" + "="*70)
    print("METRICS CALCULATION COMPLETE")
    print("="*70)
    print(f"Overall Accuracy: {overall_accuracy:.2f}%")
    print(f"Total Invoices: {len(invoice_comparisons)}")
    print(f"Perfect Matches: {summary['perfect_matches']}")
    print("="*70)
    
    return report


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(metrics: MetricsReport, output_dir: str | Path) -> None:
    """Generate comprehensive metrics report.
    
    Args:
        metrics: MetricsReport object
        output_dir: Directory to write report files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("GENERATING REPORTS")
    print("="*70)
    
    # 1. JSON report (complete data)
    json_path = output_dir / "metrics_report.json"
    json_path.write_text(
        json.dumps(asdict(metrics), indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    print(f"[OK] JSON report: {json_path}")
    
    # 2. Human-readable summary report
    summary_path = output_dir / "metrics_summary.txt"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("FRENCH INVOICE EXTRACTION - METRICS REPORT\n")
        f.write("="*70 + "\n\n")
        
        f.write("OVERALL SUMMARY\n")
        f.write("-"*70 + "\n")
        f.write(f"Total Invoices Compared:    {metrics.summary['total_invoices_compared']}\n")
        f.write(f"Total Fields Compared:      {metrics.summary['total_fields_compared']}\n")
        f.write(f"Total Fields Matched:       {metrics.summary['total_fields_matched']}\n")
        f.write(f"Overall Accuracy:           {metrics.overall_accuracy:.2f}%\n")
        f.write(f"Perfect Matches:            {metrics.summary['perfect_matches']}\n")
        f.write(f"Invoices with Matches:      {metrics.summary['invoices_with_matches']}\n")
        f.write("\n")
        
        f.write("FIELD-LEVEL METRICS\n")
        f.write("-"*70 + "\n")
        f.write(f"{'Field':<25} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1':<10}\n")
        f.write("-"*70 + "\n")
        
        for fm in metrics.field_metrics:
            f.write(f"{fm.field_name:<25} {fm.accuracy:>7.2f}%  {fm.precision:>7.2f}%  {fm.recall:>7.2f}%  {fm.f1_score:>7.2f}%\n")
        
        f.write("\n")
        f.write("DETAILED FIELD STATISTICS\n")
        f.write("-"*70 + "\n")
        
        for fm in metrics.field_metrics:
            f.write(f"\n{fm.field_name}:\n")
            f.write(f"  Total invoices:           {fm.total_invoices}\n")
            f.write(f"  Correct:                  {fm.correct}\n")
            f.write(f"  Incorrect:                {fm.incorrect}\n")
            f.write(f"  Missing in extracted:     {fm.missing_in_extracted}\n")
            f.write(f"  Missing in ground truth:  {fm.missing_in_ground_truth}\n")
            f.write(f"  Accuracy:                 {fm.accuracy:.2f}%\n")
        
        f.write("\n")
        f.write("PER-INVOICE ACCURACY\n")
        f.write("-"*70 + "\n")
        f.write(f"{'Invoice':<50} {'Matched':<10} {'Accuracy':<10}\n")
        f.write("-"*70 + "\n")
        
        for comp in sorted(metrics.invoice_comparisons, key=lambda x: x.accuracy, reverse=True):
            f.write(f"{comp.file_name:<50} {comp.matched_fields}/{comp.total_fields:<8} {comp.accuracy:>6.1f}%\n")
        
        f.write("\n" + "="*70 + "\n")
    
    print(f"[OK] Summary report: {summary_path}")
    
    # 3. Detailed comparison CSV
    csv_path = output_dir / "detailed_comparison.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Invoice', 'Field', 'Extracted', 'Ground Truth', 'Match'])
        
        for comp in metrics.invoice_comparisons:
            for field_name, details in comp.field_details.items():
                writer.writerow([
                    comp.file_name,
                    field_name,
                    str(details['extracted']),
                    str(details['ground_truth']),
                    'YES' if details['match'] else 'NO'
                ])
    
    print(f"[OK] Detailed comparison: {csv_path}")
    print("="*70)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate metrics and generate summary report for French invoice extraction."
    )
    parser.add_argument(
        "--extracted",
        default="outputs/extracted",
        help="Directory containing extracted entity JSON files"
    )
    parser.add_argument(
        "--ground-truth",
        default="docs/ground_truth.csv",
        help="Path to ground truth CSV file"
    )
    parser.add_argument(
        "--output",
        default="outputs",
        help="Directory to write metrics reports"
    )
    
    args = parser.parse_args()
    
    # Calculate metrics
    metrics = calculate_metrics(args.extracted, args.ground_truth)
    
    # Generate reports
    generate_report(metrics, args.output)
    
    print("\n[OK] Task 10 complete!")


if __name__ == "__main__":
    _cli()
