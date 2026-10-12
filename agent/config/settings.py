"""ALL environment-specific values live here (read from .env). Change .env, not the code."""
import os, pathlib
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLDEN_SET = pathlib.Path(os.getenv("GOLDEN_SET_PATH", ROOT / "data" / "golden_set.csv"))
REPORTS = ROOT / "reports"

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
SEARCH_PATH = os.getenv("SEARCH_PATH", "/api/search")
AUTH_HEADER_NAME = os.getenv("AUTH_HEADER_NAME", "X-Token")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")

REQ_QUERY = os.getenv("REQ_QUERY_FIELD", "query")
REQ_PATIENT = os.getenv("REQ_PATIENT_FIELD", "patient_id")
RESP_RESULTS = os.getenv("RESP_RESULTS_FIELD", "results")
RESP_DOC = os.getenv("RESP_DOC_FIELD", "doc")
RESP_PAGE = os.getenv("RESP_PAGE_FIELD", "page")
RESP_PATIENT = os.getenv("RESP_PATIENT_FIELD", "patient_id")

TOP_K = int(os.getenv("TOP_K", "5"))
MIN_HIT_RATE = float(os.getenv("MIN_HIT_RATE", "0.90"))
MIN_MRR = float(os.getenv("MIN_MRR", "0.80"))
MAX_P95_MS = float(os.getenv("MAX_P95_MS", "500"))

MODEL_VERSION = os.getenv("MODEL_VERSION", "not specified")
ENV_NAME = os.getenv("ENV_NAME", "test")

# ---- agent settings ----
MAX_AGENT_CALLS = int(os.getenv("MAX_AGENT_CALLS", "250"))   # hard budget of API calls per run
BRAIN = os.getenv("BRAIN", "rule")                            # rule | llm
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "")                  # company-APPROVED endpoint only
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_AUTH_HEADER = os.getenv("LLM_AUTH_HEADER", "Authorization")
LLM_MODEL = os.getenv("LLM_MODEL", "")
FACTS_FILE = ROOT / "data" / "facts.csv"
