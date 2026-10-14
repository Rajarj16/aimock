"""
AI Model Testing POC - Configuration
=====================================
This is the file to edit once Dev gives you real endpoints and test data.
Everything here is a placeholder until then.
"""

# ---------------------------------------------------------------------------
# MODEL ENDPOINTS - ask Dev for these. Each model should be callable
# independently in QA/Test, not just through the full pipeline, so you can
# isolate failures to one stage.
# ---------------------------------------------------------------------------
ENDPOINTS = {
    "ocr": "https://qa.smartrecords.example.com/api/ocr",                # Model 1 - EasyOCR
    "indexing": "https://qa.smartrecords.example.com/api/index",          # Model 2 - SVM/XGBoost
    "search": "https://qa.smartrecords.example.com/api/search",           # Model 3 - KG + Elasticsearch
    "entity_resolver": "https://qa.smartrecords.example.com/api/entities",  # Model 4 - embedding model
    "clinical_assistant": "https://qa.smartrecords.example.com/api/assistant",  # Model 5 - RAG + Llama 8B
}

# ---------------------------------------------------------------------------
# TEST DATA - ask Dev/data team for de-identified or synthetic medical
# records with ground-truth labels. NEVER use real PHI here.
# ---------------------------------------------------------------------------
GOLDEN_SEARCH_QUERIES = "test_data/golden_search_queries.json"
GOLDEN_QA_SET = "test_data/golden_qa_set.json"
GROUND_TRUTH_OCR = "test_data/ground_truth_ocr.json"
GROUND_TRUTH_SECTIONS = "test_data/ground_truth_sections.json"

# ---------------------------------------------------------------------------
# THRESHOLDS - starting points; tune once you have a baseline from Dev or
# your first real run. These are NOT industry-standard numbers, they're
# reasonable starting gates to tighten or loosen based on actual results.
# ---------------------------------------------------------------------------
SEARCH_RECALL_AT_K = 5          # how many top results count as "found it"
SEARCH_MIN_RECALL = 0.80        # 80% of golden queries must surface the right doc in top-K
GROUNDEDNESS_MIN_SCORE = 0.85   # fraction of answer claims that must trace to retrieved evidence

REPORT_DIR = "reports"
