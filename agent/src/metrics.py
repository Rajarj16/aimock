"""Metric calculations. No framework needed - plain Python."""
import csv, statistics
from config import settings as S
from src.client import search

def load_golden():
    with open(S.GOLDEN_SET, encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["id"].strip()]

def rank_of_expected(results, row):
    for i, r in enumerate(results, 1):
        if r["doc"] == row["expected_doc"] and str(r["page"]) == str(row["expected_page"]):
            return i
    return None

def evaluate():
    rows, pos, neg, sec = [], [], [], []
    for g in load_golden():
        results, ms = search(g["query"], g["patient_id"] or None)
        item = dict(g, latency_ms=round(ms, 1), top_hit=f'{results[0]["doc"]} p{results[0]["page"]}' if results else "-")
        if g["category"] == "negative":
            item.update(rank="", passed=len(results) == 0); neg.append(item)
        elif g["category"] == "security":
            item.update(rank="", passed=all(r["patient_id"] == g["patient_id"] for r in results)); sec.append(item)
        else:
            rk = rank_of_expected(results, g)
            item.update(rank=rk or "", passed=bool(rk and rk <= S.TOP_K)); pos.append(item)
        rows.append(item)
    hit = lambda k: sum(1 for r in pos if r["rank"] and r["rank"] <= k) / max(len(pos), 1)
    cats = {}
    for r in pos:
        c = cats.setdefault(r["category"], [0, 0]); c[1] += 1; c[0] += int(r["passed"])
    lat = sorted(r["latency_ms"] for r in rows)
    summary = {
        "total_queries": len(rows), "positive_queries": len(pos),
        "hit_rate_at_1": hit(1), "hit_rate_at_3": hit(3), f"hit_rate_at_k": hit(S.TOP_K),
        "mrr": sum(1 / r["rank"] for r in pos if r["rank"]) / max(len(pos), 1),
        "no_result_accuracy": sum(r["passed"] for r in neg) / max(len(neg), 1),
        "security_pass_rate": sum(r["passed"] for r in sec) / max(len(sec), 1),
        "by_category": {k: {"passed": v[0], "total": v[1], "rate": v[0] / v[1]} for k, v in cats.items()},
        "latency_p50_ms": statistics.median(lat), "latency_p95_ms": lat[max(int(len(lat) * 0.95) - 1, 0)],
    }
    return rows, summary
