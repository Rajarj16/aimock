"""Safety rails. The agent cannot act outside these limits - they are enforced in code, not by prompt."""
import re
from urllib.parse import urlparse
from config import settings as S

class BudgetExceeded(Exception): pass

PHI_PATTERNS = [re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),          # SSN-like
                re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),           # email
                re.compile(r"\b\d{9,}\b")]                        # long numbers (MRN / phone-like)

class Guardrails:
    def __init__(self, max_calls=None):
        self.max_calls = max_calls or S.MAX_AGENT_CALLS
        self.calls = 0
        self.allowed_host = urlparse(S.BASE_URL).hostname
        self.blocked = []

    def check_query(self, q):
        if urlparse(S.BASE_URL).hostname != self.allowed_host:
            return False, "host not in allow-list"
        for p in PHI_PATTERNS:
            if p.search(q):
                self.blocked.append(q); return False, "query looks like PHI/identifier - blocked"
        if len(q) > 200:
            return False, "query too long"
        return True, ""

    def charge(self):
        if self.calls >= self.max_calls:
            raise BudgetExceeded(f"call budget of {self.max_calls} reached")
        self.calls += 1
