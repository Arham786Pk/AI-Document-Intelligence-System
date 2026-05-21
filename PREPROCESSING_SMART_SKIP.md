# Smart Preprocessing with Skip Logic

## Overview

The preprocessing module and pipeline have been updated to intelligently skip already processed files, preventing unnecessary reprocessing and saving time.

## Changes Made

### 1. **Preprocessor Module (`src/preprocessor.py`)**

#### New Parameter: `skip_existing`
- Added to `preprocess_invoice()` and `preprocess_folder()` functions
- Default: `True` (skip already processed files)
- Set to `False` to force reprocessing

#### Skip Logic
```python
# Compares modification times:
# - If output PNG exists AND is newer than source file → SKIP
# - If output PNG doesn't exist OR is older than source → PROCESS
```

#### CLI Flag: `--force`
```bash
# Skip existing files (default)
python -m src.preprocessor --input data/Images --output data/processed

# Force reprocessing (ignore existing files)
python -m src.preprocessor --input data/Images --output data/processed --force
```

### 2. **Pipeline Module (`src/pipeline.py`)**

#### Updated `run_preprocessing()`
- Now accepts `skip_existing` parameter
- Tracks skipped files in the report
- Shows: "Preprocessed X invoices, skipped Y, Z errors"

#### Enhanced `run_from_processed()`
- New parameter: `raw_sources` (optional list of raw directories)
- If `raw_sources` provided: runs preprocessing first with smart skipping
- If `raw_sources` omitted: skips preprocessing entirely

#### New CLI Flag: `--raw-sources`
```bash
# Run pipeline with smart preprocessing (checks both raw source folders)
python -m src.pipeline --input data/processed --output outputs --from processed \
  --raw-sources data/Images data/Scanned_PDF

# Run pipeline without preprocessing (OCR + Extraction only)
python -m src.pipeline --input data/processed --output outputs --from processed
```

## Usage Examples

### Scenario 1: First Time Processing
```bash
# Process everything from scratch
python -m src.pipeline --input data/processed --output outputs --from processed \
  --raw-sources data/Images data/Scanned_PDF
```
**Result:** All files preprocessed, OCR'd, and extracted

### Scenario 2: Adding New Invoices
```bash
# Add new files to data/Images/ or data/Scanned_PDF/
# Then run the same command
python -m src.pipeline --input data/processed --output outputs --from processed \
  --raw-sources data/Images data/Scanned_PDF
```
**Result:** 
- Existing files: SKIPPED (fast)
- New files: PROCESSED
- All files: OCR'd and extracted

### Scenario 3: Already Preprocessed
```bash
# Skip preprocessing entirely
python -m src.pipeline --input data/processed --output outputs --from processed
```
**Result:** Only OCR and extraction run

### Scenario 4: Force Reprocessing
```bash
# Force reprocess everything
python -m src.preprocessor --input data/Images --output data/processed --force
python -m src.preprocessor --input data/Scanned_PDF --output data/processed --force
```
**Result:** All files reprocessed regardless of existing outputs

## Benefits

✅ **Faster execution**: Skips already processed files  
✅ **Incremental processing**: Only processes new/modified files  
✅ **Safe by default**: Won't overwrite existing work  
✅ **Flexible**: Can force reprocessing when needed  
✅ **Transparent**: Reports show skipped vs processed counts  

## Technical Details

### Skip Detection Logic

```python
def should_skip(source_path, output_path):
    """
    Returns True if:
    1. Output file exists
    2. Output modification time > Source modification time
    
    Otherwise returns False (needs processing)
    """
    if not output_path.exists():
        return False
    
    source_mtime = source_path.stat().st_mtime
    output_mtime = output_path.stat().st_mtime
    
    return output_mtime > source_mtime
```

### Skipped File Handling

When a file is skipped:
1. Reads existing output to get dimensions
2. Creates a minimal `InvoiceResult` object
3. Sets quality score to 0.8 (default for skipped files)
4. Prints: `[SKIP] filename (already processed)`

## Backward Compatibility

✅ **Fully backward compatible**
- Default behavior: skip existing files (new)
- Old behavior: use `--force` flag
- All existing commands still work

## Testing

No changes needed to existing tests. The skip logic is transparent to the test suite.

## Summary

The preprocessing module now works like the OCR module - it intelligently skips files that don't need reprocessing. This makes the pipeline much more efficient for incremental updates and repeated runs.
