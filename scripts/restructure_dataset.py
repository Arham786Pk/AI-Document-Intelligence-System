"""One-shot dataset restructure for Milestone 2 (resumable).

Flattens the data tree into exactly two folders:
    data/pdf/      -> all invoice PDFs (real + synthetic), flat, no subfolders
    data/images/   -> all invoice images (real + synthetic), flat, no subfolders

Real files get a consistent name; non-invoice / low-quality / PII files are
moved to quarantine/ (preserved). Manifests are rebuilt from git rename data so
the script is safe to re-run after a partial move.
"""

import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PDF_OUT = DATA / "pdf"
IMG_OUT = DATA / "images"
QUARANTINE = ROOT / "quarantine"


def git_mv(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "mv", str(src), str(dst)], cwd=ROOT, check=True)


def natural_key(p: Path):
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", p.name)]


def next_index(out_dir: Path, prefix: str) -> int:
    nums = [int(m.group(1))
            for p in out_dir.glob(f"{prefix}*")
            if (m := re.search(r"(\d+)", p.name))]
    return max(nums, default=0) + 1


def write_manifest():
    """Rebuild manifests from git's staged rename detection."""
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "status", "--porcelain"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    pdf_rows, img_rows = [], []
    for line in out.splitlines():
        if " -> " not in line:
            continue
        old, new = line[3:].split(" -> ")
        if new.startswith("data/pdf/"):
            pdf_rows.append((Path(new).name, "real", old))
        elif new.startswith("data/images/"):
            img_rows.append((Path(new).name, "real", old))
    pdf_rows.sort(key=lambda r: r[0])
    img_rows.sort(key=lambda r: r[0])
    for name, rows in (("pdf_manifest.csv", pdf_rows), ("images_manifest.csv", img_rows)):
        with open(DATA / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["filename", "type", "original_path"])
            w.writerows(rows)
    print(f"Manifests written: {len(pdf_rows)} pdf rows, {len(img_rows)} image rows")


def main():
    PDF_OUT.mkdir(parents=True, exist_ok=True)
    IMG_OUT.mkdir(parents=True, exist_ok=True)

    # --- Remaining sourced PDFs ---
    sourced = sorted((DATA / "Scanned_PDF" / "sourced_internet").glob("*.pdf"), key=natural_key)
    idx = next_index(PDF_OUT, "FR_invoice_real_")
    for src in sourced:
        git_mv(src, PDF_OUT / f"FR_invoice_real_{idx:03d}.pdf")
        idx += 1
    print(f"Moved {len(sourced)} sourced PDFs (now {idx - 1} real PDFs total)")

    # --- Images ---
    img_src = DATA / "Images"
    if img_src.exists():
        real_imgs = sorted(
            [p for p in img_src.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}],
            key=natural_key,
        )
        for i, src in enumerate(real_imgs, start=1):
            git_mv(src, IMG_OUT / f"FR_invoice_img_real_{i:03d}{src.suffix.lower()}")
        print(f"Moved {len(real_imgs)} real images")

    # --- Quarantine ---
    QUARANTINE.mkdir(parents=True, exist_ok=True)
    for sub in ("_low_quality", "_not_invoices", "_pii_review"):
        d = DATA / "Scanned_PDF" / "sourced_internet" / sub
        if d.exists():
            for f in sorted(d.glob("*.pdf")):
                git_mv(f, QUARANTINE / sub.lstrip("_") / f.name)
            print(f"Quarantined {sub}")

    write_manifest()


if __name__ == "__main__":
    main()
