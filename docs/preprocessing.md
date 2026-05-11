# Preprocessing — Task 6

Module: [`src/preprocessor.py`](../src/preprocessor.py)
CLI (run once per source folder):
- `python -m src.preprocessor --input data/Images       --output data/processed`
- `python -m src.preprocessor --input data/Scanned_PDF  --output data/processed`

Per-page pipeline that turns a French invoice (PDF or phone photo) into a clean,
binarised, deskewed 300-DPI PNG ready for the OCR engine in Task 7.

---

## What it does

| Step | Purpose | Implementation |
|------|---------|---------------|
| 1. Source detection | Distinguish digital PDFs (extractable text) from scanned PDFs (image only) and from standalone photos. | `detect_source_type()` — opens the PDF and counts text chars; `≥ 80` chars on any page → `digital_pdf`. |
| 2. Render to RGB | Get every page as a 300-DPI RGB array. | `fitz.Page.get_pixmap(matrix=72→300 zoom)` for PDFs; `PIL.Image.open` for photos. |
| 3. Resize | Phone photos rarely embed real DPI metadata. We rescale so the short edge ≈ A4 width × 300 DPI. | `_resize_to_dpi()` — short-edge target = 8.27 × 300 ≈ 2480 px. |
| 4. Greyscale | Drop colour. | `cv2.cvtColor(..., COLOR_RGB2GRAY)` |
| 5. Denoise | Suppress JPEG artefacts and paper grain on photos. Skipped for digital PDFs (already clean). | `cv2.fastNlMeansDenoising(h=10)` |
| 6. Deskew | Rotate so text lines are horizontal. | Otsu threshold → minAreaRect on foreground pixels → `cv2.warpAffine`. |
| 7. Binarise | Robust to uneven lighting (typical of phone photos). | `cv2.adaptiveThreshold` with `ADAPTIVE_THRESH_GAUSSIAN_C`, blockSize 31, C 15. |
| 8. Quality score | Per-page sharpness + ink-coverage in `[0, 1]`. Invoice score = mean of pages. | `0.7 × min(1, lap_var/200) + 0.3 × coverage_band(0.02..0.40)`. |

Multi-page invoices are kept as `page_01.png`, `page_02.png`, … under one
folder per invoice, so Task 7 can OCR them in order and collapse to a single
JSON in Task 9.

---

## Output layout

```
data/processed/
├── preprocessing_manifest.json
├── Invoice_FR_016_scanned_260508_103316/
│   └── page_01.png
├── IMG-20260507-WA0148/
│   └── page_01.png
└── ...
```

`preprocessing_manifest.json` carries one record per invoice plus a summary
block. Example record:

```json
{
  "invoice_name": "Invoice_FR_018_scanned_260508_103257",
  "source_path": "...",
  "source_type": "scanned_pdf",
  "page_count": 1,
  "pages": [{ "page_index": 0, "output_path": "...", "width": 2479,
               "height": 3508, "dpi": 300, "quality_score": 0.632 }],
  "invoice_quality_score": 0.632,
  "degraded": false
}
```

---

## Quality score and degraded flag

| Component | Weight | Source |
|-----------|--------|--------|
| Sharpness | 0.7 | `min(1, Laplacian_variance / 200)` on the deskewed greyscale. |
| Coverage  | 0.3 | Penalises pages with `< 2 %` or `> 40 %` ink. |

`degraded = invoice_quality_score < 0.3`. This threshold flags blank scans,
black-page misfires, or out-of-focus phone shots while leaving real invoices
alone.

### Calibration on the Milestone-1 dataset

| Slice | n | mean | min | max | degraded |
|-------|---|------|-----|-----|----------|
| Scanned PDFs | 5 | 0.54 | 0.44 | 0.63 | 0 |
| Phone-photo invoices | 16 | 0.43 | 0.32 | 0.63 | 0 |
| Whole dataset | 21 | 0.46 | 0.31 | 0.63 | 0 |

(See `data/processed/preprocessing_manifest.json` after running the CLI.)

---

## Public API

```python
from src.preprocessor import (
    detect_source_type,    # (Path) -> "digital_pdf" | "scanned_pdf" | "image"
    preprocess_invoice,    # (src, out_root) -> InvoiceResult
    preprocess_folder,     # (in_dir, out_root) -> list[InvoiceResult]
    write_manifest,        # (results, out_root) -> Path
)
```

`InvoiceResult` is a dataclass with `pages: list[PageResult]`,
`invoice_quality_score`, and `degraded` flag — see the source for the full
shape.

---

## Tests

`tests/test_preprocessor.py` covers source-type detection, end-to-end
processing of one PDF and one photo, and constants. The suite auto-skips when
the gitignored client invoices are not present.

```bash
python -m pytest tests/test_preprocessor.py -v
```
