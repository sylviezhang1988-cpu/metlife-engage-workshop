-- flag_duplicate_claims: later submissions of the same pet + clinic + visit_date.
-- Invoice number is intentionally NOT in the key (resubmissions reuse, suffix, or rewrite it).
-- Replace ${catalog}.${schema} before scheduling.

CREATE OR REPLACE TABLE ${catalog}.${schema}.claims_flagged AS
WITH ranked AS (
  SELECT
    c.*,
    ROW_NUMBER() OVER (
      PARTITION BY pet_id, clinic_id, visit_date
      ORDER BY submitted_date, claim_id
    ) AS visit_rank,
    FIRST_VALUE(claim_id) OVER (
      PARTITION BY pet_id, clinic_id, visit_date
      ORDER BY submitted_date, claim_id
    ) AS original_claim_id
  FROM ${catalog}.${schema}.claims c
)
SELECT
  claim_id,
  original_claim_id,
  pet_id,
  clinic_id,
  visit_date,
  invoice_number,
  claimed_amount,
  claim_status,
  denial_reason,
  submitted_date
FROM ranked
WHERE visit_rank > 1;
