# Email Ingestion Methodology

## Overview
This report details the methodology, evaluation, and production roadmap for an automated Information Extraction (IE) pipeline. The prototype is designed to ingest semi-structured broker emails and multi-file attachments, converting them into structured JSON underwriting records.

---

## 1: Exploratory Data Analysis (EDA)
Prior to model selection, a structural analysis of the 50-submission dataset was conducted to understand document heterogeneity and token volume. EDA was explicitly targeted at token length and entity distribution to determine the foundational architecture. By confirming the data fits within standard context windows, we ruled out the need for complex, latency-heavy chunking or Retrieval-Augmented Generation (RAG) pipelines. 

**Key Findings:**
* **Payload Volume:** Submissions average **3.5 files** and **1,146 words** (approx. 1,524 tokens) per grouped payload, peaking at nearly 2,500 tokens. This easily fits within the context window of modern LLMs, eliminating the immediate need for chunking or Retrieval-Augmented Generation (RAG).
* **Data format:** The dataset exhibits high formatting heterogeneity. However, key financial and entity cues are highly prevalent: explicit currency symbols (£, $, €) and key-value pairings appear in 100% of the sample, while worded multipliers (e.g., "million", "k") appear in 96%.
* **Document Hierarchies & Fragmentation:** Critical underwriting data is rarely contained in the email body alone. Target entities are distributed across the email cover letter and attached markdown schedules. These form a horizontal document hierarchy (where separate documents logically relate to a single transaction), requiring a multi-document aggregation approach prior to extraction.

---

## 2: Ingestion & Extraction Model
Based on the EDA, a zero-shot, prompt-constrained Large Language Model (LLM) pipeline was implemented. A zero-shot approach utilising a highly capable foundation model was chosen over Supervised Fine-Tuning (SFT) because SFT is notoriously brittle when faced with the high formatting variance typical of diverse broker submissions. The pipeline leverages the architectural concept of Expansion to Contraction: the raw, unstructured payload represents an expansive semantic space, which the strict system prompt then forcefully "contracts" down into the precise target data model. This leads to better precision and retrieval against the ground truth validation. 

**Methodology:**
1. **Document Aggregation:** The ingestion engine parses file prefixes (e.g., `E001`) to group the primary email and all associated attachments into a single, unified text payload.
2. **LLM Extraction:** The payload is passed to a high-capacity LLM via the Groq API (`gpt-oss-20b` class models). 
3. **Constrained Schema:** A strict system prompt enforces a rigid JSON schema, applying type-casting (e.g., forcing numeric integers for revenue and stripping currency symbols) and returning arrays for multi-label fields (Countries, Requested Coverages).
4. **Determinism:** The model temperature is set to `0.0` to eliminate generative variation and to return the precise text to match the ground truth dataset.

---

## 3: Model Evaluation
The prototype's extractions were evaluated against a 50-record ground-truth dataset. The pipeline achieved a **0.0% failure/malformed rate**, successfully returning parsable JSON for all 50 submissions. Standard generative NLP metrics (like BLEU or ROUGE) are inappropriate for structured data extraction. In an underwriting context, predicting "10,000" instead of "1,000,000" might yield high character overlap, but it represents a catastrophic commercial failure. Therefore, strict exact-match accuracy and set-based F1 scores were selected to reflect true data integrity.


### Performance Metrics

| Field | Evaluation Metric | Score |
| :--- | :--- | :--- |
| **Company Name** | Exact Match Accuracy (Strict) | **98.00%** |
| **Revenue** | Exact Match Accuracy (Strict) | **94.00%** |
| **Industry** | Semantic Match Accuracy (Inclusion) | **98.00%** |
| **Countries** | Macro F1-Score (Set-based) | **99.00%** |
| **Requested Coverages** | Macro F1-Score (Set-based) | **98.00%** |

### Edge Case & Error Analysis
The 6% error rate in Revenue and minor discrepancies in other fields highlighted critical commercial edge cases to address before production:

1. **Predictions vs. Actuals (e.g., Submissions E007, E039, E050)**
   * *Issue:* The LLM extracted projected future turnover (e.g., Foxmere predicted at £488k) instead of the ground-truth completed fiscal year actuals (£546k).
   * *Resolution:* The production schema must be explicitly split into `revenue_historical_actual` and `revenue_projected_estimate` to force the model to disambiguate the figures.
2. **Operational Territories vs. Incidental Mentions (e.g., Submission E024)**
   * *Issue:* The model extracted "France" and "Canada" due to incidental text mentions (e.g., supplier locations or governing law), whereas the ground truth only required the operational risk territory ("Ireland").
   * *Resolution:* Refine prompt instructions to strictly isolate revenue-generating operational territories.
3. **Entity Suffix Truncation (e.g., Submission E047)**
   * *Issue:* The model extracted "Maplecrest Industries Ltd" from an email signature, missing the formal "Systems" suffix present in the ground truth.
   * *Resolution:* fuzzy matching against corporate registries (e.g., Companies House).

---

## 4: Production Handover & Feature Tickets
To safely scale this pipeline to handle 10,000+ daily submissions, the deterministic notebook prototype must be transitioned into an autonomous, event-driven agentic workflow. The following engineering tickets outline the remaining technical architecture.

### Ticket ENG-101: Implement Pydantic Schema & Structured Decoding
* **Context:** The PoC relied on markdown block stripping and post-hoc JSON parsing. Production requires absolute type-safety guarantees to prevent database insertion failures.
* **Acceptance Criteria:** 
  * Integrate constrained decoding libraries (e.g., `instructor` or `Outlines`).
  * Bind the extraction prompt to strict Pydantic models.
  * Ensure missing or ambiguous fields deserialize cleanly to `None` or `[]` rather than hallucinating generic strings.

### Ticket ENG-102: LLM Rate-Limit Management
* **Context:** The PoC utilised sequential execution with static delays (`time.sleep(20)`) to respect API quotas. This will bottleneck under high commercial volume.
* **Acceptance Criteria:** 
  * Wrap the extraction logic in an asynchronous worker (e.g., Celery/Redis or AWS Lambda) triggered by an ingestion message queue (SQS/Kafka).
  * Implement dynamic rate-limit handling with exponential backoff and jitter to maximise throughput within token-per-minute (TPM) limits.

### Ticket ENG-103: Different file formats for attachments (PDFs/Excel)
* **Context:** The PoC processed pre-cleaned `.md` files. Real-world broker attachments include scanned PDFs and complex Excel loss runs.
* **Acceptance Criteria:** 
  * Deploy a document parser as a pre-processing step.
  * The parser must preserve horizontal table headers across page breaks to ensure financial columns remain perfectly aligned for the LLM.

### Ticket ENG-104: Confidence Scoring & Manual Underwriter Reviews
* **Context:** Fully automated ingestion carries severe financial risk if ambiguous revenue figures (like the projections in E039) are ingested silently.
* **Acceptance Criteria:** 
  * Extract token log-probabilities alongside the JSON data to generate a confidence score (0.0 to 1.0).
  * Automatically route submissions scoring below `0.85`, or those with conflicting financial tables, to an Underwriter Review UI with the source text explicitly highlighted.