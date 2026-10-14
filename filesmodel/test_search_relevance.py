"""
AI Model Testing POC - Contextual Search (Model #3) relevance evaluation
=========================================================================
Tests the KG + Elasticsearch search layer: does searching a term actually
surface the right record(s) in the top-K results?

Usage:
    python test_search_relevance.py
"""

import json
import requests

import config


def load_golden_queries():
    with open(config.GOLDEN_SEARCH_QUERIES, "r", encoding="utf-8") as f:
        return json.load(f)


def call_search(query, top_k):
    """Call the real search endpoint. Adjust the request/response shape
    once Dev confirms the actual API contract."""
    response = requests.post(
        config.ENDPOINTS["search"],
        json={"query": query, "top_k": top_k},
        timeout=10,
    )
    response.raise_for_status()
    # Expected shape: {"results": [{"doc_id": "...", "score": 0.0}, ...]}
    return [r["doc_id"] for r in response.json().get("results", [])]


def recall_at_k(expected_ids, returned_ids):
    if not expected_ids:
        return None  # nothing to check
    hits = sum(1 for doc_id in expected_ids if doc_id in returned_ids)
    return hits / len(expected_ids)


def run():
    queries = load_golden_queries()
    results = []
    total_recall = 0.0
    scored_count = 0

    print(f"Running {len(queries)} golden search queries against Contextual Search...\n")

    for item in queries:
        query = item["query"]
        expected = item["expected_doc_ids"]
        try:
            returned = call_search(query, config.SEARCH_RECALL_AT_K)
        except Exception as e:
            print(f"  FAILED to call search for '{query}': {e}")
            results.append({"query": query, "error": str(e)})
            continue

        recall = recall_at_k(expected, returned)
        passed = recall is None or recall >= 1.0 / len(expected) if expected else True

        print(f"  Query: '{query}'")
        print(f"    Expected: {expected}")
        print(f"    Returned (top {config.SEARCH_RECALL_AT_K}): {returned}")
        print(f"    Recall@{config.SEARCH_RECALL_AT_K}: {recall}")
        print(f"    Note: {item.get('notes', '')}\n")

        results.append({
            "query": query,
            "expected": expected,
            "returned": returned,
            "recall": recall,
        })

        if recall is not None:
            total_recall += recall
            scored_count += 1

    overall = total_recall / scored_count if scored_count else 0
    print("=" * 50)
    print(f"Overall average recall@{config.SEARCH_RECALL_AT_K}: {overall:.2f}")
    print(f"Threshold (config.SEARCH_MIN_RECALL): {config.SEARCH_MIN_RECALL}")
    print("PASS" if overall >= config.SEARCH_MIN_RECALL else "FAIL - below threshold")
    print("=" * 50)

    return results


if __name__ == "__main__":
    run()
