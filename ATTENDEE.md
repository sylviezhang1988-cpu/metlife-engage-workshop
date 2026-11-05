# MetLife Engage: Using AI on Databricks (attendee guide)

Synthetic pet-insurance claims. You will run notebooks in order on **serverless** compute.

## Before you start

- You need a Databricks workspace with **serverless** notebooks enabled.
- You need an existing **catalog** you can use (`USE CATALOG`). You do **not** create catalogs in this workshop.
- Do **not** create a classic cluster.

## 1. Get the notebooks (5 min)

1. In Databricks: **Workspace → Add → Git folder**.
2. Paste: `https://github.com/sylviezhang1988-cpu/metlife-engage-workshop`
3. Clone branch `main`.

If Git folders are blocked, download this repo as a zip, unzip it, and import the `.ipynb` files into one workspace folder. Keep them together so `%run ./00_setup` still works.

## 2. Set up (once)

1. Open `00_setup`. Attach **serverless** compute.
2. Run the **first code cell** once. Widgets appear at the top of the notebook.
3. Set widgets:
   - `catalog`: the catalog you can already use. Do not leave it blank and do not guess.
   - `schema`: leave `metlife_claims` unless your facilitator says otherwise.
   - `create_schema_if_missing`: `true` (set to `false` only if your schema already exists and you cannot create it).
4. **Run All** on `00_setup` (or run the remaining cells).

If `USE CATALOG`, `USE SCHEMA`, or `CREATE TABLE` fails, stop and ask your facilitator for access before you continue.

## 3. Run in order

Run every notebook after `00_setup`. Each one starts with `%run ./00_setup`, so keep the same catalog and schema widgets.

| # | Notebook | What it does |
|---|----------|--------------|
| 01 | `01_generate_synthetic_claims` | Creates sample claim tables, including planted duplicates |
| 02 | `02_metrics_and_anomalies` | Duplicate view, trap query, metric view |
| 03 | `03_genie_agent_and_one` | Set up Genie over the tables |
| 04 | `04_genie_code_prompts` | Prompt patterns for Genie (CLI is optional) |
| 05 | `05_generate_pet_claim_pdfs` | Writes 12 mock claim PDFs to the `claim_docs` volume |
| 06 | `06_hands_on_labs` | Labs A to D. Run when your facilitator says so |
| 07 | `07_bronze_parse_pdfs` | Parses PDFs with `ai_parse_document` |
| 08 | `08_silver_extract_classify` | Classifies and extracts fields with `ai_classify` and `ai_extract` |
| 09 | `09_gold_metrics_and_genie` | Builds gold tables, metric view, and Genie instructions for the PDF data |

## Rules

- **Serverless only.** No classic clusters.
- **Do not** run `CREATE CATALOG`.
- **Duplicate** = same pet + same clinic + same visit date. Invoice number is not the key. Two different pets on the same day are not duplicates.
- **Lab D planted pair:** Max at Pine Vet Clinic on `2026-08-03` (`CLM-PET-00044` and `CLM-PET-00045`).

## If something breaks

| Symptom | Fix |
|---------|-----|
| Catalog or schema permission error | Check the catalog widget. Ask your facilitator for `USE CATALOG` / `CREATE SCHEMA` |
| Notebook can't find `./00_setup` | Keep all notebooks in the same folder |
| Notebook fails on a step after a previous run | Re-run `00_setup`, then re-run from the failed notebook |
| Git folder won't clone | Use the zip fallback in step 1 |
| Still stuck | Raise your hand. Do not create a cluster to work around it |
