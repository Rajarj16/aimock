# Smartrecord - AI Search Quality Testing (QA project)

Black-box evaluation of Smartrecord's semantic search: golden set -> automated run -> metrics -> scorecard.

## Files QA owns (this is the whole project)
| File | Purpose |
|---|---|
| `.env` (from `.env.example`) | URL, token, API field names, quality targets. **Never commit.** |
| `data/golden_set.csv` | Queries + expected doc/page. THE core QA asset. |
| `data/test_documents_inventory.csv` | What is in the test environment's documents (helps you write the golden set) |
| `config/settings.py` | Reads `.env` |
| `src/client.py` | Calls the search API |
| `src/metrics.py` | Hit rate, MRR, leak check, latency |
| `tests/test_search_quality.py` | pytest: one test per golden row + quality gates |
| `tests/test_ui_smoke.py` | Optional Playwright smoke test |
| `perf/search_load.js` | K6 load test |
| `scripts/run_evaluation.py` | Builds `reports/scorecard.html` + `results.csv` |
| `docs/questions_for_dev.md` | What to ask Dev |

## Setup
    pip install -r requirements.txt
    cp .env.example .env       # then edit values

## Run
    python scripts/run_evaluation.py                                   # scorecard
    pytest --html=reports/pytest_report.html --self-contained-html     # per-query tests
    k6 run -e BASE_URL=... -e TOKEN=... perf/search_load.js            # load
    pytest -m ui                                                       # optional UI smoke

## Getting started on the real project
1. Walk through `docs/questions_for_dev.md` with Dev.
2. Fill `.env` (URL, token, request/response field names).
3. Fill `data/test_documents_inventory.csv` from the test environment's documents.
4. Write 30-50 rows in `data/golden_set.csv` (all categories) and have a clinician/BA review the expected answers.
5. Run the scorecard, review failures with Dev, agree targets, re-run after each model/config change.

Categories: exact, brand_generic, synonym, abbreviation, typo, natural_language, negative, security.
No real PHI in any file, report or screenshot.
