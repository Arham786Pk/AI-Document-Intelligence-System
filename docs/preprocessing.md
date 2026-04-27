# Task 6 — Preprocessing methodology

This document explains **what** the preprocessing stage does, **why** each
step exists, and **how** to reproduce / extend it.

The pipeline is implemented in [`src/preprocessor.py`](../src/preprocessor.py)
(core module) and driven by [`src/run_preprocess.py`](../src/run_preprocess.py)
(reads `docs/ground_truth.csv` and processes the 20 listed documents).

---

## 1. Purpose

OCR engines (Tesseract, PaddleOCR) are sensitive to image quality. A clean,
straight, high-contrast page can OCR at >95 % character accuracy; a tilted
or noisy scan of the same page may drop to 50–60 %.

Preprocessing turns each input PDF into a set of **per-page PNG images** that
are optimised for the OCR stage (Task 7). It does **not** read text — it
only prepares the pixels.

---

## 2. Inputs and outputs

| | Path | Count | Format |
|--|------|------:|--------|
| **Input**  | `data/raw/used/{digital_pdfs,scanned_docs}/*.pdf` and `data/raw/extra/{digital_pdfs,scanned_docs}/*.pdf` | 20 PDFs | text-PDF or scanned-PDF |
| **Output** | `data/processed/<doc_stem>_p<NN>.png` | 51 PNGs | grayscale or binarised PNG |

Naming pattern: `<original_filename_without_extension>_p01.png`,
`_p02.png`, … one PNG per page.

The pipeline reads **only** documents listed in
[`docs/ground_truth.csv`](ground_truth.csv) (20 FR docs total). Six of those
20 live in `data/raw/extra/` because the GT refresh pulled in real-filled FR
PDFs from the held-out pool; the loader is modality-aware and resolves both
locations. The remaining ~117 unlabelled docs in `data/raw/extra/` are
intentionally skipped — no point preprocessing what cannot be scored.

---

## 3. Two processing paths

The script picks one of two paths per document, based on the `modality`
column in the ground-truth CSV:

| Modality   | Count | Path        | Steps                                        |
|------------|------:|-------------|----------------------------------------------|
| `digital`  | 18    | **light**   | render → grayscale → save                    |
| `scanned`  | 2     | **full**    | render → grayscale → deskew → denoise → adaptive threshold → save |

### Why two paths?

Digital PDFs are exported from Word / InDesign / LaTeX — their text edges
are already crisp. Running aggressive cleanup on them (denoise, threshold)
**hurts** quality: anti-aliased edges get destroyed and characters thicken.
A light path preserves the original sharpness.

Scanned PDFs are camera- or scanner-captured pages with noise, tilt, and
uneven lighting. They need the full pipeline to be readable.

---

## 4. Each step explained

### 4.1 Render at 300 DPI

```python
DPI = 300
ZOOM = DPI / 72.0   # PyMuPDF default is 72 DPI; multiply to scale up
mat = fitz.Matrix(ZOOM, ZOOM)
pix = page.get_pixmap(matrix=mat, alpha=False)
```

PDFs store text as vector glyphs. To run OCR we need a raster image. The
target resolution is **300 DPI**, which is the print-industry standard and
the documented sweet spot for OCR engines.

| DPI  | A4 image size | OCR quality | Notes                              |
|------|---------------|-------------|------------------------------------|
| 72   | 595 × 842     | ❌ poor     | text edges blur out                |
| 150  | 1240 × 1754   | ⚠️ ok       | borderline for small text          |
| **300** | **2480 × 3508** | **✅ best** | **chosen value**            |
| 600  | 4960 × 7016   | ✅ same     | no quality gain, 2–3× slower       |

### 4.2 Grayscale

```python
gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
```

Colour information is irrelevant to OCR. Reducing 3 channels to 1 makes
all downstream steps roughly 3× faster and simplifies thresholding.

### 4.3 Deskew (scanned only)

```python
inv = cv2.bitwise_not(gray)
coords = np.column_stack(np.where(inv > 0))   # all dark pixel coordinates
angle = cv2.minAreaRect(coords)[-1]
angle = -(90 + angle) if angle < -45 else -angle
```

Scanners and phone cameras almost never capture a page perfectly straight.
Even a 2° tilt drops OCR accuracy noticeably.

The algorithm:
1. Invert so text becomes "on" pixels.
2. Find the smallest rotated rectangle that contains every text pixel.
3. The rectangle's angle ≈ the page's tilt.
4. Rotate by the negative of that angle (skip if `|angle| < 0.3°` to avoid
   noise-induced micro-rotations).

### 4.4 Denoise (scanned only)

```python
cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
```

Old scans contain "salt-and-pepper" noise — random dark/light pixels that
look like punctuation to OCR. **Non-local means** removes them by
averaging similar small patches across the page. Unlike blur filters, it
preserves edges, so text strokes stay sharp.

`h=10` is moderate strength; raising it removes more noise but starts
eroding thin strokes.

### 4.5 Adaptive threshold (scanned only)

```python
cv2.adaptiveThreshold(
    gray, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
    blockSize=31, C=15,
)
```

Converts the grayscale page into pure black-on-white. **Adaptive** means
each region computes its own threshold — important for scans with uneven
lighting (one corner brighter than another).

`blockSize=31` controls the local window; `C=15` is a brightness offset.
Both are tuned for office-document scans at 300 DPI.

---

## 5. Verification

A smoke test runs the full pipeline on the first available ground-truth
document and asserts that page PNGs are written and non-empty:

```bash
python tests/test_preprocessor.py
# expected output: OK
```

To rerun the full batch:

```bash
python src/run_preprocess.py
# expected output:
# INFO preprocessed Real_MaterialCert_FR_Larobinetterie_134822.pdf (1 pages, digital)
# ...
# INFO done: 20 ok, 0 missing, 0 failed (of 20)
```

---

## 6. Results

| Metric                       | Value      |
|------------------------------|------------|
| Documents processed          | 20 / 20    |
| Failed                       | 0          |
| Total page PNGs produced     | 51         |
| Disk footprint of `data/processed/` | ~42 MB |
| Avg pages per document       | 5.25       |
| Largest doc                  | `Real_FabricationSheet_EN_DOE_Module2A.pdf` (54 pages) |
| Smallest docs                | many at 1 page |

Pages-per-document breakdown:

| Pages | Documents |
|------:|-----------|
| 1     | 11        |
| 2     | 4         |
| 4     | 3         |
| 10    | 1         |
| 12    | 1         |
| 54    | 1         |

---

## 7. Known issues & limitations

- **MuPDF "structure tree" warnings** — printed for some scanned PDFs.
  Cosmetic only; pages still render correctly.
- **Deskew sensitivity on text-sparse pages** — `minAreaRect` becomes
  unreliable if a page has very few dark pixels (e.g. mostly-blank cover
  pages). Could fall back to Hough-line-based deskew in future.
- **Single global modality per document** — every page of a doc uses the
  same path. A few real PDFs are mixed (digital text + scanned exhibits);
  per-page modality detection would be a future enhancement.
- **No multi-column / table awareness** — preprocessor outputs whole pages.
  Layout analysis is deferred to the OCR stage (PaddleOCR has built-in
  layout detection).

---

## 8. Future work (out of scope for Milestone 1)

- Per-page modality detection (`fitz.Page.get_text()` empty → scanned).
- Border / shadow removal for phone-camera scans.
- Optional super-resolution for very low-DPI inputs.
- Page-level layout segmentation (text vs table vs figure) before OCR.

---

## 9. File index for this task

| Path | Purpose |
|------|---------|
| [`src/preprocessor.py`](../src/preprocessor.py) | Core module — `preprocess_document(path, out_dir, modality)` and helpers |
| [`src/run_preprocess.py`](../src/run_preprocess.py) | CLI driver — reads ground truth, processes all 20 |
| [`tests/test_preprocessor.py`](../tests/test_preprocessor.py) | Smoke test — verifies one PDF round-trips |
| [`scripts/split_used_vs_extra.py`](../scripts/split_used_vs_extra.py) | One-shot — separated `data/raw/` into `used/` and `extra/` |
| `data/processed/` | Output directory (51 PNGs, regenerable) |
