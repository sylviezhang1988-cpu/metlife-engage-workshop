#!/usr/bin/env python3
"""Synthetic pet-insurance tables for the MetLife Engage workshop.

Designed to be called from notebook 01_build_workshop_data.
Fixes from REVIEW_FEEDBACK.md: PH0013 trap, date caps, in-term claims,
lower loss ratio, Max→Buddy in the random list (Sparky is planted separately).
"""
from __future__ import annotations

import datetime as dt
import random
from typing import Any

from pyspark.sql import Row

D = lambda s: dt.date.fromisoformat(s)


def _rand_date(a: dt.date, b: dt.date) -> dt.date:
    if b < a:
        return a
    return a + dt.timedelta(days=random.randint(0, (b - a).days))


def generate(today: dt.date | None = None) -> dict[str, list[Row]]:
    """Return dict of table name → rows. seed(42) for stable counts."""
    random.seed(42)
    today = today or dt.date.today()

    STATES = ["NC", "NY", "NJ", "CA", "TX", "FL", "GA", "IL", "PA", "OH"]
    FIRST = ["Ava", "Liam", "Noah", "Emma", "Mia", "Owen", "Zoe", "Eli", "Ivy", "Leo", "Nora", "Jack"]
    LAST = ["Smith", "Patel", "Garcia", "Kim", "Nguyen", "Brown", "Lopez", "Chen", "Davis", "Moore"]
    DOGS = ["Labrador", "Golden Retriever", "French Bulldog", "Beagle", "Poodle", "Mixed"]
    CATS = ["Domestic Shorthair", "Maine Coon", "Siamese", "Ragdoll", "Mixed"]
    # Swap Max → Buddy so seed(42) length stays 8 (Sparky is planted in PDF claims).
    PET_NAMES = ["Buddy", "Bella", "Luna", "Charlie", "Milo", "Daisy", "Coco", "Rocky"]
    DIAG = {
        "Wellness": (80, 180),
        "Dental": (200, 600),
        "GI Illness": (150, 700),
        "Skin/Allergy": (100, 400),
        "Orthopedic": (400, 2500),
        "Cancer": (800, 4000),
        "Accident/Injury": (200, 1800),
        "Urinary": (150, 600),
    }
    CHANNELS = ["Mobile App", "Web Portal", "Email", "Clinic Direct"]
    TIERS = {
        "Basic": (0.70, 500, 5000, 32),
        "Standard": (0.80, 250, 10000, 48),
        "Premium": (0.90, 100, 20000, 71),
    }

    policyholders = [
        Row(
            policyholder_id=f"PH{i:04d}",
            first_name=random.choice(FIRST),
            last_name=random.choice(LAST),
            email=f"user{i}@example.com",
            state=random.choice(STATES),
            signup_date=_rand_date(D("2021-01-01"), D("2024-06-30")),
        )
        for i in range(1, 201)
    ]

    clinics = [
        Row(
            clinic_id=f"VC{i:03d}",
            clinic_name=(
                f"{random.choice(['Oak', 'Pine', 'Maple', 'Cedar', 'River', 'Summit'])} "
                f"{random.choice(['Animal Hospital', 'Vet Clinic', 'Pet Care', 'Emergency Vets'])} {i}"
            ),
            city=random.choice(["Cary", "Raleigh", "Charlotte", "Durham", "Atlanta", "Austin"]),
            state=random.choice(STATES),
            is_emergency=(i % 5 == 0),
        )
        for i in range(1, 21)
    ]

    pets, policies = [], []
    for i in range(1, 301):
        ph = policyholders[(i - 1) % 200] if i <= 200 else random.choice(policyholders)
        sp = random.choice(["Dog", "Cat"])
        pets.append(
            Row(
                pet_id=f"PET{i:04d}",
                policyholder_id=ph.policyholder_id,
                pet_name=random.choice(PET_NAMES),
                species=sp,
                breed=random.choice(DOGS if sp == "Dog" else CATS),
                birth_date=_rand_date(D("2012-01-01"), D("2023-06-01")),
            )
        )
        tier = random.choices(list(TIERS), [0.3, 0.5, 0.2])[0]
        r, ded, lim, prem = TIERS[tier]
        # Policies start across 2024-2026 so claims stay dense through the
        # latest data window (otherwise "last week" / "last 90 days" is empty).
        start = _rand_date(D("2024-07-01"), D("2026-07-31"))
        policies.append(
            Row(
                policy_id=f"POL{i:04d}",
                pet_id=f"PET{i:04d}",
                policyholder_id=ph.policyholder_id,
                plan_tier=tier,
                annual_deductible=float(ded),
                reimbursement_rate=r,
                annual_limit=float(lim),
                monthly_premium=float(prem + random.randint(-5, 15)),
                start_date=start,
                end_date=start + dt.timedelta(days=730),
                policy_status=random.choices(["Active", "Cancelled"], [0.9, 0.1])[0],
            )
        )

    claims: list[Row] = []
    payments: list[Row] = []

    def make_claim(
        cid: str,
        pol: Row,
        clinic_id: str,
        visit: dt.date,
        diag: str,
        amt: float,
        inv: str,
        submitted: dt.date,
        force_status: str | None = None,
        denial: str | None = None,
    ) -> Row:
        status = force_status or random.choices(
            ["Paid", "Approved", "Denied", "In Review", "Submitted"],
            [0.55, 0.10, 0.15, 0.12, 0.08],
        )[0]
        decided = status in ("Paid", "Approved", "Denied")
        decision = None
        if decided:
            decision = min(submitted + dt.timedelta(days=random.randint(1, 14)), today)
        if status == "Denied" and not denial:
            denial = random.choice(
                ["Pre-existing condition", "Not covered", "Missing documentation", "Waiting period"]
            )
        approved = None
        if decided:
            approved = 0.0 if status == "Denied" else round(amt * pol.reimbursement_rate, 2)
        c = Row(
            claim_id=cid,
            policy_id=pol.policy_id,
            pet_id=pol.pet_id,
            clinic_id=clinic_id,
            visit_date=visit,
            invoice_number=inv,
            diagnosis_category=diag,
            claimed_amount=float(amt),
            approved_amount=approved,
            claim_status=status,
            denial_reason=denial if status == "Denied" else None,
            submission_channel=random.choice(CHANNELS),
            submitted_date=submitted,
            decision_date=decision,
        )
        claims.append(c)
        if status == "Paid" and decision is not None and approved is not None:
            pay_date = min(decision + dt.timedelta(days=random.randint(1, 5)), today)
            payments.append(
                Row(
                    payment_id=f"PAY{len(payments)+1:05d}",
                    claim_id=cid,
                    payment_date=pay_date,
                    payment_amount=approved,
                    payment_method=random.choice(["Direct Deposit", "Check"]),
                )
            )
        return c

    # Fewer claims + in-term visits → loss ratio nearer 0.6–0.9
    n = 0
    attempts = 0
    while n < 700 and attempts < 5000:
        attempts += 1
        pol = random.choice(policies)
        term_end = min(pol.end_date, D("2026-10-15"))
        if pol.start_date >= term_end:
            continue
        visit = _rand_date(pol.start_date, term_end)
        submitted = min(visit + dt.timedelta(days=random.randint(0, 7)), today)
        diag = random.choice(list(DIAG))
        lo, hi = DIAG[diag]
        n += 1
        clinic_id = random.choice(clinics).clinic_id
        orig = make_claim(
            f"CLM{n:06d}",
            pol,
            clinic_id,
            visit,
            diag,
            round(random.uniform(lo, hi), 2),
            f"INV-{random.randint(100000, 999999)}",
            submitted,
        )
        if random.random() < 0.05:
            n += 1
            style = random.choice(["same_inv", "suffix", "new_inv"])
            inv = {
                "same_inv": orig.invoice_number,
                "suffix": orig.invoice_number + "-R",
                "new_inv": f"INV-{random.randint(100000, 999999)}",
            }[style]
            caught = random.random() < 0.35
            make_claim(
                f"CLM{n:06d}",
                pol,
                orig.clinic_id,
                visit,
                diag,
                round(orig.claimed_amount * random.uniform(0.97, 1.03), 2),
                inv,
                min(orig.submitted_date + dt.timedelta(days=random.randint(3, 30)), today),
                force_status="Denied" if caught else None,
                denial="Duplicate claim" if caught else None,
            )

    # Explicit PH0013 sibling trap: guarantee two pets, same clinic/day, NOT a duplicate.
    # No real same-pet duplicate for this household (trap answer = none).
    ph13 = next(p for p in policyholders if p.policyholder_id == "PH0013")
    ph13_pols = [p for p in policies if p.policyholder_id == "PH0013"]
    if len(ph13_pols) < 2:
        for k in range(2 - len(ph13_pols)):
            pid = f"PET_PH13_{k+1}"
            pol_id = f"POL_PH13_{k+1}"
            pets.append(
                Row(
                    pet_id=pid,
                    policyholder_id="PH0013",
                    pet_name=["Pepper", "Ginger"][k],
                    species="Dog",
                    breed="Beagle",
                    birth_date=D("2020-01-01"),
                )
            )
            pol = Row(
                policy_id=pol_id,
                pet_id=pid,
                policyholder_id="PH0013",
                plan_tier="Standard",
                annual_deductible=250.0,
                reimbursement_rate=0.80,
                annual_limit=10000.0,
                monthly_premium=48.0,
                start_date=D("2024-01-01"),
                end_date=D("2026-12-31"),
                policy_status="Active",
            )
            policies.append(pol)
            ph13_pols.append(pol)
    clinic = clinics[0].clinic_id
    for day in (D("2025-06-15"), D("2025-09-20")):
        for pol in ph13_pols[:2]:
            n += 1
            make_claim(
                f"CLM{n:06d}",
                pol,
                clinic,
                day,
                "Wellness",
                round(random.uniform(80, 180), 2),
                f"INV-{random.randint(100000, 999999)}",
                min(day + dt.timedelta(days=1), today),
                force_status="Paid",
            )

    # Planted PDF track claims (Sparky duplicate paid = leakage the AI should find)
    pine = next((c for c in clinics if "Pine" in c.clinic_name), clinics[1])
    oak = next((c for c in clinics if "Oak" in c.clinic_name), clinics[0])
    maple = next((c for c in clinics if "Maple" in c.clinic_name), clinics[2])

    # Extra pets/policies for planted packets
    planted_holders = [
        Row(policyholder_id="PH_PET21", first_name="Priya", last_name="Shah",
            email="priya.shah@example.com", state="TX", signup_date=D("2025-01-15")),
        Row(policyholder_id="PH_PET44", first_name="Jordan", last_name="Hale",
            email="jordan.hale@example.com", state="TX", signup_date=D("2024-03-01")),
        Row(policyholder_id="PH_PET88", first_name="Elena", last_name="Ruiz",
            email="elena.ruiz@example.com", state="TX", signup_date=D("2026-09-20")),
    ]
    policyholders.extend(planted_holders)

    planted_pets = [
        Row(pet_id="PET_LUNA", policyholder_id="PH_PET21", pet_name="Luna",
            species="Cat", breed="Domestic Shorthair", birth_date=D("2023-01-01")),
        Row(pet_id="PET_SPARKY", policyholder_id="PH_PET44", pet_name="Sparky",
            species="Dog", breed="Golden Retriever", birth_date=D("2019-05-01")),
        Row(pet_id="PET_BELLA_PDF", policyholder_id="PH_PET88", pet_name="Bella",
            species="Dog", breed="French Bulldog", birth_date=D("2024-06-01")),
    ]
    pets.extend(planted_pets)

    planted_pols = [
        Row(policy_id="POL-88421", pet_id="PET_LUNA", policyholder_id="PH_PET21",
            plan_tier="Standard", annual_deductible=250.0, reimbursement_rate=0.80,
            annual_limit=10000.0, monthly_premium=48.0, start_date=D("2025-11-01"),
            end_date=D("2026-11-01"), policy_status="Active"),
        Row(policy_id="POL-91002", pet_id="PET_SPARKY", policyholder_id="PH_PET44",
            plan_tier="Premium", annual_deductible=100.0, reimbursement_rate=0.90,
            annual_limit=20000.0, monthly_premium=71.0, start_date=D("2025-01-01"),
            end_date=D("2027-01-01"), policy_status="Active"),
        Row(policy_id="POL-77210", pet_id="PET_BELLA_PDF", policyholder_id="PH_PET88",
            plan_tier="Standard", annual_deductible=250.0, reimbursement_rate=0.80,
            annual_limit=7000.0, monthly_premium=48.0, start_date=D("2026-09-28"),
            end_date=D("2027-09-28"), policy_status="Active"),
    ]
    policies.extend(planted_pols)
    pol_by_id = {p.policy_id: p for p in planted_pols}

    make_claim("CLM-PET-00021", pol_by_id["POL-88421"], oak.clinic_id, D("2026-09-12"),
               "GI Illness", 842.40, "INV-OA-4412", D("2026-09-14"), force_status="Paid")
    make_claim("CLM-PET-00044", pol_by_id["POL-91002"], pine.clinic_id, D("2026-08-03"),
               "Orthopedic", 4210.00, "INV-PV-2201", D("2026-08-05"), force_status="Paid")
    # Resubmit — also Paid → leakage the PDF track should surface
    make_claim("CLM-PET-00045", pol_by_id["POL-91002"], pine.clinic_id, D("2026-08-03"),
               "Orthopedic", 4210.00, "INV-PV-2201-R", D("2026-08-19"), force_status="Paid")
    make_claim("CLM-PET-00088", pol_by_id["POL-77210"], maple.clinic_id, D("2026-10-01"),
               "Accident/Injury", 1150.00, "INV-ME-9904", D("2026-10-02"),
               force_status="Denied", denial="Waiting period")

    earned = []
    for p in policies:
        m = p.start_date.replace(day=1)
        while m <= min(p.end_date, today):
            earned.append(Row(policy_id=p.policy_id, plan_tier=p.plan_tier, month=m, earned_premium=p.monthly_premium))
            m = (m.replace(day=28) + dt.timedelta(days=4)).replace(day=1)

    ASSET = {
        "Corporate Bond": (0.045, 6.5),
        "Treasury": (0.039, 8.0),
        "Municipal Bond": (0.033, 7.2),
        "Agency MBS": (0.051, 5.1),
        "Commercial Mortgage": (0.058, 4.4),
        "Private Credit": (0.087, 3.2),
        "Public Equity": (0.0, 0.0),
    }
    RATING = ["AAA", "AA", "A", "BBB", "BB"]
    holdings = []
    for i in range(1, 401):
        a = random.choice(list(ASSET))
        y, dur = ASSET[a]
        holdings.append(
            Row(
                holding_id=f"H{i:04d}",
                asset_class=a,
                sector=random.choice(["Financials", "Utilities", "Industrials", "Healthcare", "Tech", "Government", "Real Estate"]),
                rating=None if a == "Public Equity" else random.choice(RATING),
                market_value=float(round(random.uniform(1e6, 5e7), 2)),
                book_yield=float(round(max(y + random.uniform(-0.01, 0.01), 0.0), 4)),
                duration_years=float(round(max(dur + random.uniform(-2, 2), 0.0), 2)),
                as_of_date=D("2026-09-30"),
            )
        )

    return {
        "policyholders": policyholders,
        "vet_clinics": clinics,
        "pets": pets,
        "policies": policies,
        "claims": claims,
        "claim_payments": payments,
        "earned_premium_monthly": earned,
        "investment_holdings": holdings,
    }


def answer_key_sql() -> str:
    return """
SELECT
  COUNT(*) AS suspected_duplicates,
  COUNT_IF(d.claim_status = 'Paid') AS duplicates_paid,
  COUNT_IF(d.claim_status = 'Denied' AND d.denial_reason = 'Duplicate claim') AS duplicates_caught,
  ROUND(SUM(p.payment_amount), 2) AS leakage_usd
FROM v_suspected_duplicate_claims d
LEFT JOIN claim_payments p USING (claim_id)
"""
