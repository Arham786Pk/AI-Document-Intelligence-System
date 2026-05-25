# Model Download Instructions

## ✅ Download Link Configured!

The `download_model.py` script has been updated with the Google Drive link to the model files.

---

## 📥 For Teammates: How to Download the Model

### **Option 1: Manual Download (Recommended)**

1. **Open the Google Drive link:**
   ```
   https://drive.google.com/drive/folders/1FVYfMqdNqxY859l3qKEvH9SzI2eL6Aj7?usp=sharing
   ```

2. **Download all 6 files** from the `best` folder:
   - `config.json`
   - `model.safetensors` (480 MB)
   - `preprocessor_config.json`
   - `tokenizer_config.json`
   - `tokenizer.json` (2.2 MB)
   - `training_args.bin`

3. **Place them in your local repository:**
   ```
   AI-Document-Intelligence-System/
   └── models/
       └── layoutlmv3/
           └── best/
               ├── config.json
               ├── model.safetensors          ← Place here
               ├── preprocessor_config.json
               ├── tokenizer_config.json
               ├── tokenizer.json             ← Place here
               └── training_args.bin          ← Place here
   ```

4. **Verify installation:**
   ```bash
   python -c "from src.ai_extractor import LayoutLMv3Extractor; print('Model loaded successfully!')"
   ```

---

### **Option 2: Using gdown (Automated)**

If you want to automate the download:

1. **Install gdown:**
   ```bash
   pip install gdown
   ```

2. **Download the folder:**
   ```bash
   gdown --folder https://drive.google.com/drive/folders/1FVYfMqdNqxY859l3qKEvH9SzI2eL6Aj7?usp=sharing -O models/layoutlmv3/best
   ```

3. **Verify installation:**
   ```bash
   python -c "from src.ai_extractor import LayoutLMv3Extractor; print('Model loaded successfully!')"
   ```

---

### **Option 3: Train the Model Yourself**

If you prefer to train from scratch:

```bash
python src/train_layoutlmv3.py
# Training takes ~2-3 hours on GPU
# Model will be saved to models/layoutlmv3/best/
```

---

## 📋 What Files Are Needed

### **Already in GitHub (small config files):**
- ✅ `config.json` (~2 KB)
- ✅ `tokenizer_config.json` (~1 KB)
- ✅ `preprocessor_config.json` (~1 KB)

### **Need to Download (large model files):**
- ⚠️ `model.safetensors` (480 MB) - The trained model weights
- ⚠️ `tokenizer.json` (2.2 MB) - Tokenizer vocabulary
- ⚠️ `training_args.bin` (4 KB) - Training configuration

**Note:** The small config files are already in the repository, but downloading all 6 files ensures you have everything.

---

## 🎯 Quick Start After Download

Once you have the model files:

### **Test AI Extraction:**
```bash
python -m src.pipeline --from raw --input data/images --output outputs --extractor ai
```

### **Test Hybrid Mode (Recommended):**
```bash
python -m src.pipeline --from raw --input data/images --output outputs --extractor hybrid
```

### **Test Rules Mode (No Model Needed):**
```bash
python -m src.pipeline --from raw --input data/images --output outputs --extractor rules
```

---

## ❓ Troubleshooting

### **Error: "Model file not found"**
- Check that files are in `models/layoutlmv3/best/`
- Verify all 6 files are present
- Check file names match exactly (case-sensitive)

### **Error: "transformers not installed"**
```bash
pip install transformers torch accelerate
```

### **Error: "CUDA out of memory"**
- Use CPU mode (slower but works): The model will automatically use CPU if GPU is not available
- Or reduce batch size in the code

### **Download is slow**
- Google Drive may throttle large downloads
- Try downloading during off-peak hours
- Or use Option 3 (train yourself) if you have a GPU

---

## 📊 Model Information

- **Architecture:** LayoutLMv3 (microsoft/layoutlmv3-base)
- **Task:** Token classification (Named Entity Recognition)
- **Entities:** 12 invoice fields
- **Training Data:** 140 documents (FUNSD format)
- **Performance:** 86.96% macro F1 score
- **Size:** 480 MB (model weights)

---

## 🔗 Links

- **Google Drive:** https://drive.google.com/drive/folders/1FVYfMqdNqxY859l3qKEvH9SzI2eL6Aj7?usp=sharing
- **Repository:** https://github.com/Arham786Pk/AI-Document-Intelligence-System
- **Documentation:** See `MODEL_SETUP.md` for detailed setup instructions

---

**Last Updated:** May 25, 2026  
**Model Version:** M2 Final (86.96% F1)
