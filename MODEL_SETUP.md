# Model Setup Instructions

## Overview

The trained LayoutLMv3 model files are **not included in the git repository** due to their large size (480+ MB). This document explains how to obtain and set up the model files for running the AI extraction pipeline.

## Quick Start

You have **two options** to get the model:

### Option 1: Download Pre-trained Model (Recommended)
Download the pre-trained model from the shared storage location.

### Option 2: Train the Model Yourself
Train the model from scratch using the provided training script.

---

## Option 1: Download Pre-trained Model

### Step 1: Download Model Files

**Contact the project maintainer** for the download link to the model files.

The model package includes:
- `model.safetensors` (480 MB) - The trained model weights
- `tokenizer.json` (2.2 MB) - Tokenizer vocabulary
- `training_args.bin` (4 KB) - Training configuration
- `config.json` - Model configuration
- `tokenizer_config.json` - Tokenizer configuration
- `preprocessor_config.json` - Preprocessor configuration

### Step 2: Extract and Place Files

1. Extract the downloaded model files
2. Place them in the following directory structure:

```
AI-Document-Intelligence-System/
└── models/
    └── layoutlmv3/
        └── best/
            ├── model.safetensors          ← Place here
            ├── tokenizer.json             ← Place here
            ├── training_args.bin          ← Place here
            ├── config.json                ← Already in repo
            ├── tokenizer_config.json      ← Already in repo
            └── preprocessor_config.json   ← Already in repo
```

### Step 3: Verify Installation

Run this command to verify the model is correctly installed:

```bash
python -c "from src.ai_extractor import LayoutLMv3Extractor; print('Model loaded successfully!')"
```

If successful, you should see: `Model loaded successfully!`

---

## Option 2: Train the Model Yourself

If you prefer to train the model from scratch or the download link is unavailable:

### Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended, 8GB+ VRAM)
- ~2-3 hours training time

### Training Steps

1. **Ensure you have the FUNSD dataset:**
   ```bash
   ls data/funsd/
   # Should show: train.jsonl, val.jsonl, test.jsonl
   ```

2. **Run the training script:**
   ```bash
   python src/train_layoutlmv3.py
   ```

3. **Monitor training progress:**
   - Training will run for 20 epochs
   - Best model will be saved to `models/layoutlmv3/best/`
   - Expected final F1 score: ~86-87%

4. **Verify the trained model:**
   ```bash
   python -c "from src.ai_extractor import LayoutLMv3Extractor; print('Model loaded successfully!')"
   ```

### Training Configuration

The training script uses these settings:
- **Epochs**: 20
- **Batch size**: 4 (adjust based on GPU memory)
- **Learning rate**: 5e-5
- **Model**: microsoft/layoutlmv3-base
- **Dataset**: FUNSD (140 train, 30 val, 30 test)

---

## Troubleshooting

### Error: "Model file not found"

**Problem**: The model files are missing from `models/layoutlmv3/best/`

**Solution**: 
1. Check if the directory exists: `ls models/layoutlmv3/best/`
2. Verify you've downloaded/trained the model
3. Ensure files are in the correct location

### Error: "CUDA out of memory"

**Problem**: GPU doesn't have enough memory for training

**Solution**:
1. Reduce batch size in `src/train_layoutlmv3.py`:
   ```python
   per_device_train_batch_size=2  # Reduce from 4 to 2
   ```
2. Or train on CPU (slower):
   ```python
   no_cuda=True
   ```

### Error: "Tokenizer files not found"

**Problem**: `tokenizer.json` is missing

**Solution**:
1. Re-download the model package
2. Or retrain the model to regenerate all files

### Model Performance Issues

**Problem**: Model accuracy is lower than expected

**Expected Performance**:
- **Macro F1**: 86.96%
- **Per-entity F1**: See `docs/task10_model_comparison.md`

**Solution**:
1. Verify you're using the correct model checkpoint
2. Check if test data matches training distribution
3. Review `evaluation_results.json` for detailed metrics

---

## Model Information

### Model Details

- **Architecture**: LayoutLMv3 (microsoft/layoutlmv3-base)
- **Task**: Token classification (Named Entity Recognition)
- **Entities**: 12 invoice fields (invoice_number, date, total_amount, etc.)
- **Training Data**: FUNSD dataset (140 documents)
- **Performance**: 86.96% macro F1 score

### File Sizes

| File | Size | Purpose |
|------|------|---------|
| `model.safetensors` | 480 MB | Model weights |
| `tokenizer.json` | 2.2 MB | Tokenizer vocabulary |
| `training_args.bin` | 4 KB | Training config |
| `config.json` | 2 KB | Model config |
| `tokenizer_config.json` | 1 KB | Tokenizer config |
| `preprocessor_config.json` | 1 KB | Preprocessor config |

### Why Not in Git?

GitHub has a 100 MB file size limit. The model file (480 MB) exceeds this limit, so we:
1. Exclude it from git using `.gitignore`
2. Provide download/training instructions instead
3. Keep smaller config files in the repo

---

## Using the Model

Once the model is set up, you can use it in three ways:

### 1. AI Extraction Mode (Best Accuracy)

```python
from src.pipeline import process_invoice

result = process_invoice(
    "data/images/FR_invoice_img_real_001.jpg",
    extractor="ai"
)
print(result)
```

**Performance**: 86.96% F1, ~45 seconds per document

### 2. Hybrid Mode (Recommended)

```python
result = process_invoice(
    "data/images/FR_invoice_img_real_001.jpg",
    extractor="hybrid"
)
```

**Performance**: Best of both worlds, ~53 seconds per document

### 3. Rules-Only Mode (Fastest)

```python
result = process_invoice(
    "data/images/FR_invoice_img_real_001.jpg",
    extractor="rules"
)
```

**Performance**: 67.78% F1, ~0.5 seconds per document

---

## Additional Resources

- **Training Script**: `src/train_layoutlmv3.py`
- **AI Extractor**: `src/ai_extractor.py`
- **Pipeline**: `src/pipeline.py`
- **Model Comparison**: `docs/task10_model_comparison.md`
- **M2 Report**: `M2_COMPLETE_WORKFLOW_REPORT.md`

---

## Support

For questions or issues:
1. Check the troubleshooting section above
2. Review the M2 documentation: `M2_COMPLETE_WORKFLOW_REPORT.md`
3. Contact the project maintainer for the model download link

---

**Last Updated**: May 25, 2026  
**Model Version**: M2 Final (86.96% F1)
