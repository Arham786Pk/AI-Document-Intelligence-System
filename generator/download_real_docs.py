"""
Real Document Downloader — PDFs for data/raw/{digital_pdfs, scanned_docs}

Downloads publicly available sample industrial PDFs and saves them directly
with the project's final naming convention:

    Real_<DocType>_<Lang>_<Source>.pdf

DocType  ∈ MaterialCert | WeldingPlan | FabricationSheet | InspectionReport | Invoice
Lang     ∈ EN | FR

USAGE:
    python generator/download_real_docs.py

The script is idempotent (skips files that already exist and validate as PDF).
"""
from __future__ import annotations
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE = Path(__file__).resolve().parent.parent
DIGITAL = BASE / "data" / "raw" / "digital_pdfs"
SCANNED = BASE / "data" / "raw" / "scanned_docs"
for p in (DIGITAL, SCANNED):
    p.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36"),
    "Accept": "application/pdf, */*",
}

# (target_folder, save_as, url, notes)
DOWNLOADS = [
    # =============== MATERIAL CERTIFICATES — EN ===============
    (DIGITAL, "Real_MaterialCert_EN_EN10204_Standard.pdf",
     "https://www.sanyosteel.com/files/EN/EN%2010204.pdf",
     "EN 10204 standard text"),
    (DIGITAL, "Real_MaterialCert_EN_Blackmer.pdf",
     "https://www.psgdover.com/docs/default-source/blackmer-docs/application-forms/form588.pdf?sfvrsn=ba6dcb59_6",
     "Blackmer / PSG Dover sample test certs"),
    (DIGITAL, "Real_MaterialCert_EN_Aerometal.pdf",
     "https://aerometalsalliance.com/resources/data-sheets/view/Aero-Metal-Alliance_All-Metals-Test-Certificates_54.pdf",
     "Aero Metal Alliance all-metals certs"),
    (DIGITAL, "Real_MaterialCert_EN_ABS_Cutsheet.pdf",
     "https://ww2.eagle.org/content/dam/eagle/publications/cutsheets/EN%2010204%20Material%20Verification%20Cutsheet.pdf",
     "American Bureau of Shipping cutsheet"),
    (DIGITAL, "Real_MaterialCert_EN_Intafast.pdf",
     "https://www.intafast.com/wp-content/uploads/2019/04/Test-certificates.pdf",
     "Intafast test certificates intro"),
    (DIGITAL, "Real_MaterialCert_EN_Actonbright.pdf",
     "https://www.actonbrightsteel.co.uk/datasheets/useful_information/bs_en_10204_certificate_types.pdf",
     "Acton Bright Steel cert types guide"),
    (SCANNED, "Real_MaterialCert_EN_NST_Inspection.pdf",
     "https://en.nst.no/dokumenter/sertifikater/13A31001.pdf",
     "Norsk Sveiseteknikk real 3.1 inspection cert"),
    (SCANNED, "Real_MaterialCert_EN_Niedax.pdf",
     "https://www.niedax.com/fileadmin/user_upload/user_upload/Mill_test_Certificate_1_.pdf",
     "Niedax scanned mill test certificate"),
    (SCANNED, "Real_MaterialCert_EN_Posco_Archro.pdf",
     "https://www.archro.com/pdf/perforated-metal-sheet-mill-certificate.pdf",
     "POSCO mill test cert (via Archro)"),
    (SCANNED, "Real_MaterialCert_EN_Processfittings_22.pdf",
     "https://www.processfittings.com/app/download/36290976/2.2+SAMPLE+Certificate.pdf",
     "Process Fittings EN 10204 2.2 sample cert"),
    (SCANNED, "Real_MaterialCert_EN_Easternmetal_Pipe.pdf",
     "https://www.easternmetaltrading.com/wp-content/uploads/2025/02/4982-Pipe-Mill-Certs.pdf",
     "Eastern Metal Trading pipe mill certs (multi-page scan)"),
    (SCANNED, "Real_MaterialCert_EN_NFPA13_Aboveground.pdf",
     "https://cdnsm5-hosted.civiclive.com/UserFiles/Servers/Server_6004363/File/Government/City%20Departments%20and%20Division/Fire/Fire%20Prevention/Aboveground%20Piping%20Certificate%20NFPA%2013.pdf",
     "NFPA 13 aboveground piping contractor material & test cert"),

    # =============== MATERIAL CERTIFICATES — FR ===============
    (DIGITAL, "Real_MaterialCert_FR_Larobinetterie_134822.pdf",
     "https://www.larobinetterie.com/?action=certificats/get-certificat-pdf/134822&language=fr_FR&tmp_lang=O",
     "La Robinetterie - Certificat de Reception 3.1"),
    (DIGITAL, "Real_MaterialCert_FR_Dillinger_Antelis.pdf",
     "https://antelis-steel.com/document/certificat-de-reception-3-1_EN-10204-2004_ISO-10474-2013.pdf",
     "Dillinger Hutte via Antelis (3.1)"),
    (DIGITAL, "Real_MaterialCert_FR_Larobinetterie_160629.pdf",
     "https://www.larobinetterie.com/?action=get-original-certificat-pdf/160629",
     "La Robinetterie - Certificat d'essai EN 10204 3.1"),
    (DIGITAL, "Real_MaterialCert_FR_Rocdacier_inox304L.pdf",
     "https://www.rocdacier.com/wp-content/uploads/2020/08/certificat-inox-304L.pdf",
     "Roc d'Acier certificat de reception 3.1 inox 304L"),
    (DIGITAL, "Real_MaterialCert_FR_Antelis_Dillinger_32.pdf",
     "https://antelis-steel.com/document/Certificat-reception-3-2-EN10204-2004_ISO10474-2013.pdf",
     "Antelis / Dillinger Hutte certificat 3.2 EN 10204"),
    (SCANNED, "Real_MaterialCert_FR_Ugitech_Alim.pdf",
     "https://swisssteel-group.com/content-media/documents/Certificates/Ugitech/ALIMENTARY-ATTESTATION_FR.pdf",
     "Ugitech / SwissSteel attestation alimentaire (signee)"),

    # =============== WELDING PLANS / WPS — EN ===============
    (DIGITAL, "Real_WeldingPlan_EN_AWS_D17.1.pdf",
     "https://pubs.aws.org/content/free_downloads/WPS_Sample_Form-D17.1-D17.1M-2010-AMD1.pdf",
     "AWS D17.1 WPS sample form"),
    (DIGITAL, "Real_WeldingPlan_EN_AWS_FormN1.pdf",
     "https://pubs.aws.org/content/free_downloads/Form_N1.pdf",
     "AWS D1.1 Annex N Form N-1 WPS"),
    (DIGITAL, "Real_WeldingPlan_EN_Sandvik.pdf",
     "https://www.mining.sandvik/siteassets/general-documents/download-center/ground-engaging-tools/product-welding-procedures/wps-ss-011-r2-wps-for-ha-50--32mm-ss2000--ss2300-material.pdf",
     "Sandvik WPS SS-011-R2"),
    (DIGITAL, "Real_WeldingPlan_EN_Ohiogas.pdf",
     "https://www.ohiogasassoc.org/wp/wp-content/uploads/2014/04/John-Lucas.pdf",
     "Ohio Gas Assoc WPS presentation"),
    (DIGITAL, "Real_WeldingPlan_EN_ASME_QW483.pdf",
     "https://www.asme.org/wwwasmeorg/media/resourcefiles/aboutasme/standards_certification/bpvc%20data%20forms/bpvc_ix_qw-483.pdf",
     "ASME BPVC Section IX form QW-483 PQR"),
    (DIGITAL, "Real_WeldingPlan_EN_FDOT_PQR_D16.pdf",
     "https://fdotwww.blob.core.windows.net/sitefinity/docs/default-source/materials/structural/fieldoperations/commericalinspection/documents/d1-6-pqr-675-070-13-digital-form.pdf?sfvrsn=f3a609de_4",
     "FDOT AWS D1.6 PQR digital form"),
    (SCANNED, "Real_WeldingPlan_EN_WPSAmerica_PQR_Sample.pdf",
     "https://www.wpsamerica.com/samplepqr.pdf",
     "WPSAmerica PQR sample (AWS D1.1)"),
    (SCANNED, "Real_WeldingPlan_EN_WPSAmerica_WPQR.pdf",
     "https://www.wpsamerica.com/guides/WPQR-WPSAmerica.pdf",
     "WPSAmerica WPQR sample (AWS D1.1)"),

    # =============== WELDING PLANS / DMOS / QMOS — FR ===============
    (DIGITAL, "Real_WeldingPlan_FR_CEREMA_QMOS_DMOS.pdf",
     "https://piles.cerema.fr/IMG/pdf/04c_qmos_dmos_cle0cd6d1.pdf",
     "CEREMA QMOS/DMOS"),
    (DIGITAL, "Real_WeldingPlan_FR_Axxair_QMOS_TIG.pdf",
     "https://blog.axxair.com/hubfs/Guides-AXXAIR/Guide-QMOS-soudage-TIG.pdf",
     "Axxair Guide QMOS soudage TIG"),
    (DIGITAL, "Real_WeldingPlan_FR_Cewac_DMOS_QMOS.pdf",
     "https://www.cewac.be/uploads/common/file/a4flyer_dmos_qmos.pdf",
     "CEWAC flyer DMOS / QMOS"),
    (DIGITAL, "Real_WeldingPlan_FR_Austech_QS_DMOS.pdf",
     "https://austech.nc/wp-content/uploads/2017/06/QS-DMOS.pdf",
     "Austech QS / DMOS"),
    (DIGITAL, "Real_WeldingPlan_FR_Isgroupe_Rediger_DMOS.pdf",
     "https://www.isgroupe.com/hubfs/FP-Fichiers/FP-%20pages%20%C3%A0%20pages/2%20-%20Technologie/RDMOS%20-%20R%C3%A9digez%20vos%20descriptifs%20de%20mode%20op%C3%A9ratoire%20de%20soudage%20(DMOS).pdf",
     "IS Groupe - Rediger vos DMOS"),
    (DIGITAL, "Real_WeldingPlan_FR_Isgroupe_Cahiers_Soudage.pdf",
     "https://www.isgroupe.com/hubfs/FP-Fichiers/FP-%20pages%20%C3%A0%20pages/2%20-%20Technologie/RCS%20-%20R%C3%A9digez%20vos%20cahiers%20de%20soudage.pdf",
     "IS Groupe - Rediger vos cahiers de soudage"),
    (DIGITAL, "Real_WeldingPlan_FR_Formation_Soudure_DMOS_QMOS_QS.pdf",
     "https://www.formation-soudure.com/DMOS,%20QMOS%20et%20QS.pdf",
     "Formation-Soudure DMOS / QMOS / QS"),
    (DIGITAL, "Real_WeldingPlan_FR_Francegaz_AFG_B132.pdf",
     "https://www.francegaz.fr/wp-content/uploads/B-132-52-Nov-2020-N270-Rev4.pdf",
     "France Gaz AFG B.132-52 qualification soudeurs"),
    (DIGITAL, "Real_WeldingPlan_FR_Metalpro_Soudage_EN1090.pdf",
     "https://www.metal-pro.org/files/union-des-metalliers/espace-public/publications/guides/soudage_VF3.pdf",
     "Union des Metalliers guide soudage EN 1090-2"),
    (SCANNED, "Real_WeldingPlan_FR_Cahier_Soudage_Filtres.pdf",
     "https://www.soudeurs.com/telechargements/647-cahier%20de%20soudage%20FILTRES%20%20SEPARATEURS.pdf",
     "Cahier de soudage filtres separateurs (scan multi-pieces)"),

    # =============== FABRICATION SHEETS — EN/FR ===============
    (DIGITAL, "Real_FabricationSheet_EN_DOE_Module2A.pdf",
     "https://www.energy.gov/sites/default/files/2021-07/Module_2A.pdf",
     "DOE Module 2A BOM and BOP"),
    (DIGITAL, "Real_FabricationSheet_FR_Goulet_Lecture_Plan_Soudage.pdf",
     "https://goulet.ca/abstract/lecture-de-plans-en-soudage-52.pdf",
     "Goulet lecture de plans en soudage"),

    # =============== INVOICES — EN ===============
    (DIGITAL, "Real_Invoice_EN_Tennant.pdf",
     "https://www.tennantco.com/content/dam/resources/web-content/supplier-documents/sample-commercial-invoice.pdf",
     "Tennant sample commercial invoice"),
    (DIGITAL, "Real_Invoice_EN_Baxter_Freight.pdf",
     "https://baxterfreight.com/wp-content/uploads/2023/03/Sample-for-Commercial-Invoice.pdf",
     "Baxter Freight commercial invoice sample"),
    (DIGITAL, "Real_Invoice_EN_Tnt_Template.pdf",
     "https://www.tnt.com/dam/tnt_express_media/global_media_library/images/customs-clearance/commercial-invoice-template-jan-18.pdf",
     "TNT commercial invoice template"),
    (DIGITAL, "Real_Invoice_EN_Livingston.pdf",
     "https://www.livingstonintl.com/livingston-content/uploads/2012/08/US-commercial-invoice.pdf",
     "Livingston International US commercial invoice"),

    # =============== INVOICES / FACTURES — FR ===============
    (DIGITAL, "Real_Invoice_FR_Grex_Facture_Export.pdf",
     "https://www.grex.fr/sites/g/files/mwbcuj1706/files/2024-01/Fiscalit%C3%A9_La%20facture%20commerciale%20export%20janvier%202024.pdf",
     "GREX facture commerciale export"),
    (DIGITAL, "Real_Invoice_FR_Ups.pdf",
     "https://www.ups.com/assets/resources/webcontent/fr_FR/invoice.pdf",
     "UPS facture commerciale FR"),
    (DIGITAL, "Real_Invoice_FR_Globalnegotiator.pdf",
     "https://globalnegotiator.com/files/documents-commerce-exterieur-mod%C3%A8le-exemple.pdf",
     "Global Negotiator documents commerce exterieur"),
    (DIGITAL, "Real_Invoice_FR_Noyon.pdf",
     "https://www.noyon.eu/wp-content/uploads/2020/11/3-Facture-Invoice.pdf",
     "Noyon modele facture commerciale proforma"),
    (DIGITAL, "Real_Invoice_FR_Swiftexp_Bilingual.pdf",
     "https://swiftexp.com/wp-content/uploads/2021/12/commercial_inv.pdf",
     "Swift Express facture commerciale bilingue"),
    (DIGITAL, "Real_Invoice_FR_Cbsa_Customs.pdf",
     "https://www.cbsa-asfc.gc.ca/publications/forms-formulaires/ci1.pdf",
     "CBSA Canada facture des douanes canadiennes"),
    (DIGITAL, "Real_Invoice_FR_fm6_Bon_Livraison.pdf",
     "https://fm6education.ma/wp-content/uploads/2021/05/Bon-de-livraison.pdf",
     "FM6 Education bon de livraison"),

    # =============== INSPECTION REPORTS — EN ===============
    (DIGITAL, "Real_InspectionReport_EN_LANL_Weld.pdf",
     "https://engstandards.lanl.gov/esm/welding/vol1/GWS%201-02-Att.3R1.pdf",
     "LANL weld inspection report form"),
    (SCANNED, "Real_InspectionReport_EN_Trinity_VT_Report.pdf",
     "https://trinityndt.com/wp-content/uploads/2026/01/Visual-Testing-Report-Format-Free-Download.pdf",
     "Trinity NDT visual testing report format"),

    # =============== RAPPORTS D'INSPECTION / CND — FR ===============
    (DIGITAL, "Real_InspectionReport_FR_Ifsttar_Auscultation.pdf",
     "http://www.ifsttar.fr/collections/CahiersInteractifs/CII1/pdfs/FicheB3-1-Guide_Auscultation_Ouvrage_Art-Cahier_Interactif_Ifsttar.pdf",
     "IFSTTAR guide auscultation ouvrage d'art"),
    (DIGITAL, "Real_InspectionReport_FR_Deltafluid_CND.pdf",
     "https://www.deltafluid.fr/files/Documents/deltafluid-cnd.pdf",
     "Delta Fluid guide controle non destructif"),
    (DIGITAL, "Real_InspectionReport_FR_Ndtnet_Cofrend.pdf",
     "https://www.ndt.net/article/cofrend2014/papers/ME2D3_G_CORNELOUP.pdf",
     "NDT.net COFREND 2014 conception CND"),
    (DIGITAL, "Real_InspectionReport_FR_Annaba_CND_Soudure.pdf",
     "https://biblio.univ-annaba.dz/ingeniorat/wp-content/uploads/2022/02/ilovepdf_merged-1.pdf",
     "Universite Annaba CND joints de soudure"),
]


def is_pdf(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(5) == b"%PDF-"
    except Exception:
        return False


def download(url: str, dst: Path) -> tuple[bool, str]:
    if dst.exists() and is_pdf(dst) and dst.stat().st_size > 1024:
        return True, "already exists, skipped"
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=30) as r:
            data = r.read()
        if len(data) < 1024:
            return False, f"too small ({len(data)} bytes) - likely HTML error page"
        if not data.startswith(b"%PDF-"):
            return False, "not a PDF (site may block scripted access)"
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
    for folder, name, url, notes in DOWNLOADS:
        dst = folder / name
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
        print("\nFailures (open in browser and Save-As manually if needed):")
        for url, rel, msg, notes in failures:
            print(f"  - {notes}\n    URL:  {url}\n    Dest: {rel}\n    Why:  {msg}")


if __name__ == "__main__":
    main()
