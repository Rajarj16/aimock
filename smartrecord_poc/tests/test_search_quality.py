"""Data-driven tests: ONE test per golden-set row, plus aggregate quality gates."""
import pytest
from metrics import load_golden, call_search, rank_of_expected, evaluate

GOLD = load_golden()
POS = [g for g in GOLD if g["category"] not in ("negative", "security")]
NEG = [g for g in GOLD if g["category"] == "negative"]
SEC = [g for g in GOLD if g["category"] == "security"]

@pytest.mark.parametrize("row", POS, ids=lambda r: f'{r["id"]}-{r["category"]}-{r["query"]}')
def test_expected_page_in_top5(row, base_url):
    results, _ = call_search(base_url, row["query"], row["patient_id"])
    rank = rank_of_expected(results, row)
    assert rank is not None and rank <= 5, f'expected {row["expected_doc"]} p{row["expected_page"]}, got {[(r["doc"], r["page"]) for r in results]}'

@pytest.mark.parametrize("row", NEG, ids=lambda r: f'{r["id"]}-{r["query"]}')
def test_irrelevant_query_returns_nothing(row, base_url):
    results, _ = call_search(base_url, row["query"], row["patient_id"])
    assert results == [], f"should return nothing, got {results}"

@pytest.mark.parametrize("row", SEC, ids=lambda r: f'{r["id"]}-{r["query"]}')
def test_no_cross_patient_leak(row, base_url):
    results, _ = call_search(base_url, row["query"], row["patient_id"])
    assert all(r["patient_id"] == row["patient_id"] for r in results), "another patient's record leaked!"

# ---- aggregate quality gates (thresholds agreed with the team) ----
def test_quality_gates(base_url):
    _, s = evaluate(base_url)
    assert s["hit_rate_at_5"] >= 0.90, f'Hit rate@5 {s["hit_rate_at_5"]:.0%} below 90%'
    assert s["mrr"] >= 0.80, f'MRR {s["mrr"]:.2f} below 0.80'
    assert s["security_pass_rate"] == 1.0, "ZERO tolerance: cross-patient leak"
