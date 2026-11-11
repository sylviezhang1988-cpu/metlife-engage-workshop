# Using AI on Databricks Effectively

Hands-on notebooks for the MetLife Engage workshop (Cary · Nov 18). Synthetic pet-insurance claims. Run on **serverless**. Do not create a classic cluster. Do **not** `CREATE CATALOG`.

**Theme:** use AI to build the repeatable process, not to be the process.

## Facilitator preflight (before the room)

- Catalog `13238_dna_hackathon2026` must be writable from **serverless**, including its managed storage (storage account `sa13238e1sb0102`). `CREATE SCHEMA` / `CREATE VOLUME` alone is not enough — confirm a `saveAsTable` in `01` succeeds.
- Every attendee catalog you hand out must pass that same serverless storage check.
- Confirm AI Functions (`ai_parse_document`, `ai_classify`, `ai_extract`) in the workspace region for Lab D.

See `ATTENDEE.md` for the full checklist and the “If something breaks” table.

## Get this repo into your workspace

1. In Databricks: **Workspace → Add → Git folder** (or Repos).
2. Paste this repository URL.
3. Clone onto `main`.
4. Open `00_setup`. Catalog defaults to `13238_dna_hackathon2026`. Schema may stay `metlife_claims`.
5. Attach **serverless** and Run All on `00_setup`, then continue in order.

If Git folder is blocked, import the `.ipynb` files from a zip of this repo instead.

If several people share one Git folder, they will overwrite each other’s `.workshop_config.json` — each person should re-set the schema widget in `00_setup`.

## Widgets (`00_setup`)

| Widget | What to put |
|--------|-------------|
| `catalog` | Hardcoded to `13238_dna_hackathon2026` |
| `schema` | Defaults to `metlife_claims`; created if you have permission |
| `create_schema_if_missing` | `true` / `false` |

Other notebooks start with `%run ./00_setup`, so they pick up the same widgets.

## Order (5 notebooks)

| File | Who | Purpose | Ends with |
|------|-----|---------|-----------|
| `00_setup` | Everyone | Catalog / schema / volume + theme | Config saved |
| `01_build_workshop_data` | Attendees | Synthetic tables + PDFs + PK/FK | Tables + PDFs ready |
| `02_genie_agent` | Attendees | Genie Agent + Labs A/B | Genie One scheduled |
| `03_genie_code` | Attendees | Genie Code + Lab C | `flag_duplicate_claims()` job |
| `04_ai_on_claim_pdfs` | Attendees | Bronze → silver → gold (Lab D) | Gold tables + Genie |

## Duplicate definition

Same `pet_id + clinic_id + visit_date`, later `submitted_date`. Invoice number is not the key. Sibling pets on the same day are not duplicates (trap household: **PH0013**).

- **Leakage** = suspected duplicate with status Paid
- **Caught** = Denied, reason `Duplicate claim`

PDF planted pair: **Sparky** at Pine Vet Clinic on `2026-08-03` (`CLM-PET-00044` / `CLM-PET-00045`).
