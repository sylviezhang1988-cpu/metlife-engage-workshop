# Pet insurance claim PDFs

Twelve mock PDFs for the MetLife Engage AI Functions lab. Same folder shape as the auto-claim sample in [insurance-claim-knowledge-base](https://github.com/qian-yu-db/insurance-claim-knowledge-base/tree/main/sample_data/claims): one folder per claim id.

Regenerate with `python generate_pet_claim_pdfs.py` from `working/metlife-engage-workshop/`. Workshop notebook `05_generate_pet_claim_pdfs.ipynb` writes the same files to `/Volumes/<catalog>/<schema>/claim_docs/pdfs/`.

| Claim | Pet | Clinic | Visit | Point of the packet |
|-------|-----|--------|-------|---------------------|
| CLM-PET-00021 | Luna (cat) | Oak Animal Hospital | 2026-09-12 | Clean paid GI claim |
| CLM-PET-00044 | Max (dog) | Pine Vet Clinic | 2026-08-03 | Original TPLO invoice `INV-PV-2201` |
| CLM-PET-00045 | Max (dog) | Pine Vet Clinic | 2026-08-03 | Resubmit `INV-PV-2201-R` — **duplicate** |
| CLM-PET-00088 | Bella (dog) | Maple Emergency Vets | 2026-10-01 | Waiting-period deny, not a duplicate |
