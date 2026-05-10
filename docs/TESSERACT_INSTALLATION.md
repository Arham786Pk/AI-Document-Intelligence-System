# Tesseract OCR Installation Guide

**Required for Task 7 (OCR Engine)**

Tesseract OCR with the French language pack (`fra`) is **mandatory** for the French invoice OCR engine to work correctly.

---

## Windows Installation

### Step 1: Download Tesseract Installer

1. Go to: https://github.com/UB-Mannheim/tesseract/wiki
2. Download the latest installer (e.g., `tesseract-ocr-w64-setup-5.3.3.20231005.exe`)
3. Run the installer

### Step 2: Install with French Language Pack

**IMPORTANT:** During installation:

1. When you reach the "Choose Components" screen
2. **Expand "Additional language data"**
3. **Check the box for "French (fra)"**
4. Complete the installation

Default installation path: `C:\Program Files\Tesseract-OCR\`

### Step 3: Add to PATH (if not automatic)

If Tesseract is not in your PATH:

1. Open System Properties → Environment Variables
2. Edit the `Path` variable
3. Add: `C:\Program Files\Tesseract-OCR`
4. Click OK and restart your terminal

### Step 4: Verify Installation

Open a **new** terminal and run:

```cmd
tesseract --version
```

Expected output:
```
tesseract 5.3.3
 leptonica-1.83.1
  ...
```

Check French language pack:

```cmd
tesseract --list-langs
```

Expected output should include:
```
List of available languages (2):
eng
fra
```

If `fra` is **not** listed, see "Manual Language Pack Installation" below.

---

## Manual French Language Pack Installation

If you installed Tesseract but forgot to include the French language pack:

### Option 1: Re-run Installer

1. Run the Tesseract installer again
2. Choose "Modify" installation
3. Check "French (fra)" under Additional language data
4. Complete the modification

### Option 2: Manual Download

1. Download `fra.traineddata` from:
   https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata

2. Copy it to:
   ```
   C:\Program Files\Tesseract-OCR\tessdata\fra.traineddata
   ```

3. Verify:
   ```cmd
   tesseract --list-langs
   ```

---

## macOS Installation

### Using Homebrew

```bash
# Install Tesseract
brew install tesseract

# Install language packs (includes French)
brew install tesseract-lang
```

### Verify

```bash
tesseract --version
tesseract --list-langs
```

---

## Linux Installation

### Debian/Ubuntu

```bash
# Install Tesseract
sudo apt-get update
sudo apt-get install -y tesseract-ocr

# Install French language pack
sudo apt-get install -y tesseract-ocr-fra
```

### Fedora/RHEL

```bash
sudo dnf install tesseract tesseract-langpack-fra
```

### Verify

```bash
tesseract --version
tesseract --list-langs
```

---

## Testing the Installation

### Quick Test

Run the demo script:

```bash
python scripts/demo_ocr.py
```

This will:
1. Check if Tesseract is installed
2. Verify the French language pack
3. Attempt OCR on a sample image

### Manual Test

Create a test file `test_ocr.py`:

```python
import pytesseract
from PIL import Image

# Test basic OCR
print("Tesseract version:", pytesseract.get_tesseract_version())
print("Available languages:", pytesseract.get_languages())

# Test French OCR (if you have a test image)
# img = Image.open("test_image.png")
# text = pytesseract.image_to_string(img, lang='fra')
# print("Extracted text:", text)
```

Run:
```bash
python test_ocr.py
```

---

## Troubleshooting

### Error: "tesseract is not installed or it's not in your PATH"

**Cause:** Tesseract is not installed or not in system PATH

**Solution:**
1. Install Tesseract (see above)
2. Add to PATH
3. Restart terminal
4. Verify with `tesseract --version`

### Error: Accents appear as "?" or wrong characters

**Cause:** French language pack not installed

**Solution:**
1. Check: `tesseract --list-langs`
2. If `fra` is missing, install it (see "Manual Language Pack Installation")
3. Verify again

### Error: "TesseractNotFoundError"

**Cause:** Python can't find Tesseract executable

**Solution (Windows):**
```python
# Add to your script before importing pytesseract
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

**Solution (macOS/Linux):**
```bash
# Find Tesseract location
which tesseract

# Add to environment
export TESSDATA_PREFIX=/usr/local/share/tessdata/
```

### Low OCR Confidence / Poor Results

**Possible causes:**
1. Image not preprocessed (run Task 6 first)
2. Wrong language pack (must use `fra` for French)
3. Image quality too low

**Solutions:**
1. Ensure preprocessing ran: `python -m src.preprocessor`
2. Verify French pack: `tesseract --list-langs`
3. Check preprocessing quality scores in manifest

---

## After Installation

Once Tesseract is installed with the French language pack:

1. **Reorganize and run OCR:**
   ```bash
   python scripts/reorganize_and_ocr.py
   ```

2. **Or run OCR directly:**
   ```bash
   python -m src.ocr_engine --input data/processed --output outputs/ocr_results
   ```

3. **Verify results:**
   ```bash
   # Check manifest
   cat outputs/ocr_results/ocr_manifest.json
   
   # Check individual invoice
   cat outputs/ocr_results/Real_Invoice_FR_Cbsa_Customs.json
   ```

---

## Additional Resources

- **Tesseract Documentation:** https://tesseract-ocr.github.io/
- **Tesseract GitHub:** https://github.com/tesseract-ocr/tesseract
- **Language Data:** https://github.com/tesseract-ocr/tessdata
- **Windows Installer:** https://github.com/UB-Mannheim/tesseract/wiki

---

## Quick Reference

| Platform | Install Command | Language Pack |
|----------|----------------|---------------|
| Windows | Download installer from GitHub | Check "French (fra)" during install |
| macOS | `brew install tesseract tesseract-lang` | Included in tesseract-lang |
| Ubuntu/Debian | `sudo apt-get install tesseract-ocr tesseract-ocr-fra` | Separate package |
| Fedora/RHEL | `sudo dnf install tesseract tesseract-langpack-fra` | Separate package |

**Verify:** `tesseract --list-langs` should show `fra`

---

**Need help?** Check the troubleshooting section or refer to the official Tesseract documentation.
