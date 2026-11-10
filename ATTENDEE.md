# MetLife Engage: Using AI on Databricks (attendee guide)

Synthetic pet-insurance claims. Five notebooks, run in order on **serverless** compute.

## Before you start

- You need a Databricks workspace with **serverless** notebooks enabled.
- You need an existing **catalog** you can use (`USE CATALOG`). You do **not** create catalogs in this workshop.
- Do **not** create a classic cluster.

## 1. Get the notebooks (5 min)

1. In Databricks: **Workspace → Add → Git folder**.
2. Paste: `https://github.com/sylviezhang1988-cpu/metlife-engage-workshop`
3. Clone branch `main`.

If Git folders are blocked, download this repo as a zip, unzip it, and import the `.ipynb` files into one workspace folder. Keep them together so `%run ./00_setup` still works.

If several people share one folder, you will overwrite each other’s `.workshop_config.json`. Re-set the catalog widget in `00_setup` if that happens.

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

Each notebook after `00_setup` starts with `%run ./00_setup`, which reuses the catalog and schema you saved.

| # | Notebook | What you do |
|---|----------|-------------|
| 01 | `01_build_workshop_data` | Build your synthetic tables + PDFs in your schema (run once, before 02) |
| 02 | `02_genie_agent` | Build Genie Agent, then Lab A (fix an answer) + Lab B (schedule Genie One) |
| 03 | `03_genie_code` | Genie Code prompts + Lab C (`flag_duplicate_claims` + daily job) |
| 04 | `04_ai_on_claim_pdfs` | Bronze → silver → gold on claim PDFs (Lab D). Find Sparky’s duplicate |

## Rules

- **Serverless only.** No classic clusters.
- **Do not** run `CREATE CATALOG`.
- **Duplicate** = same pet + same clinic + same visit date. Invoice number is not the key. Two different pets on the same day are not duplicates (trap: household **PH0013** → expect none).
- **PDF planted pair:** Sparky at Pine Vet Clinic on `2026-08-03` (`CLM-PET-00044` and `CLM-PET-00045`).

## If something breaks

| Symptom | Fix |
|---------|-----|
| Catalog or schema permission error | Check the catalog widget. Ask your facilitator for `USE CATALOG` / `CREATE SCHEMA` |
| Notebook can't find `./00_setup` | Keep all notebooks in the same folder |
| Blank catalog in 02–04 | Re-run `00_setup` first |
| Git folder won't clone | Use the zip fallback in step 1 |
| Still stuck | Raise your hand. Do not create a cluster to work around it |
