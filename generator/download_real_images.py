"""
Download real industrial document IMAGES from public blog / reference sites.

These are genuinely new images (not page-renders of PDFs we already have).
Saved directly into data/raw/images/ with the Real_<DocType>_<Lang>_<Source>.<ext>
convention so they slot in next to the synthetic images.
"""
from __future__ import annotations
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = Path(__file__).resolve().parent.parent
IMG_DIR = BASE / "data" / "raw" / "images"
IMG_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36"),
    "Accept": "image/avif,image/webp,image/png,image/jpeg,image/*,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}

# (save_as, url, notes)
DOWNLOADS = [
    # -------- Material Certificates --------
    ("Real_MaterialCert_EN_MeadMetals_Example1.jpg",
     "https://www.meadmetals.com/hs-fs/hubfs/mill%20test%20report%20example%201.jpg?width=652",
     "Mead Metals mill test report example 1"),
    ("Real_MaterialCert_EN_MeadMetals_Example2.jpg",
     "https://www.meadmetals.com/hs-fs/hubfs/mill%20test%20report%20example%202.jpg?width=800&height=1034",
     "Mead Metals mill test report example 2"),
    ("Real_MaterialCert_EN_MeadMetals_Example3.jpg",
     "https://www.meadmetals.com/hs-fs/hubfs/mill%20test%20report%20example%203.jpg?width=800&height=1034",
     "Mead Metals mill test report example 3"),
    ("Real_MaterialCert_EN_HQTS_S690QL.jpg",
     "https://www.hqts.com/wp-content/uploads/2023/03/S690QL-Steel-Plate-MTC_00-1024x724.jpg",
     "HQTS S690QL steel plate MTC"),
    ("Real_MaterialCert_EN_WhatIsPiping_Sample.png",
     "https://whatispiping.com/wp-content/uploads/2023/05/Sample-Material-Test-Certificate.png",
     "WhatIsPiping sample material test certificate"),
    ("Real_MaterialCert_EN_WeldFabWorld_Seamless.jpg",
     "https://www.weldfabworld.com/wp-content/uploads/2025/08/536617529_1233445395462760_5884830540522569487_n.jpg",
     "WeldFabWorld seamless stainless pipe MTC"),
    ("Real_MaterialCert_EN_Wermac_MTC.gif",
     "https://www.wermac.org/documents/docs_img/mtc.gif",
     "Wermac mill test certificate illustration"),
    ("Real_MaterialCert_EN_Wermac_Heat.gif",
     "https://www.wermac.org/documents/docs_img/heat1.gif",
     "Wermac heat number illustration"),
    ("Real_MaterialCert_FR_Artis_Exemple.png",
     "https://cdn.prod.website-files.com/608149adc4340fa49156d7fb/6099257307641bec9f872be9_2.-exemple-certificat-matiere.png",
     "Artis Groupe exemple certificat matiere"),
    ("Real_MaterialCert_FR_Artis_Documents.png",
     "https://cdn.prod.website-files.com/608149adc4340fa49156d7fb/609925727c7397cd2bd98e0b_1.documents-de-controle.png",
     "Artis Groupe documents de controle"),
    ("Real_MaterialCert_FR_RocDacier_S355J2M.jpg",
     "https://www.rocdacier.com/wp-content/uploads/2020/08/certificat-matiere-S355J2M.jpg",
     "RocDacier certificat matiere S355J2+M"),

    # -------- Welding Plans / WPS / Weld maps --------
    ("Real_WeldingPlan_EN_Eziil_WPS1.png",
     "https://eziil.com/wp-content/uploads/2024/02/WPS-document-example.png",
     "Eziil WPS document example"),
    ("Real_WeldingPlan_EN_Eziil_WPS2.png",
     "https://eziil.com/wp-content/uploads/2024/02/WPS-document-example-2.png",
     "Eziil WPS/PQR support doc"),
    ("Real_WeldingPlan_EN_Eziil_PQR.png",
     "https://eziil.com/wp-content/uploads/2024/02/PQR-sample.png",
     "Eziil PQR sample"),
    ("Real_WeldingPlan_EN_MaterialWelding_Map.jpg",
     "https://materialwelding.com/wp-content/uploads/2022/04/Welding_map-1.jpg",
     "MaterialWelding pressure-vessel weld map"),
    ("Real_WeldingPlan_EN_MaterialWelding_PipingMap.png",
     "https://materialwelding.com/wp-content/uploads/2021/08/weld-map.png",
     "MaterialWelding piping weld map"),
    ("Real_WeldingPlan_EN_MaterialWelding_Log.png",
     "https://materialwelding.com/wp-content/uploads/2021/08/weld-log.png",
     "MaterialWelding weld log example"),
    ("Real_WeldingPlan_EN_Holland_WeldLog.jpg",
     "https://hollandapt.blog/wp-content/uploads/2017/02/weld-log.jpg",
     "Holland APT typical weld log"),

    # -------- Fabrication Sheets / BOM --------
    ("Real_FabricationSheet_EN_Eziil_BOM1.png",
     "https://eziil.com/wp-content/uploads/2024/02/BOM_example_1.png",
     "Eziil BOM example 1"),
    ("Real_FabricationSheet_EN_Eziil_BOM2.png",
     "https://eziil.com/wp-content/uploads/2024/02/BOM_example_2.png",
     "Eziil BOM example 2"),
    ("Real_FabricationSheet_EN_Eziil_BOM3.png",
     "https://eziil.com/wp-content/uploads/2024/02/BOM_example_3.png",
     "Eziil BOM example 3 (hierarchical)"),

    # -------- Invoices --------
    ("Real_Invoice_EN_IncoDocs_Commercial.jpg",
     "https://incodocs.com/templates/Commercial%20Invoice.jpg",
     "IncoDocs commercial invoice template"),
    ("Real_Invoice_EN_Anshum_OCR1.jpg",
     "https://github.com/anshumyname/Invoice_ocr/raw/testing/readme_images/img1.jpg",
     "GitHub Invoice_ocr readme img1"),
    ("Real_Invoice_EN_Anshum_OCR2.jpg",
     "https://github.com/anshumyname/Invoice_ocr/raw/testing/readme_images/img2.jpg",
     "GitHub Invoice_ocr readme img2"),
    ("Real_Invoice_EN_Anshum_OCR3.jpg",
     "https://github.com/anshumyname/Invoice_ocr/raw/testing/readme_images/img3.jpg",
     "GitHub Invoice_ocr readme img3"),

    # -------- Inspection Reports --------
    ("Real_InspectionReport_EN_Pdffiller_Weld.png",
     "https://www.pdffiller.com/preview/250/13/250013429/large.png",
     "PdfFiller welding visual inspection report sample"),
    ("Real_InspectionReport_EN_SCM_Initial.png",
     "https://scm-solution.com/wp-content/uploads/2024/07/1-724x1024.png",
     "SCM initial project inspection checklist"),
    ("Real_InspectionReport_EN_SCM_Business.png",
     "https://scm-solution.com/wp-content/uploads/2024/07/2-724x1024.png",
     "SCM business functions quality report"),
    ("Real_InspectionReport_EN_SCM_Dispatch1.png",
     "https://scm-solution.com/wp-content/uploads/2024/07/3-724x1024.png",
     "SCM product quality inspection before dispatch 1"),
    ("Real_InspectionReport_EN_SCM_Dispatch2.png",
     "https://scm-solution.com/wp-content/uploads/2024/07/4-724x1024.png",
     "SCM product quality inspection before dispatch 2"),
    ("Real_InspectionReport_EN_SCM_Shipment.png",
     "https://scm-solution.com/wp-content/uploads/2024/07/5-724x1024.png",
     "SCM product shipment inspection report"),
    ("Real_InspectionReport_EN_SCM_Safety.png",
     "https://scm-solution.com/wp-content/uploads/2024/07/6-724x1024.png",
     "SCM workplace safety inspection report"),
]


def is_image_bytes(data: bytes) -> bool:
    if not data or len(data) < 50:
        return False
    # JPEG
    if data[:3] == b"\xff\xd8\xff":
        return True
    # PNG
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    # GIF
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return True
    # WEBP (RIFF....WEBP)
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True
    return False


def download(url: str, dst: Path) -> tuple[bool, str]:
    if dst.exists() and dst.stat().st_size > 1024:
        return True, "already exists, skipped"
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=30) as r:
            data = r.read()
        if len(data) < 512:
            return False, f"too small ({len(data)} bytes)"
        if not is_image_bytes(data):
            return False, f"not a recognised image (got {data[:8]!r})"
        dst.write_bytes(data)
        return True, f"OK ({len(data):,} bytes)"
    except HTTPError as e:
        return False, f"HTTP {e.code}"
    except URLError as e:
        return False, f"URL error: {e.reason}"
    except Exception as e:
        return False, f"error: {e}"


def main():
    ok, fail = 0, 0
    failures = []
    for name, url, notes in DOWNLOADS:
        dst = IMG_DIR / name
        rel = dst.relative_to(BASE)
        print(f"  -> {rel}")
        success, msg = download(url, dst)
        if success:
            ok += 1
            print(f"     [OK] {msg}")
        else:
            fail += 1
            print(f"     [FAIL] {msg}")
            failures.append((url, rel, msg, notes))

    print("\n" + "=" * 70)
    print(f"Done. Success: {ok}   Failed: {fail}   Total: {len(DOWNLOADS)}")
    if failures:
        print("\nFailures (open URL in browser and Save-As if you want these):")
        for url, rel, msg, notes in failures:
            print(f"  - {notes}: {msg}\n    {url}\n    -> {rel}")


if __name__ == "__main__":
    main()
