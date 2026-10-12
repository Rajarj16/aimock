"""MOCK 'semantic' search engine.
Stand-in for Dev's real model (embeddings + vector DB). It is deliberately
imperfect so your test suite has something real to find.
In the real project you do NOT write this - Dev owns it."""
import json, math, re, difflib, pathlib

DOCS = json.loads((pathlib.Path(__file__).parent / "data" / "documents.json").read_text())
STOP = {"the","a","an","of","for","in","on","and","to","is","was","with","has","have","show","me","patient","patients","any"}

# synonym knowledge (a real model learns this; here it's hand-written and INCOMPLETE on purpose)
SYN = {
    "dolo": ["paracetamol", "acetaminophen"], "crocin": ["paracetamol", "acetaminophen"],
    "paracetamol": ["acetaminophen", "dolo"], "acetaminophen": ["paracetamol", "dolo"],
    "bp": ["blood", "pressure"], "hypertension": ["blood", "pressure"],
    "diabetes": ["glucose", "hba1c", "glycemic"], "diabetic": ["diabetes", "glucose"],
    "xray": ["x-ray", "chest"], "cholesterol": ["lipid", "statin"],
    "headache": ["migraine"], "allergic": ["allergy"], "allergies": ["allergy"],
    "surgery": ["appendectomy"], "medicine": ["prescription", "tab"], "medication": ["prescription", "tab"],
    # missing on purpose: htn, "sugar", "heart attack", "mi" ...
}

def tok(s):
    return [t for t in re.findall(r"[a-z0-9\-]+", s.lower()) if t not in STOP]

VOCAB = sorted({t for d in DOCS for t in tok(d["text"])})
DF = {}
for d in DOCS:
    for t in set(tok(d["text"])):
        DF[t] = DF.get(t, 0) + 1
N = len(DOCS)
idf = lambda t: math.log(1 + N / (1 + DF.get(t, 0)))

def expand(query):
    out = []
    for t in tok(query):
        if t not in VOCAB and t not in SYN:
            m = difflib.get_close_matches(t, VOCAB + list(SYN), n=1, cutoff=0.8)  # typo tolerance
            t = m[0] if m else t
        out.append((t, 1.0))
        out += [(s, 0.7) for s in SYN.get(t, [])]
    return out

def search(query, patient_id=None, k=5, min_score=0.9):
    q = expand(query)
    res = []
    for d in DOCS:
        if patient_id and d["patient_id"] != patient_id:
            continue
        toks = set(tok(d["text"]))
        score = sum(w * idf(t) for t, w in q if t in toks)
        if score >= min_score:
            res.append({"doc": d["doc"], "page": d["page"], "patient_id": d["patient_id"],
                        "score": round(score, 3), "snippet": d["text"][:90]})
    res.sort(key=lambda r: -r["score"])
    return res[:k]
