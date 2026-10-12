"""python scripts/run_agent.py  ->  reports/agent_report.html + reports/agent_trace.json"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from agent.agent import Agent, load_facts
from agent.brain import get_brain
from agent.guardrails import Guardrails
from agent.report import write_reports
from src.client import is_reachable
from config import settings as S

GOAL = ("Explore Smartrecord's semantic search for each known record page. Invent realistic searches "
        "(brand names, abbreviations, typos, plain-language), find which kinds fail, investigate why, "
        "check that no patient's data leaks to another patient, and report with evidence.")

if not is_reachable():
    sys.exit(f"Search service not reachable at {S.BASE_URL}")
brain = get_brain()
agent = Agent(brain, Guardrails(), GOAL).run(load_facts())
s = agent.summary()
write_reports(agent, GOAL, brain.name)
print(f'Brain: {brain.name}')
print(f'Searches tried: {s["variants"]} | right page found: {s["passed"]} | failures: {s["failed"]} | leaks: {s["leaks"]} | calls: {s["calls"]}/{s["max_calls"]}')
print("By type:", {k: f"{p}/{t}" for k, (p, t) in s["by_kind"].items()})
causes = {}
for f in agent.findings: causes.setdefault(f["cause"], []).append(f["query"])
for c, q in causes.items(): print(f"  - {c}: {q}")
print("Wrote reports/agent_report.html and reports/agent_trace.json")
