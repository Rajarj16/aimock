"""The agent loop: GOAL -> PLAN -> ACT -> OBSERVE -> (FAIL? INVESTIGATE) -> REMEMBER -> REPORT"""
import csv, re
from collections import defaultdict
from config import settings as S
from agent.tools import Tools
from agent.guardrails import BudgetExceeded

GENERIC = {"the", "what", "does", "with", "patient", "about", "record", "say", "any", "and", "for"}

def load_facts():
    with open(S.FACTS_FILE, encoding="utf-8") as f:
        return list(csv.DictReader(f))

class Agent:
    def __init__(self, brain, guard, goal):
        self.brain, self.guard, self.goal = brain, guard, goal
        self.trace, self.tools = [], None
        self.tools = Tools(guard, self.trace)
        self.attempts, self.findings, self.security = [], [], []
        self.pattern = {}                 # MEMORY: kind -> [root_cause, times_confirmed]
        self.stopped_reason = None

    def rank(self, results, fact):
        for i, r in enumerate(results or [], 1):
            if r["doc"] == fact["doc"] and str(r["page"]) == str(fact["page"]):
                return i
        return None

    def run(self, facts):
        self.patients = sorted({f["patient_id"] for f in facts})
        try:
            for fact in facts:
                self.test_fact(fact)
                self.security_probe(fact)
        except BudgetExceeded as e:
            self.stopped_reason = str(e)
        return self

    def test_fact(self, fact):
        plan = self.brain.plan(fact)
        for v in plan:
            res = self.tools.search(v["query"], fact["patient_id"],
                                    thought=f'{fact["fact_id"]}: try a "{v["kind"]}" search for {fact["doc"]} p{fact["page"]}')
            rk = self.rank(res, fact)
            ok = bool(rk and rk <= S.TOP_K)
            self.attempts.append(dict(fact_id=fact["fact_id"], kind=v["kind"], query=v["query"], ok=ok, rank=rk))
            if not ok:
                self.investigate(fact, v)

    def investigate(self, fact, v):
        kind, primary = v["kind"], fact["key_terms"].split(";")[0].strip()
        known = self.pattern.get(kind)
        if known and known[1] >= 2:       # ADAPT: pattern already confirmed twice -> save budget
            known[1] += 1
            self.findings.append(dict(fact_id=fact["fact_id"], kind=kind, query=v["query"], cause=known[0],
                                      suggestion="(same pattern as earlier failures)", evidence="deep probe skipped: pattern already confirmed twice", inferred=True))
            return
        ctl = self.tools.search(primary, fact["patient_id"],
                                thought=f'"{v["query"]}" failed. Hypothesis: page is retrievable but this phrasing type is not handled. Control test with plain term "{primary}".')
        control_ok = bool(self.rank(ctl, fact))
        token_hits = []
        if control_ok and kind == "natural_language":
            words = [w for w in re.findall(r"[A-Za-z0-9\-]+", v["query"]) if len(w) > 2 and w.lower() not in GENERIC][:4]
            for w in words:
                r = self.tools.search(w, fact["patient_id"], thought=f'Localise the failure: does the single word "{w}" find the page?')
                if self.rank(r, fact): token_hits.append(w)
        cause, suggestion = self.brain.diagnose(kind, control_ok, token_hits)
        self.pattern[kind] = [cause, (self.pattern[kind][1] + 1) if kind in self.pattern and self.pattern[kind][0] == cause else 1]
        ev = f'plain term "{primary}" {"found" if control_ok else "did NOT find"} the page' + (f'; single words that work: {token_hits}' if token_hits else "")
        self.findings.append(dict(fact_id=fact["fact_id"], kind=kind, query=v["query"], cause=cause, suggestion=suggestion, evidence=ev, inferred=False))

    def security_probe(self, fact):
        other = next(p for p in self.patients if p != fact["patient_id"])
        term = fact["key_terms"].split(";")[0].strip()
        res = self.tools.search(term, other, thought=f'Security sweep: search "{term}" as {other}; none of {fact["patient_id"]}\'s records may appear.')
        leaked = [r for r in (res or []) if r["patient_id"] != other]
        self.security.append(dict(fact_id=fact["fact_id"], searched_as=other, term=term, leaked=len(leaked)))

    def summary(self):
        by = defaultdict(lambda: [0, 0])
        for a in self.attempts:
            by[a["kind"]][1] += 1; by[a["kind"]][0] += int(a["ok"])
        return dict(variants=len(self.attempts), passed=sum(a["ok"] for a in self.attempts),
                    failed=sum(not a["ok"] for a in self.attempts), by_kind=dict(by),
                    leaks=sum(s["leaked"] for s in self.security), sweeps=len(self.security),
                    calls=self.guard.calls, max_calls=self.guard.max_calls, blocked=len(self.guard.blocked),
                    stopped=self.stopped_reason)
