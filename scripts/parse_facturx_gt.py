"""Extract EXACT ground truth from embedded Factur-X / EN16931 XML.

Factur-X PDFs embed a UN/CEFACT Cross-Industry-Invoice (CII) XML with the
authoritative invoice data. Parsing it gives perfect 12-entity ground truth
(supplier, consumer, dates, SIRET, tax, totals, line items) — no OCR, no guess.

Updates docs/real_ground_truth.json in place for every facturx/securibox doc
that carries an embedded factur-x.xml.
"""

import csv
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
GT = ROOT / "docs" / "real_ground_truth.json"
PDF_DIR = ROOT / "data" / "pdf"


def local(tag):
    return tag.rsplit("}", 1)[-1]


def findall_local(root, name):
    return [e for e in root.iter() if local(e.tag) == name]


def first_text(root, name):
    for e in root.iter():
        if local(e.tag) == name and e.text and e.text.strip():
            return e.text.strip()
    return ""


def child_text(parent, name):
    for e in parent.iter():
        if local(e.tag) == name and e.text and e.text.strip():
            return e.text.strip()
    return ""


def fmt_date(s):
    s = (s or "").strip()
    if re.fullmatch(r"\d{8}", s):
        return f"{s[6:8]}/{s[4:6]}/{s[0:4]}"
    return s


def money(s):
    s = (s or "").strip().replace(" ", "")
    return f"{float(s):.2f}" if re.fullmatch(r"-?\d+(\.\d+)?", s) else s


def parse_cii(xml_bytes):
    root = ET.fromstring(xml_bytes)

    # parties
    def party_name(party_tag):
        for p in root.iter():
            if local(p.tag) == party_tag:
                return child_text(p, "Name")
        return ""

    supplier = party_name("SellerTradeParty")
    consumer = party_name("BuyerTradeParty")

    # SIRET: SellerTradeParty/SpecifiedLegalOrganization/ID
    siret = ""
    for p in root.iter():
        if local(p.tag) == "SellerTradeParty":
            for org in p.iter():
                if local(org.tag) == "SpecifiedLegalOrganization":
                    sid = child_text(org, "ID")
                    if re.fullmatch(r"\d{9,14}", re.sub(r"\D", "", sid)):
                        siret = re.sub(r"\D", "", sid)
            break

    inv_no = ""
    for ed in root.iter():
        if local(ed.tag) == "ExchangedDocument":
            inv_no = child_text(ed, "ID")
            break
    # issue date
    issue = ""
    for e in root.iter():
        if local(e.tag) == "IssueDateTime":
            issue = fmt_date(child_text(e, "DateTimeString"))
            break
    # due date
    due = ""
    for e in root.iter():
        if local(e.tag) == "DueDateDateTime":
            due = fmt_date(child_text(e, "DateTimeString"))
            break

    # tax (dedupe rates, sum calculated amounts)
    pcts, tax_sum = [], 0.0
    for tax in findall_local(root, "ApplicableTradeTax"):
        pct = child_text(tax, "RateApplicablePercent")
        amt = child_text(tax, "CalculatedAmount")
        if pct:
            p = re.sub(r"\.0+$", "", pct)
            if p not in pcts:
                pcts.append(p)
        try:
            tax_sum += float(amt)
        except (TypeError, ValueError):
            pass
    tva_pct = pcts[0] if len(pcts) == 1 else pcts
    tva_amt = f"{tax_sum:.2f}" if pcts else ""

    # totals
    grand = due_pay = ""
    for s in findall_local(root, "SpecifiedTradeSettlementHeaderMonetarySummation"):
        grand = money(child_text(s, "GrandTotalAmount"))
        due_pay = money(child_text(s, "DuePayableAmount"))

    # line items
    items = []
    for li in findall_local(root, "IncludedSupplyChainTradeLineItem"):
        name = qty = price = ""
        for e in li.iter():
            t = local(e.tag)
            if t == "Name" and not name and e.text:
                name = e.text.strip()
            elif t == "BilledQuantity" and e.text:
                qty = e.text.strip()
            elif t == "ChargeAmount" and not price and e.text:
                price = money(e.text)
        if name:
            items.append({"description": name, "quantity": qty, "unit_price": price})

    paid = (due_pay in ("0.00", "0")) and grand not in ("", "0.00")
    return {
        "supplier_name": supplier,
        "invoice_number": inv_no,
        "invoice_date": issue,
        "siret": siret,
        "echeance": due,
        "invoice_content": items,
        "tva_percentage": tva_pct,
        "tva_amount": tva_amt,
        "total_amount": grand,
        "payment_status": "PAID" if paid else "UNKNOWN",
        "solde_du": due_pay if (due_pay not in ("0.00", "0", "")) else "",
        "consumer_name": consumer,
    }


def main():
    man = {r["filename"]: Path(r["original_path"]).name
           for r in csv.DictReader(open(ROOT / "data" / "pdf_manifest.csv", encoding="utf-8"))}
    gt = json.loads(GT.read_text(encoding="utf-8"))

    updated = 0
    for p in sorted(PDF_DIR.glob("FR_invoice_real_*.pdf")):
        orig = man.get(p.name, "")
        if not ("facturx" in orig or "securibox" in orig):
            continue
        d = fitz.open(str(p))
        names = d.embfile_names()
        xml_name = next((n for n in names if n.lower().endswith(".xml")), None)
        if not xml_name:
            d.close()
            continue
        xml_bytes = d.embfile_get(xml_name)
        d.close()
        try:
            rec = parse_cii(xml_bytes)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {p.name}: parse failed ({exc})")
            continue
        rec["file_name"] = p.name
        rec["_source"] = "facturx_xml"
        gt[p.name] = rec
        updated += 1

    GT.write_text(json.dumps(gt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {updated} records from embedded Factur-X XML")


if __name__ == "__main__":
    main()
