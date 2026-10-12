"""The 'brain' decides WHAT to try and WHY something failed. Swap it without touching the agent loop.
RuleBrain  = offline stand-in (rules). LLMBrain = calls a company-approved LLM, falls back to rules."""
import csv, json, requests
from config import settings as S

ABBR = {"hypertension": "HTN", "blood pressure": "BP", "myocardial infarction": "MI",
        "diabetes": "DM", "chest x-ray": "CXR", "type 2 diabetes": "T2DM"}
TEMPLATES = ["patient with {t}", "what does the record say about {t}"]

def make_typo(term):
    words = term.split()
    i = max(range(len(words)), key=lambda k: len(words[k]))
    w = words[i]
    if len(w) >= 5:
        words[i] = w[:len(w)//2] + w[len(w)//2 + 1:]          # drop one letter
    return " ".join(words)

class RuleBrain:
    name = "rule-based (offline demo brain)"

    def plan(self, fact):
        terms = [t.strip() for t in fact["key_terms"].split(";")]
        primary = terms[0]
        plan = [dict(kind="exact", query=primary)]
        plan += [dict(kind="related_term", query=t) for t in terms[1:3]]
        for t in terms:
            if t.lower() in ABBR:
                plan.append(dict(kind="abbreviation", query=ABBR[t.lower()])); break
        typo = make_typo(primary)
        if typo != primary:
            plan.append(dict(kind="typo", query=typo))
        plan += [dict(kind="natural_language", query=tpl.format(t=primary)) for tpl in TEMPLATES]
        seen, out = set(), []
        for p in plan:
            if p["query"].lower() not in seen:
                seen.add(p["query"].lower()); out.append(p)
        return out

    def diagnose(self, kind, control_ok, token_hits):
        """Returns (root_cause, suggestion)."""
        if not control_ok:
            return ("content_not_retrievable",
                    "Even the plain term does not find the page. Check indexing/chunking, or whether the expected page in facts.csv is right.")
        if kind == "abbreviation":
            return ("abbreviation_not_expanded", "Ask Dev to add medical-abbreviation expansion (e.g. HTN -> hypertension).")
        if kind == "typo":
            return ("typo_not_tolerated", "Ask Dev about fuzzy matching / spell correction.")
        if kind == "related_term":
            return ("synonym_not_linked", "Related terms or brand/generic names are not linked. Review the embedding model or synonym list.")
        if kind == "natural_language":
            hint = f" Single words that DO work: {', '.join(token_hits)}." if token_hits else ""
            return ("natural_language_not_understood", "Plain-language questions are not matched." + hint + " Consider query rewriting or a stronger embedding model.")
        return ("unknown", "Needs human investigation.")

class LLMBrain(RuleBrain):
    """UNTESTED SKELETON. Needs a company-approved endpoint. Send ONLY synthetic facts - never PHI.
    Expects an OpenAI-style chat-completions API; adjust the payload/headers for your provider."""
    name = "LLM brain (falls back to rules on any error)"

    def _ask(self, prompt):
        r = requests.post(S.LLM_ENDPOINT, timeout=60,
                          headers={S.LLM_AUTH_HEADER: S.LLM_API_KEY, "Content-Type": "application/json"},
                          json={"model": S.LLM_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def plan(self, fact):
        prompt = ("You are a QA engineer testing a medical-record search. Page content: "
                  f"{fact['description']}. Key terms: {fact['key_terms']}. "
                  "Return ONLY a JSON list of up to 8 objects {\"kind\": one of exact|related_term|abbreviation|typo|natural_language, \"query\": str} "
                  "of realistic searches a clinician might type, including abbreviations, misspellings and plain-language questions.")
        try:
            items = json.loads(self._ask(prompt))
            return [dict(kind=i["kind"], query=str(i["query"])) for i in items][:8]
        except Exception:
            return super().plan(fact)

def get_brain():
    return LLMBrain() if S.BRAIN == "llm" and S.LLM_ENDPOINT else RuleBrain()
