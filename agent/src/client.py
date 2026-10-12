"""Thin wrapper around the search API. If Dev's API shape differs, only .env / this file changes."""
import time, requests
from config import settings as S

def search(query, patient_id=None):
    """Returns (list_of_normalised_results, latency_ms). Each result: {doc, page, patient_id}."""
    body = {S.REQ_QUERY: query}
    if patient_id:
        body[S.REQ_PATIENT] = patient_id
    headers = {"Content-Type": "application/json"}
    if S.AUTH_TOKEN:
        headers[S.AUTH_HEADER_NAME] = S.AUTH_TOKEN
    t = time.perf_counter()
    r = requests.post(S.BASE_URL + S.SEARCH_PATH, json=body, headers=headers, timeout=15)
    ms = (time.perf_counter() - t) * 1000
    r.raise_for_status()
    raw = r.json().get(S.RESP_RESULTS, [])
    return [{"doc": x.get(S.RESP_DOC), "page": x.get(S.RESP_PAGE), "patient_id": x.get(S.RESP_PATIENT)} for x in raw], ms

def is_reachable():
    try:
        requests.get(S.BASE_URL, timeout=5); return True
    except Exception:
        return False
