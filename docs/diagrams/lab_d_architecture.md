# Lab D Architecture — Claim PDFs → Genie

Workshop slice of the [multi-modal claims knowledge base](https://github.com/qian-yu-db/insurance-claim-knowledge-base/blob/main/docs/claims_kb_architecture.md).

Production normalizes every modality (PDF, email, audio, photos) to text and unifies into one index.
Lab D keeps **one modality — claim PDFs** — and stops at structured gold tables + Genie (no vector search).

![Lab D architecture](lab_d_architecture.png)

```mermaid
flowchart LR
    subgraph UC["Unity Catalog · &lt;catalog&gt;.&lt;schema&gt;"]
      direction LR
      subgraph VOL["Volume · claim_docs/pdfs"]
        PDF[/"12 claim PDFs"/]
      end
      subgraph BRZ["Bronze · ai_parse_document"]
        B1[("bronze_pdf_files")] --> B2[("bronze_parsed_pdfs")] --> B3[("bronze_parsed_text")]
      end
      subgraph SLV["Silver · ai_classify + ai_extract"]
        S1[("silver_claim_documents")] --> S2[("silver_claim_documents_typed")]
      end
      subgraph GLD["Gold · SQL + metric view"]
        G1[("gold_claim_documents")]
        G2[("gold_clinic_invoices")]
        G3[("gold_suspected_pdf_duplicates")]
        G4["gold_pdf_invoice_metrics (metric view)"]
        G2 --> G3
        G2 --> G4
      end
      PDF -- read_files --> B1
      B3 --> S1
      S2 --> G1
      S2 --> G2
    end
    GLD --> GENIE["Genie Agent"]
    GENIE <--> USER["Claims analyst"]

    subgraph COMP["Compute"]
      AIF["AI Functions inference (Databricks-managed, billed per call)"]
      NB["Serverless notebook 04_ai_on_claim_pdfs"]
    end
    AIF -.-> BRZ
    AIF -.-> SLV
```

| Step | AI Function | Tables |
|------|-------------|--------|
| Landing | — | PDFs from notebook `01` |
| Bronze | `ai_parse_document` | `bronze_pdf_files`, `bronze_parsed_pdfs`, `bronze_parsed_text` |
| Silver | `ai_classify` + `ai_extract` | `silver_claim_documents`, `silver_claim_documents_typed` |
| Gold | — | `gold_clinic_invoices`, `gold_suspected_pdf_duplicates`, `gold_pdf_invoice_metrics` |
| Genie | — | Agent over the gold tables |

**Planted check:** Sparky · Pine Vet Clinic · `2026-08-03` · `CLM-PET-00044` / `CLM-PET-00045`.
