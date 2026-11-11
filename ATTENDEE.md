# MetLife Engage: Using AI on Databricks (attendee guide)

Synthetic pet-insurance claims. Five notebooks, run in order on **serverless** compute.

## Before you start

- You need a Databricks workspace with **serverless** notebooks enabled.
- You will use catalog **`13238_dna_hackathon2026`** (`USE CATALOG`). You do **not** create catalogs in this workshop.
- Do **not** create a classic cluster.

### Facilitator pre-event checklist

Confirm these **before** attendees arrive. Metadata-only commands can succeed while data writes still fail.

1. Attendees have `USE CATALOG` on `13238_dna_hackathon2026` and can `CREATE SCHEMA` / `CREATE TABLE` / `CREATE VOLUME` in it.
2. Catalog managed storage is reachable from **serverless** (egress / NCC). For this catalog that means storage account `sa13238e1sb0102` (`abfss://hackathon2026@sa13238e1sb0102.dfs.core.windows.net/`) is allowed by the workspace serverless network policy — or use a catalog whose storage serverless can reach.
3. Smoke-test on serverless: `00_setup` → first `saveAsTable` in `01_build_workshop_data` succeeds (not only `CREATE SCHEMA` / `CREATE VOLUME`).
4. `ai_parse_document`, `ai_classify`, and `ai_extract` are available in the workspace region (needed for notebook `04`).

## 1. Get the notebooks (5 min)

1. In Databricks: **Workspace → Add → Git folder**.
2. Paste: `https://github.com/sylviezhang1988-cpu/metlife-engage-workshop`
3. Clone branch `main`.

If Git folders are blocked, download this repo as a zip, unzip it, and import the `.ipynb` files into one workspace folder. Keep them together so `%run ./00_setup` still works.

If several people share one folder, you will overwrite each other’s `.workshop_config.json`. Re-set the schema widget in `00_setup` if that happens.

## 2. Set up (once)

1. Open `00_setup`. Attach **serverless** compute.
2. Run the **first code cell** once. Widgets appear at the top of the notebook.
3. Confirm widgets:
   - `catalog`: already set to `13238_dna_hackathon2026` — leave it.
   - `schema`: leave `metlife_claims`, or use your own schema name if several people share the catalog.
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
| Catalog or schema permission error | Confirm catalog is `13238_dna_hackathon2026`. Ask your facilitator for `USE CATALOG` / `CREATE SCHEMA` |
| `00_setup` ok, but `01` fails on `saveAsTable` with `UNAUTHORIZED_ACCESS` / `403` / “serverless network policy” | Catalog storage is blocked from serverless. Facilitator: allow storage account `sa13238e1sb0102` (or the catalog’s managed storage) in the serverless network policy / NCC, **or** switch to a catalog serverless can reach. Do **not** create a classic cluster. |
| Notebook can't find `./00_setup` | Keep all notebooks in the same folder |
| Wrong catalog/schema in 02–04 | Re-run `00_setup` first |
| Git folder won't clone | Use the zip fallback in step 1 |
| Still stuck | Raise your hand. Do not create a cluster to work around it |
