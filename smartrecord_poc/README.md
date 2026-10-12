# Smartrecord AI Search - POC Test Framework (MOCK DEMO)

Shows how to test an AI/semantic search feature as a black box: golden set -> automated run -> metrics -> scorecard.
`mock_app/` is a stand-in for Dev's real app. In the real POC you DELETE it and point the tests at the real endpoint.

## Run the demo
    pip install -r requirements.txt
    cd mock_app && python app.py          # terminal 1 (http://127.0.0.1:5000)
    python scripts/run_evaluation.py      # terminal 2 -> console scorecard + reports/scorecard.html + results.csv
    pytest tests/test_search_quality.py --html=reports/pytest_report.html --self-contained-html
    k6 run perf/search_load.js            # load test (needs k6 installed)
    pytest tests/test_ui_smoke.py         # optional, needs pytest-playwright

## Point it at the REAL Smartrecord
1. `tests/metrics.py`: change BASE, HEADERS (token), and the request/response field names in `call_search` / `rank_of_expected`.
2. Replace `tests/golden_set.csv` with queries + expected doc/page from the documents loaded in YOUR test environment.
3. Agree thresholds with the team (`scripts/run_evaluation.py` and `test_quality_gates`).

## Folder map
- tests/golden_set.csv   the heart of the POC (query -> expected doc + page)
- tests/metrics.py       hit rate, MRR, no-result accuracy, leak check, latency
- tests/test_*.py        pytest: one test per golden row + quality gates
- scripts/run_evaluation.py  scorecard generator
- perf/search_load.js    K6
- mock_app/              FAKE app (delete for the real POC)
