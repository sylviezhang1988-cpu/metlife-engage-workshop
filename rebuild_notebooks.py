#!/usr/bin/env python3
"""Emit the 5 attendee notebooks for the MetLife Engage workshop."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent


def md(source: str) -> dict:
    lines = [line + "\n" for line in source.strip("\n").split("\n")]
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    return {"cell_type": "markdown", "metadata": {}, "source": lines}


def code(source: str) -> dict:
    lines = [line + "\n" for line in source.strip("\n").split("\n")]
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines,
    }


def notebook(cells: list) -> dict:
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
            "application/vnd.databricks.v1+notebook": {
                "dashboards": [],
                "language": "python",
                "notebookMetadata": {"pythonIndentUnit": 4},
                "notebookName": "",
                "widgets": {},
            },
        },
        "cells": cells,
    }


def write(name: str, cells: list) -> None:
    path = ROOT / name
    path.write_text(json.dumps(notebook(cells), indent=1) + "\n")
    print("wrote", path.name, f"({len(cells)} cells)")


# ---------------------------------------------------------------------------
# 00_setup
# ---------------------------------------------------------------------------
write(
    "00_setup.ipynb",
    [
        md(
            """# 00 · Setup

## Theme — before / after

| Today | After this workshop |
|-------|---------------------|
| An analyst chats the same duplicate-claims question every Monday | Genie One runs it on a schedule |
| Someone re-parses claim PDFs on demand | Bronze → silver → gold tables, queried many times |
| Each analyst invents “approval rate” | One metric view everyone shares |

**Use AI to build the repeatable process, not to be the process.**

## How to start

1. Run the **next cell** once — widgets appear at the top.
2. Set **catalog** to an existing catalog you can `USE`. Schema may stay `metlife_claims`.
3. Run All (or the remaining cells).

Your catalog and schema are saved next to these notebooks as `.workshop_config.json`, so `01`–`04` reuse them. If several people share one folder, you will overwrite each other’s config — set the widgets again if that happens.

- This notebook does **not** create a catalog.
- Run on **serverless**. Do not create a classic cluster.
"""
        ),
        code(
            """dbutils.widgets.text("catalog", "")
dbutils.widgets.text("schema", "metlife_claims")
dbutils.widgets.dropdown("create_schema_if_missing", "true", ["true", "false"])
print("Widgets ready — set catalog at the top, then run the next cell.")
"""
        ),
        code(
            """import json, os, re

CONFIG = os.path.join(os.getcwd(), ".workshop_config.json")

CATALOG = dbutils.widgets.get("catalog").strip().strip("`")
SCHEMA = dbutils.widgets.get("schema").strip().strip("`")
CREATE_SCHEMA = dbutils.widgets.get("create_schema_if_missing") == "true"

if not CATALOG and os.path.exists(CONFIG):
    saved = json.load(open(CONFIG))
    CATALOG = saved.get("catalog", "")
    SCHEMA = saved.get("schema", SCHEMA)
    CREATE_SCHEMA = saved.get("create_schema_if_missing", CREATE_SCHEMA)
    print(f"Using settings saved by 00_setup: {CATALOG}.{SCHEMA}")

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
assert CATALOG, (
    "Set the catalog widget at the top of this notebook to an existing catalog you can USE, "
    "then run again. (Run 00_setup first so 01-04 can reuse it.)"
)
assert SCHEMA, "Set the schema widget (default metlife_claims is fine)."
assert IDENT.match(CATALOG) and IDENT.match(SCHEMA), (
    "catalog and schema must be Unity Catalog identifiers "
    "(start with a letter or underscore; letters, digits, underscore only)."
)
print(f"Target: {CATALOG}.{SCHEMA}")
"""
        ),
        code(
            """def uc(name: str) -> str:
    return "`" + name.replace("`", "") + "`"

if CREATE_SCHEMA:
    try:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {uc(CATALOG)}.{uc(SCHEMA)}")
        print(f"Schema ready: {CATALOG}.{SCHEMA}")
    except Exception as e:
        print(f"Could not CREATE SCHEMA (ok if it already exists and you lack CREATE): {e}")

try:
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {uc(CATALOG)}.{uc(SCHEMA)}.claim_docs")
    print(f"Volume ready: /Volumes/{CATALOG}/{SCHEMA}/claim_docs")
except Exception as e:
    print(f"Could not CREATE VOLUME (ok if already provisioned): {e}")

spark.sql(f"USE CATALOG {uc(CATALOG)}")
spark.sql(f"USE SCHEMA {uc(SCHEMA)}")
print("Current catalog/schema:", spark.sql("SELECT current_catalog(), current_schema()").collect()[0])

VOLUME = f"/Volumes/{CATALOG}/{SCHEMA}/claim_docs"
PDF_DIR = f"{VOLUME}/pdfs"
print(f"Volume path: {VOLUME}")

try:
    json.dump(
        {"catalog": CATALOG, "schema": SCHEMA, "create_schema_if_missing": CREATE_SCHEMA},
        open(CONFIG, "w"),
    )
    print("Saved catalog/schema for notebooks 01-04.")
except Exception as e:
    print(f"Could not save settings (set the widgets in each notebook instead): {e}")
"""
        ),
        md(
            """If the `USE` cell fails, you do not have access to that catalog/schema. Stop and get the account team to grant `USE CATALOG` / `USE SCHEMA` / `CREATE TABLE` before continuing."""
        ),
    ],
)

# ---------------------------------------------------------------------------
# 01_build_workshop_data (facilitator)
# ---------------------------------------------------------------------------
write(
    "01_build_workshop_data.ipynb",
    [
        md(
            """# 01 · Build workshop data (facilitator)

**Facilitator notebook.** Run once before attendees start (or have them watch you run it).

Creates:
1. Synthetic claims tables (~700 claims, planted duplicates, PH0013 sibling trap)
2. PK / FK constraints so Genie can pick up joins
3. Twelve pet-claim PDFs on the `claim_docs` volume (Sparky / Pine Vet planted pair)
4. The four `CLM-PET-*` rows inside `claims`, so the PDF duplicate was also **Paid**

`random.seed(42)` keeps counts stable. Duplicate definition: same `pet_id + clinic_id + visit_date`.
"""
        ),
        code("%run ./00_setup\n"),
        code(
            """from workshop_data import generate

tables = generate()
for name, rows in tables.items():
    spark.createDataFrame(rows).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(name)
    print(name, len(rows))
"""
        ),
        md("## Primary / foreign keys (Genie uses these as joins)"),
        code(
            """# Informational PK/FK — Genie reads these as suggested joins.
pk_fk = [
    "ALTER TABLE policyholders DROP CONSTRAINT IF EXISTS pk_policyholders",
    "ALTER TABLE pets DROP CONSTRAINT IF EXISTS pk_pets",
    "ALTER TABLE policies DROP CONSTRAINT IF EXISTS pk_policies",
    "ALTER TABLE vet_clinics DROP CONSTRAINT IF EXISTS pk_vet_clinics",
    "ALTER TABLE claims DROP CONSTRAINT IF EXISTS pk_claims",
    "ALTER TABLE claim_payments DROP CONSTRAINT IF EXISTS pk_claim_payments",
    "ALTER TABLE pets DROP CONSTRAINT IF EXISTS fk_pets_policyholder",
    "ALTER TABLE policies DROP CONSTRAINT IF EXISTS fk_policies_pet",
    "ALTER TABLE policies DROP CONSTRAINT IF EXISTS fk_policies_policyholder",
    "ALTER TABLE claims DROP CONSTRAINT IF EXISTS fk_claims_policy",
    "ALTER TABLE claims DROP CONSTRAINT IF EXISTS fk_claims_pet",
    "ALTER TABLE claims DROP CONSTRAINT IF EXISTS fk_claims_clinic",
    "ALTER TABLE claim_payments DROP CONSTRAINT IF EXISTS fk_payments_claim",
    "ALTER TABLE policyholders ADD CONSTRAINT pk_policyholders PRIMARY KEY (policyholder_id)",
    "ALTER TABLE pets ADD CONSTRAINT pk_pets PRIMARY KEY (pet_id)",
    "ALTER TABLE policies ADD CONSTRAINT pk_policies PRIMARY KEY (policy_id)",
    "ALTER TABLE vet_clinics ADD CONSTRAINT pk_vet_clinics PRIMARY KEY (clinic_id)",
    "ALTER TABLE claims ADD CONSTRAINT pk_claims PRIMARY KEY (claim_id)",
    "ALTER TABLE claim_payments ADD CONSTRAINT pk_claim_payments PRIMARY KEY (payment_id)",
    "ALTER TABLE pets ADD CONSTRAINT fk_pets_policyholder FOREIGN KEY (policyholder_id) REFERENCES policyholders(policyholder_id)",
    "ALTER TABLE policies ADD CONSTRAINT fk_policies_pet FOREIGN KEY (pet_id) REFERENCES pets(pet_id)",
    "ALTER TABLE policies ADD CONSTRAINT fk_policies_policyholder FOREIGN KEY (policyholder_id) REFERENCES policyholders(policyholder_id)",
    "ALTER TABLE claims ADD CONSTRAINT fk_claims_policy FOREIGN KEY (policy_id) REFERENCES policies(policy_id)",
    "ALTER TABLE claims ADD CONSTRAINT fk_claims_pet FOREIGN KEY (pet_id) REFERENCES pets(pet_id)",
    "ALTER TABLE claims ADD CONSTRAINT fk_claims_clinic FOREIGN KEY (clinic_id) REFERENCES vet_clinics(clinic_id)",
    "ALTER TABLE claim_payments ADD CONSTRAINT fk_payments_claim FOREIGN KEY (claim_id) REFERENCES claims(claim_id)",
]
for stmt in pk_fk:
    try:
        spark.sql(stmt)
    except Exception as e:
        print("skip:", stmt.split()[2] if "CONSTRAINT" in stmt else stmt[:40], "→", e)
print("PK/FK applied (best-effort).")
"""
        ),
        md("## Table comments"),
        code(
            """comments = [
    "COMMENT ON TABLE claims IS 'One row per submitted claim. Contains some duplicate submissions for the same pet, clinic, and visit date.'",
    "ALTER TABLE claims ALTER COLUMN claim_id COMMENT 'Unique claim ID. A resubmission of the same visit gets a NEW claim_id.'",
    "ALTER TABLE claims ALTER COLUMN invoice_number COMMENT 'Clinic invoice number as submitted; resubmissions may reuse or alter it. Do not treat as a unique key.'",
    "ALTER TABLE claims ALTER COLUMN pet_id COMMENT 'The pet treated on this visit. Duplicates are same pet_id + clinic_id + visit_date.'",
    "ALTER TABLE claims ALTER COLUMN denial_reason COMMENT 'Populated when claim_status = Denied. Use Duplicate claim for caught resubmissions.'",
    "COMMENT ON TABLE claim_payments IS 'Payouts issued for claims with status Paid. Join to claims on claim_id.'",
    "COMMENT ON TABLE policies IS 'One row per pet insurance policy. reimbursement_rate is a decimal (0.80 = 80%).'",
    "COMMENT ON TABLE pets IS 'Insured pets. Multiple pets can share a policyholder_id (household).'",
    "COMMENT ON TABLE policyholders IS 'Customers. policyholder_id is the household key.'",
    "COMMENT ON TABLE vet_clinics IS 'Clinics that submitted claims.'",
    "COMMENT ON TABLE earned_premium_monthly IS 'Earned premium by policy and month. Use with claim_payments for loss ratio.'",
    "COMMENT ON TABLE investment_holdings IS 'Synthetic portfolio snapshot as of 2026-09-30. Stretch content only.'",
]
for stmt in comments:
    spark.sql(stmt)
print("Comments applied.")
"""
        ),
        md("## Answer key + duplicate view"),
        code(
            """spark.sql(\"\"\"
CREATE OR REPLACE VIEW v_suspected_duplicate_claims AS
WITH ranked AS (
  SELECT c.*,
    ROW_NUMBER() OVER (PARTITION BY pet_id, clinic_id, visit_date ORDER BY submitted_date, claim_id) AS visit_rank,
    FIRST_VALUE(claim_id) OVER (PARTITION BY pet_id, clinic_id, visit_date ORDER BY submitted_date, claim_id) AS original_claim_id
  FROM claims c
)
SELECT * FROM ranked WHERE visit_rank > 1
\"\"\")

print("=== Facilitator answer key ===")
display(spark.sql(\"\"\"
SELECT
  COUNT(*) AS suspected_duplicates,
  COUNT_IF(d.claim_status = 'Paid') AS duplicates_paid,
  COUNT_IF(d.claim_status = 'Denied' AND d.denial_reason = 'Duplicate claim') AS duplicates_caught,
  ROUND(SUM(p.payment_amount), 2) AS leakage_usd
FROM v_suspected_duplicate_claims d
LEFT JOIN claim_payments p USING (claim_id)
\"\"\"))

print("Planted PDF claims in claims table:")
display(spark.sql(\"\"\"
SELECT claim_id, pet_id, clinic_id, visit_date, invoice_number, claim_status, claimed_amount
FROM claims
WHERE claim_id LIKE 'CLM-PET-%'
ORDER BY claim_id
\"\"\"))

print("PH0013 trap check (sibling pets same day — should NOT be duplicates):")
display(spark.sql(\"\"\"
SELECT c.claim_id, c.pet_id, p.policyholder_id, c.clinic_id, c.visit_date, c.claim_status
FROM claims c
JOIN pets p USING (pet_id)
WHERE p.policyholder_id = 'PH0013'
ORDER BY c.visit_date, c.pet_id
\"\"\"))
print("Real duplicates for PH0013 (expect 0 rows):")
display(spark.sql(\"\"\"
SELECT d.*
FROM v_suspected_duplicate_claims d
JOIN pets p USING (pet_id)
WHERE p.policyholder_id = 'PH0013'
\"\"\"))
"""
        ),
        md("## Generate claim PDFs → volume"),
        code(
            """from pathlib import Path
from generate_pet_claim_pdfs import generate

dest = Path(PDF_DIR)
written = generate(dest)
print(f"Wrote {len(written)} PDFs under {dest}")
for p in written:
    print(" ", p.relative_to(dest) if dest in p.parents or str(p).startswith(str(dest)) else p)

display(spark.sql(f\"\"\"
SELECT path, length, modificationTime
FROM read_files('{PDF_DIR}', format => 'binaryFile')
WHERE path LIKE '%.pdf'
ORDER BY path
\"\"\"))
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# 02_genie_agent
# ---------------------------------------------------------------------------
write(
    "02_genie_agent.ipynb",
    [
        md(
            """# 02 · Genie Agent + Genie One

Build a trusted Genie Agent on the workshop tables, then schedule the Monday question in Genie One.

Everything you need to paste into the Genie UI is **in this notebook** — tables, joins, instructions, and example SQL with your real catalog/schema.

**Ends with:** a Genie One scheduled report (Lab B).
"""
        ),
        code("%run ./00_setup\n"),
        md(
            """## Known-good queries

Duplicate = later claim for the same `pet_id + clinic_id + visit_date`. Invoice number is **not** the key.
Sibling pets on the same day are **not** duplicates (trap: household **PH0013**).
"""
        ),
        code(
            """spark.sql(\"\"\"
CREATE OR REPLACE VIEW v_suspected_duplicate_claims AS
WITH ranked AS (
  SELECT c.*,
    ROW_NUMBER() OVER (PARTITION BY pet_id, clinic_id, visit_date ORDER BY submitted_date, claim_id) AS visit_rank,
    FIRST_VALUE(claim_id) OVER (PARTITION BY pet_id, clinic_id, visit_date ORDER BY submitted_date, claim_id) AS original_claim_id,
    FIRST_VALUE(claim_status) OVER (PARTITION BY pet_id, clinic_id, visit_date ORDER BY submitted_date, claim_id) AS original_status
  FROM claims c
)
SELECT * FROM ranked WHERE visit_rank > 1
\"\"\")
print("view ready")
"""
        ),
        code(
            """display(spark.sql(\"\"\"
SELECT
  COUNT(*) AS suspected_duplicates,
  COUNT_IF(d.claim_status = 'Paid') AS duplicates_paid,
  COUNT_IF(d.claim_status = 'Denied' AND d.denial_reason = 'Duplicate claim') AS duplicates_caught,
  ROUND(SUM(p.payment_amount), 2) AS leakage_usd
FROM v_suspected_duplicate_claims d
LEFT JOIN claim_payments p USING (claim_id)
\"\"\"))
"""
        ),
        code(
            """display(spark.sql(\"\"\"
SELECT v.clinic_name, COUNT(*) AS suspected_duplicates
FROM v_suspected_duplicate_claims d
JOIN vet_clinics v USING (clinic_id)
GROUP BY v.clinic_name
ORDER BY suspected_duplicates DESC
LIMIT 10
\"\"\"))
"""
        ),
        code(
            """# Trap: PH0013 — sibling pets same clinic/day. Correct Genie answer: no duplicates.
display(spark.sql(\"\"\"
SELECT c.claim_id, c.pet_id, p.policyholder_id, c.clinic_id, c.visit_date, c.claim_status
FROM claims c
JOIN pets p USING (pet_id)
WHERE p.policyholder_id = 'PH0013'
ORDER BY c.visit_date, c.pet_id
\"\"\"))
"""
        ),
        md("## Metric view"),
        code(
            """spark.sql(\"\"\"
CREATE OR REPLACE VIEW claims_metrics
WITH METRICS LANGUAGE YAML AS $$
version: 1.1
source: claims
joins:
  - name: policies
    source: policies
    on: source.policy_id = policies.policy_id
dimensions:
  - name: submitted_month
    expr: DATE_TRUNC('MONTH', submitted_date)
  - expr: diagnosis_category
  - expr: claim_status
  - expr: submission_channel
  - name: plan_tier
    expr: policies.plan_tier
measures:
  - name: claim_count
    expr: COUNT(DISTINCT claim_id)
  - name: approval_rate
    expr: COUNT_IF(claim_status IN ('Approved','Paid')) / NULLIF(COUNT_IF(claim_status IN ('Approved','Paid','Denied')), 0)
    format:
      type: percentage
  - name: denial_rate
    expr: COUNT_IF(claim_status = 'Denied') / NULLIF(COUNT_IF(claim_status IN ('Approved','Paid','Denied')), 0)
    format:
      type: percentage
  - name: avg_days_to_decision
    expr: AVG(DATEDIFF(decision_date, submitted_date))
    synonyms: [processing time, time to settle]
  - name: open_claims
    expr: COUNT_IF(claim_status IN ('Submitted','In Review'))
  - name: total_claimed
    expr: SUM(claimed_amount)
    format:
      type: currency
      currency_code: USD
$$
\"\"\")
display(spark.sql(\"\"\"
SELECT diagnosis_category, MEASURE(approval_rate), MEASURE(avg_days_to_decision)
FROM claims_metrics
GROUP BY ALL
ORDER BY 1
\"\"\"))
"""
        ),
        md(
            """## Build the Genie Agent (UI)

1. **New → Genie Agent**
2. Add tables (run the next cell for the exact names):
   - `claims`, `claim_payments`, `policies`, `pets`, `policyholders`, `vet_clinics`
   - optional: `claims_metrics`, `earned_premium_monthly`
3. **Joins** — if PK/FKs from notebook 01 did not appear automatically:
   **Configure → Examples → Add → Joins**, then add:
   - claims → policies on `policy_id`
   - claims → pets on `pet_id`
   - claims → vet_clinics on `clinic_id`
   - claim_payments → claims on `claim_id`
   - pets → policyholders on `policyholder_id`
4. Paste **instructions** and **example SQL** from the cells below (self-contained CTEs — Genie cannot see `v_suspected_duplicate_claims` unless you add that view).
"""
        ),
        code(
            """print("=== Tables to add ===")
for t in [
    "claims", "claim_payments", "policies", "pets", "policyholders", "vet_clinics",
    "claims_metrics", "earned_premium_monthly",
]:
    print(f"  {CATALOG}.{SCHEMA}.{t}")

instructions = f\"\"\"This agent analyzes synthetic pet insurance claim data. All amounts are USD.

Duplicate (double) claim = a second or later claim for the same vet visit: same pet_id, clinic_id, visit_date.
The earliest submitted claim is the original. Do NOT rely on invoice_number or claimed_amount;
resubmissions reuse, suffix, or change them. Two different pets from one household on the same day are NOT duplicates.

Leakage = suspected duplicate with status Paid. Caught = denied with reason 'Duplicate claim'.
Open = Submitted or In Review. Decided = Approved, Paid, or Denied.
Approval and denial rates use decided claims only; show as percentages.
Processing time = average days from submitted_date to decision_date.
Reimbursement rate is a decimal; show it as a percentage.
\"\"\"
print("\\n=== Instructions (paste) ===\\n")
print(instructions)

fq = f"{CATALOG}.{SCHEMA}"
q1 = f\"\"\"WITH ranked AS (
  SELECT c.*,
    ROW_NUMBER() OVER (PARTITION BY pet_id, clinic_id, visit_date ORDER BY submitted_date, claim_id) AS visit_rank
  FROM {fq}.claims c
)
SELECT COUNT(*) AS suspected_duplicates,
  COUNT_IF(d.claim_status = 'Paid') AS duplicates_paid,
  ROUND(SUM(p.payment_amount), 2) AS leakage_usd
FROM ranked d
LEFT JOIN {fq}.claim_payments p USING (claim_id)
WHERE visit_rank > 1
\"\"\"
q2 = f\"\"\"WITH ranked AS (
  SELECT c.*,
    ROW_NUMBER() OVER (PARTITION BY pet_id, clinic_id, visit_date ORDER BY submitted_date, claim_id) AS visit_rank
  FROM {fq}.claims c
)
SELECT v.clinic_name, COUNT(*) AS suspected_duplicates
FROM ranked d
JOIN {fq}.vet_clinics v USING (clinic_id)
WHERE visit_rank > 1
GROUP BY v.clinic_name
ORDER BY suspected_duplicates DESC
LIMIT 10
\"\"\"
q3 = f\"\"\"WITH ranked AS (
  SELECT c.*, p.policyholder_id,
    ROW_NUMBER() OVER (PARTITION BY c.pet_id, c.clinic_id, c.visit_date ORDER BY c.submitted_date, c.claim_id) AS visit_rank
  FROM {fq}.claims c
  JOIN {fq}.pets p USING (pet_id)
  WHERE p.policyholder_id = 'PH0013'
)
SELECT claim_id, pet_id, clinic_id, visit_date, claim_status
FROM ranked
WHERE visit_rank > 1
\"\"\"
print("\\n=== Example SQL 1 — leakage ===\\n")
print(q1)
print("\\n=== Example SQL 2 — clinics ===\\n")
print(q2)
print("\\n=== Example SQL 3 — trap PH0013 (expect 0 rows) ===\\n")
print(q3)
"""
        ),
        md(
            """## Benchmark questions

1. How many suspected duplicate claims are there, and how much did we pay on them?
2. Which clinics have the most double submissions?
3. What is the approval rate by diagnosis category?
4. What is the average processing time by submission channel?
5. What is the loss ratio by plan tier for 2025?
6. **Trap:** Show duplicates for household **PH0013**. Expected: **none** (sibling pets, not duplicates).
"""
        ),
        md(
            """## Your turn — Lab A · Genie Agent (15 min)

Add your own instruction that fixes one wrong answer. Rerun a benchmark question and confirm the answer changed.

Suggested fail: ask *Show duplicates for household PH0013* on an agent **without** the sibling-pet instruction, then add it.
"""
        ),
        md(
            """## Your turn — Lab B · Genie One (10 min) — leave this running

In Genie One, ask:

> Every Monday at 8am, send me last week's suspected duplicate claims, how many were paid, total leakage, and approval rate by diagnosis.

Then **schedule** it. This is the automated outcome for Module 1.
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# 03_genie_code
# ---------------------------------------------------------------------------
write(
    "03_genie_code.ipynb",
    [
        md(
            """# 03 · Genie Code

Use Genie Code in the notebook to write a **reusable** duplicate rule once. Ask for the plan first. Ask for a SQL function or job — not a one-off answer.

**Single definition of duplicate** (reuse this everywhere):

> Same `pet_id + clinic_id + visit_date`. Earliest `submitted_date` is the original. Invoice number is not the key.

**Ends with:** a scheduled job that runs `flag_duplicate_claims()` (you build it — no starter files).

If Unity AI Gateway / Genie Code CLI is not enabled, stay in the workspace. The workshop still works.
"""
        ),
        code("%run ./00_setup\n"),
        md(
            """## Canonical function (reference)

After Genie Code drafts something, converge on this shape. Genie Agent example SQL and any job should call the **same** rule.
"""
        ),
        code(
            """# Reference implementation — attendees should rebuild via Genie Code (Lab C),
# then schedule a job that calls this (or equivalent) daily.
spark.sql(f\"\"\"
CREATE OR REPLACE FUNCTION flag_duplicate_claims()
RETURNS TABLE (
  claim_id STRING,
  original_claim_id STRING,
  pet_id STRING,
  clinic_id STRING,
  visit_date DATE,
  invoice_number STRING,
  claimed_amount DOUBLE,
  claim_status STRING,
  visit_rank INT
)
RETURN
WITH ranked AS (
  SELECT
    c.claim_id,
    FIRST_VALUE(c.claim_id) OVER (
      PARTITION BY c.pet_id, c.clinic_id, c.visit_date
      ORDER BY c.submitted_date, c.claim_id
    ) AS original_claim_id,
    c.pet_id,
    c.clinic_id,
    c.visit_date,
    c.invoice_number,
    c.claimed_amount,
    c.claim_status,
    ROW_NUMBER() OVER (
      PARTITION BY c.pet_id, c.clinic_id, c.visit_date
      ORDER BY c.submitted_date, c.claim_id
    ) AS visit_rank
  FROM {CATALOG}.{SCHEMA}.claims c
)
SELECT * FROM ranked WHERE visit_rank > 1
\"\"\")
display(spark.sql(f"SELECT * FROM flag_duplicate_claims() LIMIT 20"))
print("function ready — wire this into a daily job next")
"""
        ),
        md(
            """## Workspace prompts (paste into Genie Code)

**1. Explore**

> Profile every table in `{catalog}.{schema}`: row counts, null rates, key columns, and the join keys between them.

**2. Build the rule**

> Write a reusable SQL function `flag_duplicate_claims()` that returns claims where the same pet, clinic, and visit date were already claimed. Explain why invoice number is not reliable. Match the definition: pet_id + clinic_id + visit_date, earliest submitted_date wins.

**3. Job**

> Create a Databricks Job that runs daily, calls `flag_duplicate_claims()`, and writes results to `claims_flagged`. Show me the plan first. Do not invent a different duplicate definition.

**4. Actuarial (stretch)**

> Build a monthly loss-ratio table by plan tier from `claim_payments` and `earned_premium_monthly`, plus a data-quality check.

**5. Investments (stretch)**

> Query `investment_holdings` for market-value-weighted yield and duration by asset class.
"""
        ),
        code(
            """print(f"Catalog.schema for prompts: {CATALOG}.{SCHEMA}")
"""
        ),
        md(
            """## Your turn — Lab C · Genie Code (20 min)

Use Genie Code to build **one** of:

1. `flag_duplicate_claims()` (if you have not already) **and** a daily job that writes `claims_flagged`
2. A monthly loss-ratio table by plan tier
3. Weighted duration / yield by asset class on `investment_holdings`

Ask for the plan first. Constrain with `LIMIT` until the query is right.

**Automated outcome:** leave the duplicate job scheduled (or show the job definition ready to schedule).
"""
        ),
        md(
            """## Optional CLI (skip if Gateway is not live)

```bash
curl -fsSL https://github.com/databricks/genie-code-cli/releases/latest/download/install.sh | bash
genie --version
genie
```

Same task: create the daily job against `{catalog}.{schema}` that materializes `claims_flagged` from `flag_duplicate_claims()`.
"""
        ),
    ],
)

# ---------------------------------------------------------------------------
# 04_ai_on_claim_pdfs
# ---------------------------------------------------------------------------
write(
    "04_ai_on_claim_pdfs.ipynb",
    [
        md(
            """# 04 · AI Functions on claim PDFs

One notebook, three layers. About 12 PDFs, roughly two minutes of AI Functions time.

| Layer | What | Tables |
|-------|------|--------|
| Bronze | `ai_parse_document` | `bronze_pdf_files`, `bronze_parsed_pdfs`, `bronze_parsed_text` |
| Silver | `ai_classify` + `ai_extract` | `silver_claim_documents`, `silver_claim_documents_typed` |
| Gold | metrics + Genie | `gold_clinic_invoices`, `gold_suspected_pdf_duplicates`, metric view |

**Planted duplicate:** Sparky · Pine Vet Clinic · `2026-08-03` · `CLM-PET-00044` / `CLM-PET-00045` (both Paid in `claims`).  
Bella is a waiting-period denial — not a duplicate.

**Prerequisite:** notebook `01_build_workshop_data` already wrote PDFs to `{PDF_DIR}`.
"""
        ),
        code("%run ./00_setup\n"),
        md("## Bronze — register + parse"),
        code(
            """spark.sql(f\"\"\"
CREATE OR REPLACE TABLE bronze_pdf_files
COMMENT 'Binary PDF registry for pet-insurance claim packets'
AS
SELECT
  path,
  modificationTime,
  length,
  content,
  regexp_extract(path, '(CLM-PET-[0-9]+)', 1) AS claim_id,
  element_at(split(path, '/'), -1) AS file_name
FROM read_files('{PDF_DIR}', format => 'binaryFile')
WHERE path LIKE '%.pdf'
\"\"\")
display(spark.sql("SELECT claim_id, file_name, length FROM bronze_pdf_files ORDER BY claim_id, file_name"))
print("rows", spark.table("bronze_pdf_files").count())
"""
        ),
        code(
            """spark.sql(\"\"\"
CREATE OR REPLACE TABLE bronze_parsed_pdfs
COMMENT 'ai_parse_document VARIANT output (v2.0) for pet-claim PDFs'
AS
SELECT
  claim_id,
  file_name,
  path,
  length,
  modificationTime,
  ai_parse_document(
    content,
    map('version', '2.0', 'descriptionElementTypes', '')
  ) AS parsed
FROM bronze_pdf_files
\"\"\")
# Do not display the VARIANT column — Spark Connect cannot materialize it in the notebook UI.
display(spark.sql(\"\"\"
SELECT claim_id, file_name, length, typeof(parsed) AS parsed_type
FROM bronze_parsed_pdfs
ORDER BY claim_id, file_name
\"\"\"))
"""
        ),
        code(
            """spark.sql(\"\"\"
CREATE OR REPLACE TABLE bronze_parsed_text
COMMENT 'Flattened parse text, one row per PDF'
AS
SELECT
  claim_id,
  file_name,
  path,
  concat_ws('\\n', transform(
    from_json(to_json(parsed:document:elements), 'array<struct<content:string>>'),
    e -> e.content
  )) AS parsed_text
FROM bronze_parsed_pdfs
\"\"\")
display(spark.sql(\"\"\"
SELECT claim_id, file_name, length(parsed_text) AS n_chars, substr(parsed_text, 1, 240) AS preview
FROM bronze_parsed_text
ORDER BY claim_id, file_name
\"\"\"))
"""
        ),
        md("## Silver — classify + extract"),
        code(
            """spark.sql(\"\"\"
CREATE OR REPLACE TABLE silver_claim_documents
COMMENT 'Classified + extracted pet-claim PDF fields'
AS
SELECT
  claim_id,
  file_name,
  path,
  parsed_text,
  ai_classify(
    substr(parsed_text, 1, 4000),
    '["fnol_claim_form", "clinic_invoice", "adjuster_report", "policy_declarations", "other"]'
  ) AS classified,
  ai_extract(
    substr(parsed_text, 1, 8000),
    '{
      "claim_number": {"type": "string", "description": "Claim number such as CLM-PET-00021"},
      "policy_number": {"type": "string", "description": "Policy number such as POL-88421"},
      "pet_name": {"type": "string", "description": "Name of the pet"},
      "species": {"type": "string", "description": "Dog or Cat"},
      "breed": {"type": "string", "description": "Breed of the pet"},
      "member_name": {"type": "string", "description": "Policyholder or clinic client name"},
      "clinic_name": {"type": "string", "description": "Veterinary clinic or hospital name"},
      "visit_date": {"type": "string", "description": "Visit date or date of loss as YYYY-MM-DD"},
      "invoice_number": {"type": "string", "description": "Clinic invoice number if this is an invoice"},
      "billed_amount": {"type": "number", "description": "Total billed amount as a number, no currency symbol"},
      "diagnosis": {"type": "string", "description": "Diagnosis or presenting complaint"},
      "recommended_decision": {"type": "string", "description": "Pay, Deny, or unknown"}
    }'
  ) AS extracted
FROM bronze_parsed_text
\"\"\")
print("silver_claim_documents ready")
"""
        ),
        code(
            """# Fix D: doc_type from classified:response[0]::string
# Fix E: fields from :response:<field>:value::string only (never the whole object)
spark.sql(\"\"\"
CREATE OR REPLACE TABLE silver_claim_documents_typed
COMMENT 'Silver typed columns from ai_classify + ai_extract'
AS
SELECT
  claim_id AS packet_claim_id,
  file_name,
  path,
  classified:response[0]::string AS doc_type,
  extracted:response:claim_number:value::string AS claim_number,
  extracted:response:policy_number:value::string AS policy_number,
  extracted:response:pet_name:value::string AS pet_name,
  extracted:response:species:value::string AS species,
  extracted:response:breed:value::string AS breed,
  extracted:response:member_name:value::string AS member_name,
  extracted:response:clinic_name:value::string AS clinic_name,
  try_to_date(extracted:response:visit_date:value::string) AS visit_date,
  extracted:response:invoice_number:value::string AS invoice_number,
  try_cast(extracted:response:billed_amount:value::string AS DOUBLE) AS billed_amount,
  extracted:response:diagnosis:value::string AS diagnosis,
  extracted:response:recommended_decision:value::string AS recommended_decision
FROM silver_claim_documents
\"\"\")

display(spark.sql(\"\"\"
SELECT
  packet_claim_id, doc_type, claim_number, pet_name, clinic_name,
  visit_date, invoice_number, billed_amount, diagnosis, recommended_decision
FROM silver_claim_documents_typed
ORDER BY packet_claim_id, doc_type
\"\"\"))
"""
        ),
        md("## Gold — invoices, duplicates, metric view"),
        code(
            """spark.sql(\"\"\"
CREATE OR REPLACE TABLE gold_clinic_invoices
COMMENT 'Invoice facts extracted from pet-claim PDFs'
AS
SELECT
  claim_number,
  policy_number,
  pet_name,
  species,
  breed,
  member_name,
  clinic_name,
  visit_date,
  invoice_number,
  billed_amount,
  diagnosis,
  recommended_decision,
  file_name
FROM silver_claim_documents_typed
WHERE doc_type = 'clinic_invoice'
\"\"\")

spark.sql(\"\"\"
CREATE OR REPLACE TABLE gold_claim_documents
COMMENT 'All typed PDF documents for Genie'
AS
SELECT * FROM silver_claim_documents_typed
\"\"\")

# Fix F: lower(trim(...)) so Pine Vet Clinic == PINE VET CLINIC
spark.sql(\"\"\"
CREATE OR REPLACE TABLE gold_suspected_pdf_duplicates
COMMENT 'Invoices that share pet + clinic + visit_date (case-insensitive)'
AS
WITH d AS (
  SELECT
    lower(trim(pet_name)) AS pet_key,
    lower(trim(clinic_name)) AS clinic_key,
    visit_date,
    count(*) AS n_invoices
  FROM gold_clinic_invoices
  WHERE pet_name IS NOT NULL AND clinic_name IS NOT NULL AND visit_date IS NOT NULL
  GROUP BY 1, 2, 3
  HAVING count(*) > 1
)
SELECT i.*, d.n_invoices
FROM gold_clinic_invoices i
JOIN d
  ON lower(trim(i.pet_name)) = d.pet_key
 AND lower(trim(i.clinic_name)) = d.clinic_key
 AND i.visit_date = d.visit_date
\"\"\")

display(spark.sql("SELECT * FROM gold_clinic_invoices ORDER BY visit_date, claim_number"))
display(spark.sql("SELECT * FROM gold_suspected_pdf_duplicates ORDER BY visit_date, claim_number"))
"""
        ),
        code(
            """spark.sql(f\"\"\"
CREATE OR REPLACE VIEW gold_pdf_invoice_metrics
WITH METRICS LANGUAGE YAML
COMMENT 'Metric view over PDF-extracted clinic invoices'
AS $$
version: 0.1
source: {CATALOG}.{SCHEMA}.gold_clinic_invoices
filter: billed_amount IS NOT NULL
dimensions:
  - name: Clinic
    expr: clinic_name
  - name: Diagnosis
    expr: diagnosis
  - name: Pet
    expr: pet_name
  - name: Visit date
    expr: visit_date
  - name: Claim
    expr: claim_number
measures:
  - name: Invoice count
    expr: COUNT(1)
  - name: Total billed
    expr: SUM(billed_amount)
  - name: Average billed
    expr: AVG(billed_amount)
$$
\"\"\")
display(spark.sql(\"\"\"
SELECT
  `Clinic` AS clinic,
  MEASURE(`Invoice count`) AS invoice_count,
  MEASURE(`Total billed`) AS total_billed,
  MEASURE(`Average billed`) AS avg_billed
FROM gold_pdf_invoice_metrics
GROUP BY `Clinic`
ORDER BY total_billed DESC
\"\"\"))
"""
        ),
        code(
            """spark.sql(\"\"\"
ALTER TABLE gold_clinic_invoices ALTER COLUMN pet_name COMMENT 'Pet name extracted from the invoice PDF'
\"\"\")
spark.sql(\"\"\"
ALTER TABLE gold_clinic_invoices ALTER COLUMN clinic_name COMMENT 'Veterinary clinic extracted from the invoice PDF'
\"\"\")
spark.sql(\"\"\"
ALTER TABLE gold_clinic_invoices ALTER COLUMN visit_date COMMENT 'Visit date. Duplicate key is lower(trim(pet_name)) + lower(trim(clinic_name)) + visit_date'
\"\"\")
spark.sql(\"\"\"
ALTER TABLE gold_suspected_pdf_duplicates SET TBLPROPERTIES (
  'comment' = 'Sparky at Pine Vet Clinic on 2026-08-03 is the planted pair (CLM-PET-00044 / 00045).'
)
\"\"\")
print("comments applied")
"""
        ),
        md(
            """## Check — exactly one PDF duplicate pair

Expect **Sparky · Pine Vet Clinic · 2026-08-03 · CLM-PET-00044 / CLM-PET-00045**.
"""
        ),
        code(
            """display(spark.sql(\"\"\"
SELECT
  lower(trim(pet_name)) AS pet,
  lower(trim(clinic_name)) AS clinic,
  visit_date,
  collect_list(claim_number) AS claims,
  collect_list(invoice_number) AS invoices,
  count(*) AS n
FROM gold_clinic_invoices
GROUP BY 1, 2, 3
HAVING count(*) > 1
\"\"\"))
"""
        ),
        md(
            """## Genie on gold tables

**New → Genie Agent.** Add:

- `{catalog}.{schema}.gold_clinic_invoices`
- `{catalog}.{schema}.gold_claim_documents`
- `{catalog}.{schema}.gold_suspected_pdf_duplicates`
- `{catalog}.{schema}.gold_pdf_invoice_metrics`
"""
        ),
        code(
            """instructions = f\"\"\"
You are a pet-insurance claims analyst for a workshop. Answer only from the attached Unity Catalog objects in {CATALOG}.{SCHEMA}.

Tables
- gold_clinic_invoices: one row per clinic invoice PDF. Grain is invoice_number.
- gold_claim_documents: every parsed PDF (FNOL, invoice, adjuster, policy) with doc_type.
- gold_suspected_pdf_duplicates: invoices that share pet_name + clinic_name + visit_date (case-insensitive).
- gold_pdf_invoice_metrics: metric view. Use MEASURE(`Invoice count`), MEASURE(`Total billed`), MEASURE(`Average billed`).

Duplicate definition
Same pet_name, clinic_name, and visit_date on more than one invoice. Invoice number is not the key.
CLM-PET-00044 and CLM-PET-00045 are the planted pair (Sparky, Pine Vet Clinic, 2026-08-03).
CLM-PET-00088 is a waiting-period denial, not a duplicate.

Rules
- If a question cannot be answered from these objects, say so.
- Prefer gold_suspected_pdf_duplicates when asked about duplicates.
- Money is USD.
\"\"\".strip()
print(instructions)
print("\\nBenchmark questions:")
for i, q in enumerate([
    "How many clinic invoices did we extract from PDFs, and what is total billed?",
    "Which invoices share the same pet, clinic, and visit date?",
    "What did Pine Vet Clinic bill for Sparky, and how many claim numbers are involved?",
    "Is Bella's Maple Emergency Vets invoice a duplicate?",
    "Break down total billed by clinic using the metric view.",
], 1):
    print(f"  {i}. {q}")
"""
        ),
        md(
            """## Your turn — Lab D complete when

- [ ] `gold_suspected_pdf_duplicates` shows exactly one pair: Sparky / Pine Vet / 2026-08-03
- [ ] Those claim numbers also exist as **Paid** in the synthetic `claims` table (`CLM-PET-00044`, `CLM-PET-00045`)
- [ ] Genie on the gold tables answers the Sparky question without inventing a new duplicate key

Optional stretch: wrap bronze → silver → gold as a Lakeflow Spark Declarative Pipeline.
"""
        ),
    ],
)

print("done")
