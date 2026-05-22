# Pipeline Usage Guide - Complete Project Execution

## Quick Start - Recommended Commands

### **Option 1: Complete Pipeline with Smart Preprocessing (RECOMMENDED)**
```bash
python -m src.pipeline --input data/processed --output outputs --from processed \
  --raw-sources data/images data/pdf
```
**What it does:**
- ✅ Checks `data/images` and `data/pdf` for new/modified files
- ✅ Preprocesses only new/modified files (skips existing)
- ✅ Runs OCR on all preprocessed images (skips already processed)
- ✅ Extracts entities from all invoices
- ⚡ **Fast**: Skips already processed files

**When to use:** This is the safest and most efficient option for regular use.

---

### **Option 2: Skip Preprocessing Entirely**
```bash
python -m src.pipeline --input data/processed --output outputs --from processed
```
**What it does:**
- ❌ Skips preprocessing
- ✅ Runs OCR (skips already processed)
- ✅ Extracts entities

**When to use:** When you know all files are already preprocessed and you just want to run OCR + extraction.

---

### **Option 3: Just Calculate Metrics**
```bash
python -m src.metrics --extracted outputs/extracted --ground-truth docs/ground_truth.csv --output outputs
```
**What it does:**
- ✅ Compares extracted entities vs ground truth
- ✅ Generates accuracy reports

**When to use:** When everything is already processed and you just want to regenerate the metrics reports.

---

## Detailed Command Reference

### **Preprocessing Only**

```bash
# Smart mode (skip existing files) - DEFAULT
python -m src.preprocessor --input data/images --output data/processed
python -m src.preprocessor --input data/pdf --output data/processed

# Force mode (reprocess everything)
python -m src.preprocessor --input data/images --output data/processed --force
python -m src.preprocessor --input data/pdf --output data/processed --force

# Single file
python -m src.preprocessor --single data/images/FR_invoice_img_real_001.jpg --output data/processed
```

### **OCR Only**

```bash
# Batch OCR (skips already processed)
python -m src.ocr_engine --input data/processed --output outputs/ocr_results

# Single invoice
python -m src.ocr_engine --single data/processed/Invoice_FR_016 --output outputs/ocr_results

# Demo/test
python scripts/demo_ocr.py
```

### **Extraction Only**

```bash
python -m src.extractor --input outputs/ocr_results --output outputs/extracted
```

### **Full Pipeline Options**

```bash
# From preprocessed (with smart preprocessing check)
python -m src.pipeline --input data/processed --output outputs --from processed \
  --raw-sources data/images data/pdf

# From preprocessed (no preprocessing)
python -m src.pipeline --input data/processed --output outputs --from processed

# From raw (full pipeline with preprocessing)
python -m src.pipeline --input data/images --output outputs --from raw

# From OCR results (extraction only)
python -m src.pipeline --input outputs/ocr_results --output outputs --from ocr

# Specific stages only
python -m src.pipeline --input data/processed --output outputs --stages ocr extraction
```

### **Metrics & Reports**

```bash
python -m src.metrics --extracted outputs/extracted --ground-truth docs/ground_truth.csv --output outputs
```

---

## Understanding Skip Logic

### **Preprocessing Skip Logic**
- Compares source file modification time vs output PNG modification time
- **Skips if:** Output exists AND is newer than source
- **Processes if:** Output doesn't exist OR is older than source

### **OCR Skip Logic**
- Compares preprocessed PNG modification time vs OCR JSON modification time
- **Skips if:** JSON exists AND is newer than PNG
- **Processes if:** JSON doesn't exist OR is older than PNG

### **Extraction Skip Logic**
- ❌ No skip logic (always regenerates)
- ⚡ Very fast (rule-based, no ML)

---

## Common Scenarios

### **Scenario 1: First Time Setup**
```bash
# Run complete pipeline
python -m src.pipeline --input data/processed --output outputs --from processed \
  --raw-sources data/images data/pdf

# Calculate metrics
python -m src.metrics --extracted outputs/extracted --ground-truth docs/ground_truth.csv --output outputs
```

### **Scenario 2: Added New Invoices**
```bash
# Add new files to data/images/ or data/pdf/
# Run the same command - only new files will be processed
python -m src.pipeline --input data/processed --output outputs --from processed \
  --raw-sources data/images data/pdf

# Recalculate metrics
python -m src.metrics --extracted outputs/extracted --ground-truth docs/ground_truth.csv --output outputs
```

### **Scenario 3: Modified Source File**
```bash
# If you replace a source file with a newer version:
# 1. The file's modification time will be newer
# 2. Pipeline will automatically reprocess it
python -m src.pipeline --input data/processed --output outputs --from processed \
  --raw-sources data/images data/pdf
```

### **Scenario 4: Force Complete Reprocessing**
```bash
# Reprocess everything from scratch
python -m src.preprocessor --input data/images --output data/processed --force
python -m src.preprocessor --input data/pdf --output data/processed --force
python -m src.ocr_engine --input data/processed --output outputs/ocr_results
python -m src.extractor --input outputs/ocr_results --output outputs/extracted
python -m src.metrics --extracted outputs/extracted --ground-truth docs/ground_truth.csv --output outputs
```

### **Scenario 5: Just Regenerate Reports**
```bash
# Everything already processed, just want new reports
python -m src.metrics --extracted outputs/extracted --ground-truth docs/ground_truth.csv --output outputs
```

---

## Output Files

After running the complete pipeline, you'll have:

```
outputs/
├── ocr_results/
│   ├── FR_invoice_img_real_001.json
│   ├── ... (21 OCR JSON files)
│   └── ocr_manifest.json
├── extracted/
│   ├── FR_invoice_img_real_001.json
│   ├── ... (21 extracted entity JSON files)
├── pipeline_report.json          ← Pipeline execution stats
├── metrics_report.json            ← Complete metrics data
├── metrics_summary.txt            ← Human-readable report
└── detailed_comparison.csv        ← Field-by-field comparison
```

---

## Performance Tips

✅ **Use smart skipping** (default) - saves time on repeated runs  
✅ **Use `--raw-sources`** - automatically handles new files  
✅ **Run metrics separately** - faster iteration when testing extraction logic  
✅ **Use `--from processed`** - most common and efficient starting point  

❌ **Avoid `--force`** unless you really need to reprocess everything  
❌ **Avoid `--from raw`** unless you have a new raw directory  

---

## Troubleshooting

### **Problem: Files not being skipped**
**Solution:** Check file modification times. If you copied files, they may have new timestamps.

### **Problem: Want to force reprocessing**
**Solution:** Use `--force` flag for preprocessing, or delete output files.

### **Problem: Pipeline seems stuck**
**Solution:** Check if Tesseract is installed and French language pack is available.

### **Problem: Low accuracy in metrics**
**Solution:** This is expected for Milestone 1 (rule-based extraction). See metrics report for field-level details.

---

## Summary

**For regular use:**
```bash
python -m src.pipeline --input data/processed --output outputs --from processed \
  --raw-sources data/images data/pdf
```

This single command handles everything intelligently:
- Checks for new/modified files
- Preprocesses only what's needed
- Runs OCR with smart skipping
- Extracts all entities
- Fast and efficient! ⚡
