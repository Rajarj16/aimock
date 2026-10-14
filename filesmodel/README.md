# AI Model Testing POC — Smart Records

Tests the Smart Records AI pipeline for correctness, not security. This is
separate from the DAST POC — that covers the web/API attack surface; this
covers whether the models actually produce the right answers.

## The pipeline this maps to
1. OCR (EasyOCR) — production
2. Medical Record Indexing (SVM + XGBoost) — production
3. Contextual Search (Knowledge Graph + Elasticsearch, UMLS/Rxnorm) — production
4. Entity Resolver (embedding model, air-gapped) — in development
5. Clinical Assistant (RAG, Llama 8B) — in development

This POC starts with #3 and #5 — the two where correctness failures are
easiest to demonstrate and most meaningful to your manager. #1, #2, #4 follow
the same pattern (call model → compare to ground truth → score) once you have
labeled test data for them.

## What's included
- `test_search_relevance.py` — tests whether Contextual Search surfaces the
  right record for a given query (recall@K), including ontology resolution
  (brand name → generic, abbreviation disambiguation)
- `test_rag_groundedness.py` — tests whether the Clinical Assistant's answers
  are actually grounded in retrieved evidence, or hallucinated. Uses an LLM
  as a judge, since exact-match string comparison doesn't work for natural
  language answers.
- `test_data/` — sample golden query/Q&A sets in the expected format. These
  are PLACEHOLDERS with fake doc IDs — replace with real (de-identified)
  test data from Dev before running for real.

## Setup
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here   # only needed for groundedness judge
```

Edit `config.py`:
- Point `ENDPOINTS` at your real QA/Test API URLs
- Point the `test_data/*.json` paths at your real golden datasets once Dev
  provides them

## Run
```bash
python test_search_relevance.py
python test_rag_groundedness.py
```

## What you still need from Dev before this is real
1. **Real API endpoints** in QA/Test for each model, ideally callable
   independently (not only through the full pipeline)
2. **Ground-truth/labeled data**: correct search results per query,
   correct answers per question, correct OCR transcripts, correct section
   labels — ask if any of this already exists from their own model
   evaluation before you build it from scratch
3. **For the Clinical Assistant specifically**: confirm the API can return
   retrieved evidence chunks SEPARATELY from the final answer. If it only
   returns the final text, you cannot test groundedness — push back on this
   with Dev early, it's a testability gap, not just a nice-to-have
4. **De-identified or synthetic medical records** — never real PHI in test
   data, regardless of environment
5. **Confirmation that Model #5 truly never leaves the air-gapped network**
   — worth verifying explicitly given it resolves your company's earlier
   PHI/RAG objection

## Extending to the other three models
Same pattern each time:
1. Get a labeled ground-truth set from Dev (or build one with a clinician/
   domain reviewer if none exists)
2. Call the model's endpoint
3. Compare output to ground truth with the right metric:
   - OCR → character/word error rate
   - Indexing → precision/recall/F1 per section label
   - Entity Resolver → precision/recall on extracted entities
