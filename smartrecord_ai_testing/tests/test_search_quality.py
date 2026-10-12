"""One test per golden-set row + overall quality gates."""
import pytest
from config import settings as S
from src.client import search
from src.metrics import load_golden, rank_of_expected, evaluate

GOLD = load_golden()
POS = [g for g in GOLD if g["category"] not in ("negative", "security")]
NEG = [g for g in GOLD if g["category"] == "negative"]
SEC = [g for g in GOLD if g["category"] == "security"]
ID = lambda r: f'{r["id"]}-{r["category"]}-{r["query"]}'

@pytest.mark.parametrize("row", POS, ids=ID)
def test_expected_page_in_top_k(row):
    results, _ = search(row["query"], row["patient_id"] or None)
    rank = rank_of_expected(results, row)
    assert rank and rank <= S.TOP_K, f'expected {row["expected_doc"]} p{row["expected_page"]}, got {[(r["doc"], r["page"]) for r in results]}'

@pytest.mark.parametrize("row", NEG, ids=ID)
def test_irrelevant_query_returns_nothing(row):
    results, _ = search(row["query"], row["patient_id"] or None)
    assert results == [], f"should return nothing, got {results}"

@pytest.mark.parametrize("row", SEC, ids=ID)
def test_no_cross_patient_leak(row):
    results, _ = search(row["query"], row["patient_id"])
    assert all(r["patient_id"] == row["patient_id"] for r in results), "another patient's record leaked!"

def test_quality_gates():
    _, s = evaluate()
    assert s["hit_rate_at_k"] >= S.MIN_HIT_RATE, f'Hit rate@{S.TOP_K} {s["hit_rate_at_k"]:.0%} below {S.MIN_HIT_RATE:.0%}'
    assert s["mrr"] >= S.MIN_MRR, f'MRR {s["mrr"]:.2f} below {S.MIN_MRR}'
    assert s["security_pass_rate"] == 1.0, "ZERO tolerance: cross-patient leak"
    assert s["latency_p95_ms"] <= S.MAX_P95_MS, f'p95 {s["latency_p95_ms"]:.0f} ms too slow'
