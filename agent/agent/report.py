import html, json, datetime
from collections import defaultdict
from config import settings as S
esc = html.escape

def write_reports(agent, goal, brain_name):
    S.REPORTS.mkdir(exist_ok=True)
    s = agent.summary()
    (S.REPORTS / "agent_trace.json").write_text(json.dumps(agent.trace, indent=2), encoding="utf-8")
    pct = lambda a, b: f"{(a / b):.0%}" if b else "-"
    by_cause = defaultdict(list)
    for f in agent.findings: by_cause[f["cause"]].append(f)
    bars = "".join(f'<div class="bar"><span>{k.replace("_"," ")}</span><div class="track"><div class="fill {"low" if p/t<.8 else ""}" style="width:{p/t*100:.0f}%"></div></div><b>{p}/{t}</b></div>' for k, (p, t) in s["by_kind"].items())
    cause_html = ""
    for cause, items in sorted(by_cause.items(), key=lambda kv: -len(kv[1])):
        first = next((i for i in items if not i["inferred"]), items[0])
        ex = "".join(f'<li><code>{esc(i["query"])}</code> <small>({i["fact_id"]}, {i["kind"]}){" - inferred" if i["inferred"] else ""}</small></li>' for i in items)
        cause_html += (f'<div class="find"><h3>{cause.replace("_"," ")} <small>({len(items)} failing searches)</small></h3>'
                       f'<p><b>Evidence:</b> {esc(first["evidence"])}</p><p><b>Suggested action for Dev:</b> {esc(first["suggestion"])}</p><ul>{ex}</ul></div>')
    if not cause_html: cause_html = "<p>No failures found in this run.</p>"
    leak_txt = "0 - none found" if s["leaks"] == 0 else f'{s["leaks"]} LEAK(S) FOUND - CRITICAL'
    trace_rows = "".join(f'<tr class="{"bad" if t.get("blocked") else ""}"><td>{t["step"]}</td><td>{esc(t["thought"])}</td><td><code>{esc(t["action"])}</code></td><td>{esc(t["observation"])}</td></tr>' for t in agent.trace)
    stop = f'<div class="note warn">Run stopped early: {esc(s["stopped"])}</div>' if s["stopped"] else ""
    page = f"""<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Smartrecord Agentic Test Report</title>
<style>:root{{--bg:#fff;--fg:#1f2430;--mut:#6b7280;--line:#e3e6ec;--bad:#c0281c;--bl:#2f6fed;--card:#f7f8fa}}
@media(prefers-color-scheme:dark){{:root{{--bg:#14161b;--fg:#e6e8ee;--mut:#9aa3b2;--line:#2b2f3a;--card:#1c1f27}}}}
body{{font-family:system-ui,Segoe UI,Arial;margin:0;background:var(--bg);color:var(--fg)}}main{{max-width:1050px;margin:0 auto;padding:28px 20px 60px}}
h2{{margin:32px 0 8px;border-bottom:1px solid var(--line);padding-bottom:6px}}h3{{margin:0 0 6px;text-transform:capitalize}}.sub,small{{color:var(--mut)}}
.cards{{display:flex;gap:14px;flex-wrap:wrap;margin:16px 0}}.card{{flex:1;min-width:130px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;font-size:13px;color:var(--mut)}}.card b{{display:block;font-size:28px;color:var(--fg)}}
.note{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;font-size:14px;line-height:1.55}}.warn{{border-color:var(--bad)}}
.find{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:12px 0;font-size:14px}}.find ul{{margin:6px 0 0}}
.bar{{display:flex;align-items:center;gap:10px;margin:7px 0}}.bar span{{width:160px;text-transform:capitalize}}.track{{flex:1;background:var(--line);height:14px;border-radius:7px}}.fill{{background:var(--bl);height:14px;border-radius:7px}}.fill.low{{background:var(--bad)}}
table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}}th{{background:var(--card)}}tr.bad{{background:rgba(192,40,28,.1)}}code{{font-size:12px}}</style><main>
<h1>Smartrecord - Agentic Test Report</h1>
<div class=sub>Generated {datetime.datetime.now():%Y-%m-%d %H:%M} | Target: {esc(S.BASE_URL)} | Brain: {esc(brain_name)} | Build: {esc(S.MODEL_VERSION)}</div>
<div class=note style="margin-top:14px"><b>Goal given to the agent:</b> {esc(goal)}<br><b>Status:</b> findings below are agent-generated and need human review before any bug is filed.</div>{stop}
<div class=cards><div class=card>Searches tried<b>{s["variants"]}</b></div><div class=card>Found right page<b>{pct(s["passed"], s["variants"])}</b></div><div class=card>Failures investigated<b>{s["failed"]}</b></div>
<div class=card>Cross-patient leaks<b style="font-size:20px">{leak_txt}</b></div><div class=card>API calls used<b>{s["calls"]}/{s["max_calls"]}</b></div></div>
<h2>1. Pass rate by type of search the agent invented</h2>{bars}
<h2>2. What the agent found (grouped by likely root cause)</h2>{cause_html}
<h2>3. Security sweep</h2><div class=note>{s["sweeps"]} cross-patient searches run. Leaks: {leak_txt}. Guardrail blocks: {s["blocked"]}.</div>
<h2>4. Full audit trail (every step the agent took)</h2><table><tr><th>#</th><th>Why (thought)</th><th>Action</th><th>What came back</th></tr>{trace_rows}</table>
<h2>5. Limits</h2><div class=note>Rule-based demo brain: query variants and diagnoses come from fixed rules. An approved LLM would invent more varied searches. Diagnoses are hypotheses supported by probe evidence, not proof. Results apply to this dataset and build only.</div>
</main></html>"""
    (S.REPORTS / "agent_report.html").write_text(page, encoding="utf-8")
