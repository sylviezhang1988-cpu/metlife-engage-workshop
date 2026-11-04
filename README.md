# Using AI on Databricks Effectively

Hands-on notebooks for the MetLife Engage workshop (Cary · Nov 18). Synthetic pet-insurance claims. Run on **serverless**. Do not create a classic cluster. Do **not** `CREATE CATALOG`.

## Get this repo into your workspace

1. In Databricks: **Workspace → Add → Git folder** (or Repos).
2. Paste this repository URL.
3. Clone onto `main`.
4. Open `00_setup` and set the **catalog** widget to a catalog you can already `USE`. Schema may stay `metlife_claims`.
5. Attach **serverless** and Run All on `00_setup`, then continue in order.

If Git folder is blocked, import the `.ipynb` files from a zip of this repo instead.

## Widgets (`00_setup`)

| Widget | What to put |
|--------|-------------|
| `catalog` | **Your** existing catalog (blank on purpose — fill it in) |
| `schema` | Defaults to `metlife_claims`; created if you have permission |
| `create_schema_if_missing` | `true` / `false` |

Other notebooks start with `%run ./00_setup`, so they pick up the same widgets. If `USE` fails, you need `USE CATALOG` / `USE SCHEMA` / `CREATE TABLE` before continuing.

## Order

| File | Purpose |
|------|---------|
| `00_setup` | Catalog/schema/volume widgets |
| `01_generate_synthetic_claims` | Seed data + leakage answer key |
| `02_metrics_and_anomalies` | Duplicate view, trap query, metric view |
| `03_genie_agent_and_one` | Agent instructions, benchmark questions, Genie One |
| `04_genie_code_prompts` | Workspace prompts; CLI is optional |
| `05_generate_pet_claim_pdfs` | 12 pet-claim PDFs → `claim_docs` volume |
| `06_hands_on_labs` | Labs A–D |
| `07_bronze_parse_pdfs` | `read_files` + `ai_parse_document` |
| `08_silver_extract_classify` | `ai_classify` + `ai_extract` |
| `09_gold_metrics_and_genie` | Invoice facts, metric view, Genie instructions |

MLflow is not in this pack. AI Functions is PDF ingest only.

## Duplicate definition

Same `pet_id + clinic_id + visit_date`, later `submitted_date`. Invoice number is not the key. Sibling pets on the same day are not duplicates.

- **Leakage** = suspected duplicate with status Paid
- **Caught** = Denied, reason `Duplicate claim`

Lab D planted pair: Max at Pine Vet Clinic on `2026-08-03` (`CLM-PET-00044` / `CLM-PET-00045`).
