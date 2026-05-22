# Label Studio Setup — Milestone 2 (Task 03)

Annotation tool for labelling French invoices with the **12 entities** defined in
[entity_schema.md](entity_schema.md). Person 2 sets this up; Person 1 does the
annotation (Task 05).

## 1. Install

```bash
pip install label-studio
```

(Already in `requirements.txt`. Use the project virtualenv.)

## 2. Start the server

```bash
label-studio start
```

Opens at **http://localhost:8080**. On first run, create a local account
(email + password) — this is the login you share with Person 1.

## 3. Create the project

**Option A — automatic (recommended).** With the server running, copy your token
from *Account & Settings > Access Token*, then:

```bash
set LABEL_STUDIO_URL=http://localhost:8080
set LABEL_STUDIO_TOKEN=<your-token>
python label_studio/bootstrap_project.py
```

This creates the project, applies the 12-label config, and imports a test task.

**Option B — manual (matches the spec steps).**
1. *Create Project* → name it `FR Invoice M2 — 12 Entities`.
2. *Labeling Setup* → *Natural Language Processing* → **Named Entity Recognition**.
3. *Labeling Interface* → *Code* → paste the contents of
   [`label_studio/label_config.xml`](../label_studio/label_config.xml).
4. Save.

## 4. The 12 labels

Exactly 12, matching the schema output keys:

| Label | Schema key |
|-------|-----------|
| `SUPPLIER_NAME` | supplier_name |
| `CONSUMER_NAME` | consumer_name *(new in M2)* |
| `INVOICE_NUMBER` | invoice_number |
| `INVOICE_DATE` | invoice_date |
| `SIRET` | siret |
| `ECHEANCE` | echeance |
| `INVOICE_CONTENT` | invoice_content |
| `TVA_PERCENTAGE` | tva_percentage |
| `TVA_AMOUNT` | tva_amount |
| `TOTAL_AMOUNT` | total_amount |
| `PAYMENT_STATUS` | payment_status |
| `SOLDE_DU` | solde_du |

> **Consumer vs Supplier:** the consumer block is the one under
> `DESTINATAIRE` / `FACTURÉ À` / `CLIENT` / `ACHETEUR` / `POUR LE COMPTE DE`.
> The supplier is the header / letterhead at the top.

## 5. Test it

Import [`label_studio/test_task.json`](../label_studio/test_task.json) (done
automatically by Option A) and label a few spans — supplier, consumer, invoice
number, total — to confirm the interface works. Then have Person 1 log in and
label the same task before full annotation (Task 05) begins.

## Output of this task
- Label Studio installed and running.
- Project created with all **12** labels configured.
- One test invoice imported and label-able.
- Login shared with Person 1.
