# Pet insurance claim PDFs

Twelve mock PDFs for the MetLife Engage AI Functions lab. One folder per claim id.

Regenerate with `python generate_pet_claim_pdfs.py`. Workshop notebook `01_build_workshop_data` writes the same files to `/Volumes/<catalog>/<schema>/claim_docs/pdfs/`.

| Claim | Pet | Clinic | Visit | Point of the packet |
|-------|-----|--------|-------|---------------------|
| CLM-PET-00021 | Luna (cat) | Oak Animal Hospital | 2026-09-12 | Clean paid GI claim |
| CLM-PET-00044 | Sparky (dog) | Pine Vet Clinic | 2026-08-03 | Original TPLO invoice `INV-PV-2201` |
| CLM-PET-00045 | Sparky (dog) | Pine Vet Clinic | 2026-08-03 | Resubmit `INV-PV-2201-R` — **duplicate** |
| CLM-PET-00088 | Bella (dog) | Maple Emergency Vets | 2026-10-01 | Waiting-period deny, not a duplicate |
