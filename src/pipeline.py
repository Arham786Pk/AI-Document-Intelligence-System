"""Full pipeline integration: preprocessing → OCR → extraction.

Chains together all three stages of the document intelligence pipeline:
1. Preprocessing (Task 6): PDF → cleaned page PNGs
2. OCR (Task 7): page PNGs → structured text
3. Extraction (Task 8): text → 5 entities

This module provides both individual stage execution and full end-to-end
pipeline runs with validation and error handling.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from preprocessor import preprocess_document
from ocr_engine import ocr_document, extract_text_digital_pdf, OCRResult
from extractor import extract_entities, ExtractionResult

log = logging.getLogger("pipeline")


@dataclass
class PipelineResult:
    """Result of a full pipeline run on a single document."""
    
    document_name: str
    source_path: Path
    success: bool
    
    # Stage results
    preprocessing_ok: bool = False
    ocr_ok: bool = False
    extraction_ok: bool = False
    
    # Outputs
    page_count: int = 0
    preprocessed_pages: list[Path] = field(default_factory=list)
    ocr_results: list[OCRResult] = field(default_factory=list)
    extraction_result: ExtractionResult | None = None
    
    # Metadata
    avg_ocr_confidence: float = 0.0
    total_text_length: int = 0
    
    # Errors
    error_stage: str | None = None
    error_message: str | None = None
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "document_name": self.document_name,
            "source_path": str(self.source_path),
            "success": self.success,
            "stages": {
                "preprocessing": self.preprocessing_ok,
                "ocr": self.ocr_ok,
                "extraction": self.extraction_ok,
            },
            "outputs": {
                "page_count": self.page_count,
                "preprocessed_pages": [str(p) for p in self.preprocessed_pages],
                "avg_ocr_confidence": round(self.avg_ocr_confidence, 2),
                "total_text_length": self.total_text_length,
            },
            "extracted_entities": {
                "project_id": self.extraction_result.project_id if self.extraction_result else None,
                "supplier": self.extraction_result.supplier if self.extraction_result else None,
                "material": self.extraction_result.material if self.extraction_result else None,
                "quantity": self.extraction_result.quantity if self.extraction_result else None,
                "date": self.extraction_result.date if self.extraction_result else None,
            } if self.extraction_result else None,
            "error": {
                "stage": self.error_stage,
                "message": self.error_message,
            } if self.error_stage else None,
        }


class Pipeline:
    """Full document intelligence pipeline."""
    
    def __init__(
        self,
        processed_dir: Path,
        ocr_output_dir: Path,
        extraction_output_dir: Path,
        fallback_to_paddle: bool = True,
    ):
        """Initialize pipeline with output directories.
        
        Args:
            processed_dir: Where to write preprocessed page PNGs
            ocr_output_dir: Where to write OCR results (txt + json)
            extraction_output_dir: Where to write extraction results (json)
            fallback_to_paddle: Whether to use PaddleOCR fallback for low-confidence Tesseract results
        """
        self.processed_dir = processed_dir
        self.ocr_output_dir = ocr_output_dir
        self.extraction_output_dir = extraction_output_dir
        self.fallback_to_paddle = fallback_to_paddle
        
        # Create output directories
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.ocr_output_dir.mkdir(parents=True, exist_ok=True)
        self.extraction_output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_document(
        self,
        source_path: Path,
        modality: Literal["digital", "scanned"] = "digital",
        language: str | None = None,
    ) -> PipelineResult:
        """Run full pipeline on a single document.
        
        Args:
            source_path: Path to input PDF
            modality: "digital" or "scanned" (determines preprocessing intensity)
            language: "EN" or "FR" (auto-detected from filename if None)
        
        Returns:
            PipelineResult with all stage outputs and metadata
        """
        doc_name = source_path.stem
        result = PipelineResult(
            document_name=doc_name,
            source_path=source_path,
            success=False,
        )
        
        # Auto-detect language from filename if not provided
        if language is None:
            language = "FR" if "_FR_" in doc_name else "EN"
        
        log.info("starting pipeline for %s (modality=%s, language=%s)", doc_name, modality, language)
        
        # Stage 1: Preprocessing
        try:
            log.info("  [1/3] preprocessing...")
            page_paths = preprocess_document(source_path, self.processed_dir, modality=modality)
            result.preprocessed_pages = page_paths
            result.page_count = len(page_paths)
            result.preprocessing_ok = True
            log.info("  ✓ preprocessed %d pages", len(page_paths))
        except Exception as e:
            result.error_stage = "preprocessing"
            result.error_message = str(e)
            log.error("  ✗ preprocessing failed: %s", e)
            return result
        
        # Stage 2: OCR (or direct PDF text extraction for digital docs)
        try:
            if modality == "digital":
                log.info("  [2/3] direct PDF text extraction (digital fast path)...")
                ocr_results = extract_text_digital_pdf(source_path)
            else:
                log.info("  [2/3] OCR...")
                ocr_results = ocr_document(page_paths, fallback_to_paddle=self.fallback_to_paddle)
            result.ocr_results = ocr_results
            result.ocr_ok = True
            
            # Calculate metadata
            if ocr_results:
                result.avg_ocr_confidence = sum(r.avg_confidence for r in ocr_results) / len(ocr_results)
                result.total_text_length = sum(len(r.full_text) for r in ocr_results)
            
            # Save OCR outputs
            self._save_ocr_results(doc_name, ocr_results)
            
            log.info("  ✓ OCR complete (avg confidence: %.1f%%)", result.avg_ocr_confidence)
        except Exception as e:
            result.error_stage = "ocr"
            result.error_message = str(e)
            log.error("  ✗ OCR failed: %s", e)
            return result
        
        # Stage 3: Extraction
        try:
            log.info("  [3/3] extraction...")
            
            # Concatenate all pages' text
            full_text = "\n\n".join(r.full_text for r in ocr_results)
            
            # Extract entities
            extraction_result = extract_entities(full_text, language)
            extraction_result.document_name = doc_name
            result.extraction_result = extraction_result
            result.extraction_ok = True
            
            # Save extraction output
            self._save_extraction_result(extraction_result)
            
            log.info("  ✓ extraction complete")
            log.info(
                "    → project_id=%s, supplier=%s, material=%s, quantity=%s, date=%s",
                extraction_result.project_id or "(none)",
                (extraction_result.supplier[:30] + "...") if extraction_result.supplier and len(extraction_result.supplier) > 30 else extraction_result.supplier or "(none)",
                extraction_result.material or "(none)",
                extraction_result.quantity or "(none)",
                extraction_result.date or "(none)",
            )
        except Exception as e:
            result.error_stage = "extraction"
            result.error_message = str(e)
            log.error("  ✗ extraction failed: %s", e)
            return result
        
        # Success!
        result.success = True
        log.info("✓ pipeline complete for %s", doc_name)
        return result
    
    def _save_ocr_results(self, doc_name: str, results: list[OCRResult]) -> None:
        """Save OCR results in both human-readable and JSON formats."""
        # Human-readable text file
        txt_path = self.ocr_output_dir / f"{doc_name}.txt"
        with txt_path.open("w", encoding="utf-8") as f:
            f.write(f"# OCR Results: {doc_name}\n")
            f.write(f"# Total pages: {len(results)}\n\n")
            for i, result in enumerate(results, start=1):
                f.write(f"{'=' * 80}\n")
                f.write(f"Page {i}: {result.page_path.name}\n")
                f.write(f"Engine: {result.engine}\n")
                f.write(f"Confidence: {result.avg_confidence:.1f}%\n")
                f.write(f"Words: {len(result.words)}\n")
                f.write(f"{'-' * 80}\n")
                f.write(result.full_text)
                f.write("\n\n")
        
        # Structured JSON file
        json_path = self.ocr_output_dir / f"{doc_name}.json"
        json_data = {
            "document_name": doc_name,
            "total_pages": len(results),
            "pages": [
                {
                    "page_number": i,
                    "page_file": result.page_path.name,
                    "engine": result.engine,
                    "avg_confidence": round(result.avg_confidence, 2),
                    "full_text": result.full_text,
                    "word_count": len(result.words),
                    "words": [
                        {
                            "text": w.text,
                            "confidence": round(w.confidence, 2),
                            "bbox": w.bbox,
                        }
                        for w in result.words
                    ],
                }
                for i, result in enumerate(results, start=1)
            ],
        }
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    def _save_extraction_result(self, result: ExtractionResult) -> None:
        """Save extraction result as JSON."""
        output_path = self.extraction_output_dir / f"{result.document_name}.json"
        
        output_data = {
            "document_name": result.document_name,
            "extracted_entities": {
                "project_id": result.project_id,
                "supplier": result.supplier,
                "material": result.material,
                "quantity": result.quantity,
                "date": result.date,
            },
            "all_candidates": [
                {
                    "field": e.field,
                    "value": e.value,
                    "confidence": round(e.confidence, 3),
                    "source": e.source,
                    "raw_text": e.raw_text[:100]  # truncate for readability
                }
                for e in result.entities
            ],
            "notes": result.notes,
        }
        
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
