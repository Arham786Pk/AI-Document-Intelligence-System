"""Convenient entry point for running the French invoice processing pipeline.

This is a simple wrapper around src/pipeline.py that provides an easy-to-use
interface for running the complete pipeline.

Usage:
    # Run from preprocessed images (most common)
    python src/run.py

    # Run from raw invoices (full pipeline)
    python src/run.py --from raw --input data/pdf
    python src/run.py --from raw --input data/images

    # Run from OCR results (extraction only)
    python src/run.py --from ocr --input outputs/ocr_results

    # Custom input/output
    python src/run.py --input data/processed --output my_outputs
"""
from src.pipeline import _cli

if __name__ == "__main__":
    _cli()
