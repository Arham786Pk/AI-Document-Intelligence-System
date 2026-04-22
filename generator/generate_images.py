"""
Phone-Capture Style Image Generator
===================================
Takes existing clean PDFs from digital_pdfs/ and produces realistic
"phone photo of a document" images for the images/ folders.

Simulates:
    - Perspective skew (held at angle)
    - Uneven lighting gradient (shadow on one side)
    - Motion blur (slight hand shake)
    - Warm phone-camera tint
    - JPEG compression artifacts
    - Rotation (handheld)
    - Background padding (table surface peeking)

Output:
    data/raw/images/Synthetic_<DocType>_<Lang>_NN.(jpg|png)  (10 images)
"""

from __future__ import annotations
import random
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import math

SEED = 42
random.seed(SEED)

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
IMAGES_DIR = RAW / "images"
TMP_DIR = BASE / "generator" / "_tmp_img"
for p in (IMAGES_DIR, TMP_DIR):
    p.mkdir(parents=True, exist_ok=True)

DOC_TYPES = ["fabrication_sheet", "welding_plan", "invoice",
             "material_certificate", "inspection_report"]

DTYPE_TO_FILENAME = {
    "material_certificate": "MaterialCert",
    "welding_plan":         "WeldingPlan",
    "fabrication_sheet":    "FabricationSheet",
    "inspection_report":    "InspectionReport",
    "invoice":              "Invoice",
}


def pdf_to_png(pdf_path: Path, out_prefix: Path, dpi: int = 200) -> Path:
    subprocess.run(
        ["pdftoppm", "-r", str(dpi), "-png", str(pdf_path), str(out_prefix)],
        check=True,
    )
    pages = sorted(out_prefix.parent.glob(f"{out_prefix.name}-*.png"))
    if not pages:
        raise RuntimeError(f"pdftoppm produced no output for {pdf_path}")
    return pages[0]


def apply_perspective(img: Image.Image, rng: random.Random) -> Image.Image:
    """Slight perspective skew as if phone held at angle."""
    W, H = img.size
    # Shift corners by small random amounts
    shift = int(min(W, H) * 0.04)
    src = [(0, 0), (W, 0), (W, H), (0, H)]
    dst = [
        (rng.randint(0, shift), rng.randint(0, shift)),
        (W - rng.randint(0, shift), rng.randint(0, shift)),
        (W - rng.randint(0, shift), H - rng.randint(0, shift)),
        (rng.randint(0, shift), H - rng.randint(0, shift)),
    ]
    # Compute perspective coefficients
    matrix = []
    for (xs, ys), (xd, yd) in zip(src, dst):
        matrix.append([xs, ys, 1, 0, 0, 0, -xd * xs, -xd * ys])
        matrix.append([0, 0, 0, xs, ys, 1, -yd * xs, -yd * ys])
    import numpy as np
    A = np.array(matrix, dtype=float)
    B = np.array([p for pair in dst for p in pair], dtype=float)
    coeffs = np.linalg.solve(A, B)
    return img.transform((W, H), Image.PERSPECTIVE, tuple(coeffs),
                         resample=Image.BICUBIC,
                         fillcolor=(40, 35, 30))


def add_lighting_gradient(img: Image.Image, rng: random.Random) -> Image.Image:
    """Add uneven lighting -- one side dim like natural shadow."""
    W, H = img.size
    gradient = Image.new("L", (W, H), 255)
    draw = ImageDraw.Draw(gradient)
    # Radial/linear shadow
    direction = rng.choice(["left", "right", "top", "bottom", "corner"])
    steps = 40
    for i in range(steps):
        shade = int(255 - (i / steps) * rng.randint(50, 130))
        if direction == "left":
            draw.rectangle([i * W // steps, 0, (i + 1) * W // steps, H], fill=shade)
        elif direction == "right":
            draw.rectangle([W - (i + 1) * W // steps, 0, W - i * W // steps, H], fill=shade)
        elif direction == "top":
            draw.rectangle([0, i * H // steps, W, (i + 1) * H // steps], fill=shade)
        elif direction == "bottom":
            draw.rectangle([0, H - (i + 1) * H // steps, W, H - i * H // steps], fill=shade)
        else:  # corner
            draw.ellipse([W - (i + 1) * W // steps * 2, H - (i + 1) * H // steps * 2,
                          W + i * 20, H + i * 20], fill=shade)
    # Apply the gradient as a multiply mask
    gradient = gradient.filter(ImageFilter.GaussianBlur(radius=40))
    img_arr = img.convert("RGB")
    # Multiply channel-wise using alpha composite
    overlay = Image.new("RGB", (W, H), (0, 0, 0))
    result = Image.composite(img_arr, overlay, gradient)
    return result


def add_warm_tint(img: Image.Image, rng: random.Random) -> Image.Image:
    """Phone cameras add warm/yellow cast under indoor lighting."""
    r, g, b = img.split()
    r = r.point(lambda v: min(255, int(v * rng.uniform(1.00, 1.08))))
    g = g.point(lambda v: min(255, int(v * rng.uniform(0.95, 1.02))))
    b = b.point(lambda v: min(255, int(v * rng.uniform(0.82, 0.92))))
    return Image.merge("RGB", (r, g, b))


def add_motion_blur(img: Image.Image, rng: random.Random) -> Image.Image:
    """Slight motion blur from hand shake."""
    if rng.random() < 0.6:
        radius = rng.uniform(0.4, 1.4)
        img = img.filter(ImageFilter.GaussianBlur(radius=radius))
    return img


def add_background(img: Image.Image, rng: random.Random) -> Image.Image:
    """Pad with a darker 'table surface' around the rotated document."""
    W, H = img.size
    pad = int(min(W, H) * rng.uniform(0.06, 0.12))
    bg_color = rng.choice([
        (45, 35, 30),    # dark wood
        (70, 60, 50),    # medium wood
        (30, 30, 35),    # dark desk
        (100, 90, 75),   # light table
        (55, 55, 60),    # gray
    ])
    canvas = Image.new("RGB", (W + 2 * pad, H + 2 * pad), bg_color)
    # Add noise to background
    draw = ImageDraw.Draw(canvas)
    for _ in range(500):
        x = rng.randint(0, canvas.size[0] - 1)
        y = rng.randint(0, canvas.size[1] - 1)
        dv = rng.randint(-20, 20)
        r, g, b = bg_color
        draw.point((x, y), fill=(max(0, min(255, r + dv)),
                                  max(0, min(255, g + dv)),
                                  max(0, min(255, b + dv))))
    canvas.paste(img, (pad, pad))
    return canvas


def simulate_phone_capture(src_img: Image.Image, rng: random.Random) -> Image.Image:
    """Full phone-capture simulation pipeline."""
    img = src_img.convert("RGB")

    # 1. Downscale (phone photos often lower DPI than scan)
    w, h = img.size
    scale = rng.uniform(0.55, 0.75)
    img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # 2. Perspective skew
    img = apply_perspective(img, rng)

    # 3. Motion blur
    img = add_motion_blur(img, rng)

    # 4. Warm tint
    img = add_warm_tint(img, rng)

    # 5. Reduce contrast a touch (phone cameras often flatten)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(rng.uniform(0.80, 0.95))

    # 6. Rotate larger than scan (±3 to ±12 degrees -- handheld)
    angle = rng.uniform(-12, 12)
    img = img.rotate(angle, resample=Image.BICUBIC, expand=True,
                     fillcolor=(40, 35, 30))

    # 7. Add lighting gradient
    img = add_lighting_gradient(img, rng)

    # 8. Add background / table surface
    img = add_background(img, rng)

    # 9. Final slight sharpen-reduce pass
    if rng.random() < 0.4:
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    return img


def main():
    # Ensure numpy installed
    try:
        import numpy  # noqa
    except ImportError:
        subprocess.run(["pip", "install", "numpy", "--break-system-packages", "--quiet"],
                       check=True)

    # Load existing ground truth so we can append image entries
    gt_path = BASE / "generator" / "ground_truth_seed.json"
    ground_truth = json.loads(gt_path.read_text(encoding="utf-8"))

    # We want to index by doc_type + language + variant=digital, k=01
    # to pick a "clean source" for each image we make.
    by_key = {(d["doc_type"], d["language"], d["filename"]): d for d in ground_truth}

    # Plan: one image per doc_type per language, alternating JPG / PNG
    new_entries = []
    idx = 1000  # start outside normal index range
    for lang in ("en", "fr"):
        lang_up = lang.upper()
        images_dir = IMAGES_DIR
        images_dir.mkdir(parents=True, exist_ok=True)

        for i, dtype in enumerate(DOC_TYPES):
            dtype_cc = DTYPE_TO_FILENAME[dtype]
            # Pick a source PDF: first synthetic digital one of this type+lang
            src_pdf = RAW / "digital_pdfs" / f"Synthetic_{dtype_cc}_{lang_up}_01.pdf"
            if not src_pdf.exists():
                print(f"[skip] no source PDF for {dtype} {lang}")
                continue

            rng = random.Random(SEED + idx)
            out_prefix = TMP_DIR / f"src_{idx}"
            png_path = pdf_to_png(src_pdf, out_prefix, dpi=200)
            src_img = Image.open(png_path)

            out_img = simulate_phone_capture(src_img, rng)

            # Alternate JPG / PNG
            ext = "jpg" if i % 2 == 0 else "png"
            filename = f"Synthetic_{dtype_cc}_{lang_up}_{i+1:02d}.{ext}"
            out_path = images_dir / filename
            if ext == "jpg":
                out_img.save(out_path, "JPEG", quality=rng.randint(55, 78))
            else:
                out_img.save(out_path, "PNG", optimize=True)

            # Look up ground-truth entry for this source PDF
            src_entry = next(
                (d for d in ground_truth if d["filename"] == src_pdf.name),
                None,
            )
            if src_entry:
                entry = {
                    "project_id": src_entry["project_id"],
                    "supplier": src_entry["supplier"],
                    "material": src_entry["material"],
                    "quantity": src_entry["quantity"],
                    "date": src_entry["date"],
                    "doc_type": dtype,
                    "filename": filename,
                    "language": lang,
                    "variant": "image",
                    "path": str(out_path.relative_to(BASE)),
                    "source_pdf": src_pdf.name,
                }
                new_entries.append(entry)

            print(f"  -> {out_path.relative_to(BASE)}  ({out_path.stat().st_size // 1024} KB)")
            idx += 1

            # Cleanup the rasterized source
            try: png_path.unlink()
            except Exception: pass

    # Append to ground truth
    ground_truth.extend(new_entries)
    gt_path.write_text(json.dumps(ground_truth, indent=2, ensure_ascii=False),
                       encoding="utf-8")

    # Cleanup tmp
    for f in TMP_DIR.glob("*"):
        try: f.unlink()
        except Exception: pass

    print(f"\nGenerated {len(new_entries)} images.")
    print(f"  images/: {len(list(IMAGES_DIR.glob('Synthetic_*.*')))}")
    print(f"Ground truth total entries: {len(ground_truth)}")


if __name__ == "__main__":
    main()
