"""The ONLY things the agent can do. Read-only: it can search, nothing else. Every call is traced."""
from src.client import search as api_search

class Tools:
    def __init__(self, guard, trace):
        self.guard, self.trace = guard, trace

    def search(self, query, patient_id, thought=""):
        step = len(self.trace) + 1
        ok, why = self.guard.check_query(query)
        if not ok:
            self.trace.append(dict(step=step, thought=thought, action=f"search({query!r}, {patient_id})",
                                   observation=f"BLOCKED by guardrail: {why}", blocked=True))
            return None
        self.guard.charge()
        results, ms = api_search(query, patient_id)
        top = ", ".join(f'{r["doc"]} p{r["page"]}' for r in results[:3]) or "no results"
        self.trace.append(dict(step=step, thought=thought, action=f"search({query!r}, {patient_id})",
                               observation=f"{len(results)} result(s); top: {top}  [{ms:.0f} ms]"))
        return results
