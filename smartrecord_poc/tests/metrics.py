"""Search-quality metrics. Pure functions - no framework needed."""
import csv, time, statistics, requests, pathlib

BASE = "http://127.0.0.1:5000"
HEADERS = {"X-Token": "demo-token", "Content-Type": "application/json"}
GOLDEN = pathlib.Path(__file__).parent / "golden_set.csv"

def load_golden():
    return list(csv.DictReader(open(GOLDEN, encoding="utf-8")))

def call_search(base, query, patient_id):
    t = time.perf_counter()
    r = requests.post(f"{base}/api/search", json={"query": query, "patient_id": patient_id}, headers=HEADERS, timeout=10)
    ms = (time.perf_counter() - t) * 1000
    r.raise_for_status()
    return r.json()["results"], ms

def rank_of_expected(results, row):
    """1-based rank of the expected (doc, page) in results, or None."""
    for i, r in enumerate(results, 1):
        if r["doc"] == row["expected_doc"] and str(r["page"]) == str(row["expected_page"]):
            return i
    return None

def evaluate(base=BASE):
    rows, positives, negatives, security = [], [], [], []
    for g in load_golden():
        results, ms = call_search(base, g["query"], g["patient_id"])
        item = dict(g, latency_ms=round(ms, 1), n_results=len(results),
                    top_hit=f'{results[0]["doc"]} p{results[0]["page"]}' if results else "-")
        if g["category"] in ("negative",):
            item["rank"] = ""; item["passed"] = len(results) == 0; negatives.append(item)
        elif g["category"] == "security":
            leaked = any(r["patient_id"] != g["patient_id"] for r in results)
            item["rank"] = ""; item["passed"] = not leaked; security.append(item)
        else:
            rk = rank_of_expected(results, g)
            item["rank"] = rk or ""; item["passed"] = rk is not None and rk <= 5; positives.append(item)
        rows.append(item)
    def hit(k): return sum(1 for r in positives if r["rank"] and r["rank"] <= k) / len(positives)
    mrr = sum(1 / r["rank"] for r in positives if r["rank"]) / len(positives)
    cats = {}
    for r in positives:
        c = cats.setdefault(r["category"], [0, 0]); c[1] += 1; c[0] += 1 if r["passed"] else 0
    lat = sorted(r["latency_ms"] for r in rows)
    summary = {
        "total_queries": len(rows), "positive_queries": len(positives),
        "hit_rate_at_1": hit(1), "hit_rate_at_3": hit(3), "hit_rate_at_5": hit(5), "mrr": mrr,
        "no_result_accuracy": sum(r["passed"] for r in negatives) / len(negatives),
        "security_pass_rate": sum(r["passed"] for r in security) / len(security),
        "by_category": {k: {"passed": v[0], "total": v[1], "rate": v[0] / v[1]} for k, v in cats.items()},
        "latency_p50_ms": statistics.median(lat), "latency_p95_ms": lat[int(len(lat) * 0.95) - 1],
    }
    return rows, summary
