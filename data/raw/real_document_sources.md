# Real Public Sample Document Sources

Starting points for real publicly-available industrial sample documents.
All PDFs and images under `data/raw/` that begin with `Real_` were downloaded
from sources in this list by the generator scripts (`download_real_docs.py`,
`download_real_images.py`).

> **Reality check:** Truly operational industrial documents (welding plans,
> fabrication sheets, material certs with real heat numbers) are almost
> never public — they're commercially sensitive. Most of what you find
> online is (a) the standard that defines them, (b) a blank template, or
> (c) a marketing/training sample. The `Synthetic_*` set fills the gaps
> and provides full ground truth for pipeline testing.

## Material Certificates (EN 10204 3.1 / 3.2)

### English
- [EN 10204 Standard PDF — Sanyo Steel](https://www.sanyosteel.com/files/EN/EN%2010204.pdf)
- [Sample Test Certificates — Blackmer/PSG Dover (Form 588)](https://www.psgdover.com/docs/default-source/blackmer-docs/application-forms/form588.pdf?sfvrsn=ba6dcb59_6)
- [Aero Metal Alliance — All Metals Test Certificates](https://aerometalsalliance.com/resources/data-sheets/view/Aero-Metal-Alliance_All-Metals-Test-Certificates_54.pdf)
- [ABS Cutsheet: EN 10204 Material Verification](https://ww2.eagle.org/content/dam/eagle/publications/cutsheets/EN%2010204%20Material%20Verification%20Cutsheet.pdf)
- [Intafast — Test certificates Introduction](https://www.intafast.com/wp-content/uploads/2019/04/Test-certificates.pdf)
- [Norsk Sveiseteknikk — 3.1 Inspection Certificate](https://en.nst.no/dokumenter/sertifikater/13A31001.pdf)
- [Acton Bright Steel — BS EN 10204 Certificate Types](https://www.actonbrightsteel.co.uk/datasheets/useful_information/bs_en_10204_certificate_types.pdf)
- Niedax mill test cert (scan)
- POSCO via Archro mill certificate
- Process Fittings 2.2 cert sample
- Eastern Metal Trading pipe mill certs (multi-page scan)

### French
- [Certificat de Réception 3.1 — La Robinetterie](https://www.larobinetterie.com/?action=certificats/get-certificat-pdf/134822&language=fr_FR&tmp_lang=O)
- [Certificat matière 3.1 (NF EN 10204) — les-certificats.net](https://les-certificats.net/certificat-matiere-3-1/)
- [Dillinger Hütte — Certificat de Réception 3.1 EN 10204](https://antelis-steel.com/document/certificat-de-reception-3-1_EN-10204-2004_ISO-10474-2013.pdf)
- [Certificats matière EN 10204 guide — EXAVO](https://exavo.fr/blog/certificats-matiere-en-10204-guide)
- [Certificat d'essai EN 10204 3.1 N°736145 — La Robinetterie](https://www.larobinetterie.com/?action=get-original-certificat-pdf/160629)
- Roc d'Acier 3.1 inox 304L
- Ugitech attestation signée (scan)

## Welding Plans / WPS / DMOS / QMOS

### English
- [AWS WPS Sample Form — D17.1](https://pubs.aws.org/content/free_downloads/WPS_Sample_Form-D17.1-D17.1M-2010-AMD1.pdf)
- [AWS D1.1 Annex N Form N-1 WPS](https://pubs.aws.org/content/free_downloads/Form_N1.pdf)
- [Sandvik — WPS SS-011-R2](https://www.mining.sandvik/siteassets/general-documents/download-center/ground-engaging-tools/product-welding-procedures/wps-ss-011-r2-wps-for-ha-50--32mm-ss2000--ss2300-material.pdf)
- [Ohio Gas Assoc — WPS Presentation by John Lucas](https://www.ohiogasassoc.org/wp/wp-content/uploads/2014/04/John-Lucas.pdf)
- [Force5 Ltd — Free WPS Templates](https://www.force5ltd.co.uk/welding-procedure-template/)
- ASME QW-483 PQR form
- FDOT D1.6 PQR digital form
- WPSAmerica PQR + WPQR samples (AWS D1.1)
- NFPA 13 aboveground piping cert

### French
- [CEREMA — QMOS/DMOS PDF](https://piles.cerema.fr/IMG/pdf/04c_qmos_dmos_cle0cd6d1.pdf)
- [Soudeurs.com — Comment rédiger un DMOS](https://www.soudeurs.com/site/comment-rediger-une-fiche-de-descriptif-de-mode-operatoire-de-soudage-dmos-202/)
- [Rocd@cier — Rédiger un DMOS](https://www.rocdacier.com/rediger-un-dmos/)
- [Axxair — DMOS et QMOS explication](https://www.axxair.com/fr/blog/dmos-et-qmos-descriptif-et-qualification-des-modes-operatoires-de-soudage)
- Axxair QMOS TIG guide
- CEWAC DMOS/QMOS sample
- Austech QS/DMOS
- IS Groupe DMOS/cahier guides
- Formation-Soudure training doc
- France Gaz AFG spec
- Union Métalliers EN 1090
- Goulet lecture de plans en soudage
- Cahier de soudage filtres/séparateurs (multi-piece scan)

## Fabrication Sheets / Bill of Materials

- [Smartsheet — Free BOM Templates](https://www.smartsheet.com/free-bill-of-materials-templates)
- [DOE — Detailed Design Package Module 2A: BOM and BOP](https://www.energy.gov/sites/default/files/2021-07/Module_2A.pdf)
- [TemplateLab — 48 Free BOM Templates](https://templatelab.com/bill-of-materials/)
- [LearnMech — Engineering BOM template download](https://learnmech.com/engineering-bill-material-template-word-excel-download/)
- [TranZact — BOM format PDF/Excel/Word](https://letstranzact.com/bill-of-materials-format)

## Invoices

### English
- Tennant commercial invoice template
- Baxter Freight commercial invoice
- TNT commercial invoice
- Livingston international commercial invoice

### French
- GREX — facture export
- UPS France — facture commerciale
- Global Negotiator — facture modèle
- Noyon — exemple facture
- SwiftExp — facture commerciale
- CBSA — facture douanière
- FM6 — facture commerciale

## Inspection Reports

### English
- LANL Weld Inspection Report (Los Alamos National Lab)
- Trinity NDT visual inspection report

### French
- IFSTTAR — Auscultation / rapport d'inspection
- Delta Fluid — rapport de contrôle
- NDT.net COFREND — rapport de contrôle
- Annaba — rapport d'inspection

## Public datasets referenced in the proposal (for Milestones 2+)

- **FUNSD dataset** (scanned forms with NER labels) — https://guillaumejaume.github.io/FUNSD/
- **CORD dataset** (structured receipts/invoices) — https://github.com/clovaai/cord
- **RVL-CDIP** (400K scanned document images, 16 classes incl. invoices, specifications) — https://adamharley.com/rvl-cdip/

## Adding new real documents

1. Add the URL + target filename to the `DOWNLOADS` list in
   `generator/download_real_docs.py` (or `download_real_images.py` for images).
2. Re-run the script — it's idempotent and skips files that already exist:
   ```bash
   python generator/download_real_docs.py
   ```
3. Open the downloaded file and add a row to the ground-truth spreadsheet
   at `docs/ground_truth.csv` (Task 2).

Always check the source's licensing before commercial reuse. Most templates
are free; some standards (ISO/EN full texts) are copyrighted and may only
be referenced.
