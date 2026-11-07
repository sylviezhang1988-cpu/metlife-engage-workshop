#!/usr/bin/env python3
"""Generate a small pet-insurance claim PDF packet.

Mirrors qian-yu-db/insurance-claim-knowledge-base sample_data/claims layout:
  sample_data/claims/<claim_id>/<doctype>_<id>.pdf

Designed to run locally (repo) or from a Databricks notebook (writes to a UC Volume).
No reportlab dependency — emits simple PDF 1.4 text pages.
"""

from __future__ import annotations

from pathlib import Path

try:
    ROOT = Path(__file__).resolve().parent / "sample_data" / "claims"
except NameError:
    ROOT = Path("sample_data") / "claims"


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .encode("latin-1", "replace")
        .decode("latin-1")
    )


def write_pdf(path: Path, lines: list[str]) -> None:
    """One-page Helvetica PDF. Keep lines short (~90 chars)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    y = 750
    ops = ["BT", "/F1 16 Tf", f"50 {y} Td ({_escape(lines[0])}) Tj", "/F1 10 Tf"]
    for line in lines[1:]:
        ops.append(f"0 -14 Td ({_escape(line)}) Tj")
    ops.append("ET")
    stream = "\n".join(ops).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
        ),
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode())
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode())
    out.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    path.write_bytes(out)


def packet() -> dict[str, list[tuple[str, list[str]]]]:
    """claim_id -> [(filename, lines)]."""
    return {
        "CLM-PET-00021": [
            (
                "fnol_claim_form_CLM-PET-00021.pdf",
                [
                    "PAWS & CLAWS PET INSURANCE  —  FIRST NOTICE OF LOSS",
                    "Claim number: CLM-PET-00021",
                    "Policy number: POL-88421",
                    "Date of loss: 2026-09-12",
                    "Submitted: 2026-09-14",
                    "Member: Priya Shah",
                    "Pet: Luna  |  Species: Cat  |  Breed: Domestic Shorthair  |  Age: 3",
                    "Clinic: Oak Animal Hospital  |  Austin, TX  |  NPI 1477582210",
                    "Diagnosis: Gastrointestinal illness (vomiting / diarrhea)",
                    "Narrative: Luna had acute GI signs after a boarding stay. Exam, CBC/Chem,",
                    "and fluids at Oak Animal Hospital. No prior GI claims on this policy.",
                    "Requested amount: $842.40",
                    "Document type: FNOL claim form",
                ],
            ),
            (
                "clinic_invoice_INV-OA-4412.pdf",
                [
                    "OAK ANIMAL HOSPITAL  —  CLINIC INVOICE",
                    "Invoice number: INV-OA-4412",
                    "Invoice date: 2026-09-12",
                    "Visit date: 2026-09-12",
                    "Patient: Luna (feline, DSH)",
                    "Client: Priya Shah",
                    "Claim number: CLM-PET-00021",
                    "Policy number: POL-88421",
                    "Diagnosis: Gastrointestinal illness",
                    "Line items:",
                    "  1. Office exam (sick)                         128.00",
                    "  2. CBC / chemistry panel                     214.00",
                    "  3. Subcutaneous fluids                       186.00",
                    "  4. Oral antiemetic / probiotic                94.40",
                    "  5. Hospitalization (day)                     220.00",
                    "Subtotal: 842.40   Tax: 0.00   Total billed: 842.40",
                    "Document type: Clinic invoice",
                ],
            ),
            (
                "policy_declarations_POL-88421.pdf",
                [
                    "PAWS & CLAWS PET INSURANCE  —  POLICY DECLARATIONS",
                    "Policy number: POL-88421",
                    "Named insured: Priya Shah",
                    "Pet: Luna  |  Cat  |  Domestic Shorthair",
                    "Effective: 2025-11-01   Renewal: 2026-11-01",
                    "Accident waiting period: 2 days",
                    "Illness waiting period: 14 days",
                    "Annual limit: $10,000",
                    "Deductible: $250   Reimbursement: 80%",
                    "Orthopedic exclusion: none (illness coverage in force)",
                    "Document type: Policy declarations",
                ],
            ),
        ],
        "CLM-PET-00044": [
            (
                "fnol_claim_form_CLM-PET-00044.pdf",
                [
                    "PAWS & CLAWS PET INSURANCE  —  FIRST NOTICE OF LOSS",
                    "Claim number: CLM-PET-00044",
                    "Policy number: POL-91002",
                    "Date of loss: 2026-08-03",
                    "Submitted: 2026-08-05",
                    "Member: Jordan Hale",
                    "Pet: Sparky  |  Species: Dog  |  Breed: Golden Retriever  |  Age: 7",
                    "Clinic: Pine Vet Clinic  |  Dallas, TX  |  NPI 1829034411",
                    "Diagnosis: Cranial cruciate ligament rupture (left stifle)",
                    "Narrative: Acute non-weight-bearing lameness after a park run. TPLO",
                    "recommended. This is the original submission for the 2026-08-03 visit.",
                    "Requested amount: $4,210.00",
                    "Document type: FNOL claim form",
                ],
            ),
            (
                "clinic_invoice_INV-PV-2201.pdf",
                [
                    "PINE VET CLINIC  —  CLINIC INVOICE",
                    "Invoice number: INV-PV-2201",
                    "Invoice date: 2026-08-03",
                    "Visit date: 2026-08-03",
                    "Patient: Sparky (canine, Golden Retriever)",
                    "Client: Jordan Hale",
                    "Claim number: CLM-PET-00044",
                    "Policy number: POL-91002",
                    "Diagnosis: Cranial cruciate ligament rupture",
                    "Line items:",
                    "  1. Orthopedic consult                        245.00",
                    "  2. Radiographs (stifle)                      380.00",
                    "  3. TPLO surgery                            2,850.00",
                    "  4. Anesthesia / monitoring                   420.00",
                    "  5. Post-op medications                       315.00",
                    "Subtotal: 4,210.00   Tax: 0.00   Total billed: 4,210.00",
                    "Document type: Clinic invoice",
                ],
            ),
            (
                "adjuster_report_CLM-PET-00044.pdf",
                [
                    "PAWS & CLAWS  —  CLAIM ADJUSTER REPORT",
                    "Claim number: CLM-PET-00044",
                    "Policy number: POL-91002",
                    "Pet: Sparky  |  Clinic: Pine Vet Clinic  |  Visit date: 2026-08-03",
                    "Invoice reviewed: INV-PV-2201  |  Billed: $4,210.00",
                    "Finding: Covered accident/illness after waiting period. Deductible applies.",
                    "Note: Watch for a second packet on the same pet, clinic, and visit date.",
                    "Duplicate key taught in this workshop is pet + clinic + visit_date,",
                    "not invoice number. A resubmit with a new invoice suffix is still a duplicate.",
                    "Recommended decision: Pay (original).",
                    "Document type: Adjuster report",
                ],
            ),
        ],
        "CLM-PET-00045": [
            (
                "fnol_claim_form_CLM-PET-00045.pdf",
                [
                    "PAWS & CLAWS PET INSURANCE  —  FIRST NOTICE OF LOSS",
                    "Claim number: CLM-PET-00045",
                    "Policy number: POL-91002",
                    "Date of loss: 2026-08-03",
                    "Submitted: 2026-08-19",
                    "Member: Jordan Hale",
                    "Pet: Sparky  |  Species: Dog  |  Breed: Golden Retriever  |  Age: 7",
                    "Clinic: Pine Vet Clinic  |  Dallas, TX  |  NPI 1829034411",
                    "Diagnosis: Cranial cruciate ligament rupture (left stifle)",
                    "Narrative: Corrected resubmission of the August 3 TPLO visit. Clinic",
                    "issued a revised invoice number. Same pet, same hospital, same visit date",
                    "as CLM-PET-00044.",
                    "Requested amount: $4,210.00",
                    "Document type: FNOL claim form",
                ],
            ),
            (
                "clinic_invoice_INV-PV-2201-R.pdf",
                [
                    "PINE VET CLINIC  —  CLINIC INVOICE (REVISED)",
                    "Invoice number: INV-PV-2201-R",
                    "Invoice date: 2026-08-18",
                    "Visit date: 2026-08-03",
                    "Patient: Sparky (canine, Golden Retriever)",
                    "Client: Jordan Hale",
                    "Claim number: CLM-PET-00045",
                    "Policy number: POL-91002",
                    "Diagnosis: Cranial cruciate ligament rupture",
                    "Line items:",
                    "  1. Orthopedic consult                        245.00",
                    "  2. Radiographs (stifle)                      380.00",
                    "  3. TPLO surgery                            2,850.00",
                    "  4. Anesthesia / monitoring                   420.00",
                    "  5. Post-op medications                       315.00",
                    "Subtotal: 4,210.00   Tax: 0.00   Total billed: 4,210.00",
                    "Note: Revised invoice for the 2026-08-03 visit. Do not treat a new",
                    "invoice number as a new visit.",
                    "Document type: Clinic invoice",
                ],
            ),
        ],
        "CLM-PET-00088": [
            (
                "fnol_claim_form_CLM-PET-00088.pdf",
                [
                    "PAWS & CLAWS PET INSURANCE  —  FIRST NOTICE OF LOSS",
                    "Claim number: CLM-PET-00088",
                    "Policy number: POL-77210",
                    "Date of loss: 2026-10-01",
                    "Submitted: 2026-10-02",
                    "Member: Elena Ruiz",
                    "Pet: Bella  |  Species: Dog  |  Breed: French Bulldog  |  Age: 2",
                    "Clinic: Maple Emergency Vets  |  Houston, TX  |  NPI 1649201188",
                    "Diagnosis: Radius/ulna fracture (right forelimb)",
                    "Narrative: Bella jumped from a sofa. Emergency splint and radiographs.",
                    "Policy incepted 2026-09-28 — still inside the accident waiting period.",
                    "Requested amount: $1,150.00",
                    "Document type: FNOL claim form",
                ],
            ),
            (
                "clinic_invoice_INV-ME-9904.pdf",
                [
                    "MAPLE EMERGENCY VETS  —  CLINIC INVOICE",
                    "Invoice number: INV-ME-9904",
                    "Invoice date: 2026-10-01",
                    "Visit date: 2026-10-01",
                    "Patient: Bella (canine, French Bulldog)",
                    "Client: Elena Ruiz",
                    "Claim number: CLM-PET-00088",
                    "Policy number: POL-77210",
                    "Diagnosis: Radius/ulna fracture",
                    "Line items:",
                    "  1. Emergency exam                            210.00",
                    "  2. Radiographs (forelimb)                    340.00",
                    "  3. Splint / bandage                          280.00",
                    "  4. Pain medication / NSAID                   120.00",
                    "  5. After-hours fee                           200.00",
                    "Subtotal: 1,150.00   Tax: 0.00   Total billed: 1,150.00",
                    "Document type: Clinic invoice",
                ],
            ),
            (
                "adjuster_report_CLM-PET-00088.pdf",
                [
                    "PAWS & CLAWS  —  CLAIM ADJUSTER REPORT",
                    "Claim number: CLM-PET-00088",
                    "Policy number: POL-77210",
                    "Pet: Bella  |  Clinic: Maple Emergency Vets  |  Visit date: 2026-10-01",
                    "Invoice reviewed: INV-ME-9904  |  Billed: $1,150.00",
                    "Policy effective date: 2026-09-28",
                    "Accident waiting period: 2 days. Date of loss is day 3 from inception;",
                    "carrier applies waiting period through 2026-10-02.",
                    "Recommended decision: Deny — waiting period.",
                    "This is not a duplicate. Do not confuse waiting-period denials with",
                    "the Sparky / Pine Vet duplicate pair (CLM-PET-00044 / CLM-PET-00045).",
                    "Document type: Adjuster report",
                ],
            ),
            (
                "policy_declarations_POL-77210.pdf",
                [
                    "PAWS & CLAWS PET INSURANCE  —  POLICY DECLARATIONS",
                    "Policy number: POL-77210",
                    "Named insured: Elena Ruiz",
                    "Pet: Bella  |  Dog  |  French Bulldog",
                    "Effective: 2026-09-28   Renewal: 2027-09-28",
                    "Accident waiting period: 2 days",
                    "Illness waiting period: 14 days",
                    "Annual limit: $7,000",
                    "Deductible: $250   Reimbursement: 80%",
                    "Document type: Policy declarations",
                ],
            ),
        ],
    }


def generate(dest: Path | None = None) -> list[Path]:
    dest = dest or ROOT
    written: list[Path] = []
    for claim_id, files in packet().items():
        for name, lines in files:
            path = dest / claim_id / name
            write_pdf(path, lines)
            written.append(path)
    return written


if __name__ == "__main__":
    paths = generate()
    print(f"Wrote {len(paths)} PDFs under {ROOT}")
    for p in paths:
        print(f"  {p.relative_to(ROOT.parent.parent)}")
