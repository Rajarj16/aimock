"""python scripts/run_evaluation.py  ->  console scorecard + reports/results.csv + reports/scorecard.html"""
import sys, csv, html, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from config import settings as S
from src.metrics import evaluate

rows, s = evaluate()
K = S.TOP_K
S.REPORTS.mkdir(exist_ok=True)

# ---------- CSV ----------
cols = ["id","category","query","expected_doc","expected_page","top_hit","rank","passed","latency_ms","notes"]
with open(S.REPORTS / "results.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)

pct = lambda x: f"{x:.0%}"
word = lambda ok: "PASS" if ok else "FAIL"
gates = [(f"Hit rate@{K}", "Right page is in the top results", pct(s["hit_rate_at_k"]), f">= {S.MIN_HIT_RATE:.0%}", s["hit_rate_at_k"] >= S.MIN_HIT_RATE),
         ("MRR", "Right page is ranked near the top", f'{s["mrr"]:.2f}', f">= {S.MIN_MRR}", s["mrr"] >= S.MIN_MRR),
         ("No-result accuracy", "Nonsense searches return nothing", pct(s["no_result_accuracy"]), ">= 90%", s["no_result_accuracy"] >= .9),
         ("Cross-patient leak test", "Never shows another patient's record", pct(s["security_pass_rate"]), "= 100%", s["security_pass_rate"] == 1),
         ("Latency p95", "95% of searches are this fast or faster", f'{s["latency_p95_ms"]:.0f} ms', f"< {S.MAX_P95_MS:.0f} ms", s["latency_p95_ms"] < S.MAX_P95_MS)]
all_ok = all(g[4] for g in gates)
fails = [r for r in rows if not r["passed"]]

# ---------- console ----------
print("\n=== SMARTRECORD SEARCH QUALITY SCORECARD ===")
print(f'Queries: {s["total_queries"]} (search-type: {s["positive_queries"]})')
print(f'Hit@1 {pct(s["hit_rate_at_1"])} | Hit@3 {pct(s["hit_rate_at_3"])} | Hit@{K} {pct(s["hit_rate_at_k"])} | MRR {s["mrr"]:.2f}')
for n, _, v, t, ok in gates: print(f"  {word(ok):4}  {n:26}{v:>8}   (target {t})")
print("\nBy category:")
for c, v in s["by_category"].items(): print(f'  {c:17}{v["passed"]}/{v["total"]}  {pct(v["rate"])}')
print(f"\nFailed queries ({len(fails)}):")
for r in fails: print(f'  {r["id"]} [{r["category"]}] "{r["query"]}" expected {r["expected_doc"] or "nothing"} p{r["expected_page"]} -> got {r["top_hit"]}')

# ---------- HTML ----------
ADVICE = {
 "exact": "Core retrieval problem: even literal terms are missed. High priority - check indexing and chunking.",
 "brand_generic": "Brand and generic drug names are not linked. Ask Dev about a drug-name synonym list or a medical-aware embedding model.",
 "synonym": "Related medical terms are not connected. Review the embedding model and synonym handling.",
 "abbreviation": "Medical abbreviations (HTN, MI...) are not expanded. Ask Dev to add an abbreviation-expansion step.",
 "typo": "Misspellings break the search. Ask Dev about fuzzy matching or spell correction.",
 "natural_language": "Plain-language questions are not understood. Consider query rewriting or a stronger embedding model.",
 "negative": "System returns results for irrelevant searches. Ask Dev to add a minimum relevance-score threshold.",
 "security": "CRITICAL: another patient's data was returned. Stop and escalate to Dev and compliance before any further testing.",
}
esc = html.escape
def row_html(r):
    ok = r["passed"]
    exp = f'{r["expected_doc"]} p{r["expected_page"]}' if r["expected_doc"] else "(nothing)"
    return (f'<tr class="{"ok" if ok else "bad"}" data-r="{"pass" if ok else "fail"}"><td>{r["id"]}</td><td>{r["category"]}</td><td>{esc(r["query"])}</td>'
            f'<td>{exp}</td><td>{r["top_hit"]}</td><td>{r["rank"] or "-"}</td><td>{word(ok)}</td></tr>')
bars = "".join(f'<div class="bar"><span>{c.replace("_"," ")}</span><div class="track"><div class="fill {"low" if v["rate"]<.8 else ""}" style="width:{v["rate"]*100:.0f}%"></div></div><b>{v["passed"]}/{v["total"]}</b></div>' for c, v in s["by_category"].items())
grows = "".join(f'<tr class="{"ok" if ok else "bad"}"><td><b>{n}</b><br><small>{d}</small></td><td>{t}</td><td>{v}</td><td>{word(ok)}</td></tr>' for n, d, v, t, ok in gates)
if fails:
    items = "".join(f'<li><b>{esc(r["query"])}</b> <small>({r["id"]}, {r["category"]})</small><br>Expected {r["expected_doc"] or "nothing"} {("p"+r["expected_page"]) if r["expected_page"] else ""}; got {r["top_hit"]}<br><em>{ADVICE.get(r["category"], "")}</em></li>' for r in fails)
    fail_block = f'<ol class="fails">{items}</ol>'
else:
    fail_block = "<p>No failures in this run.</p>"
verdict = ("MEETS TARGETS" if all_ok else "BELOW TARGET")
verdict_cls = "vok" if all_ok else "vbad"
n_fail_gates = sum(1 for g in gates if not g[4])
verdict_txt = ("All quality gates passed." if all_ok else f"{n_fail_gates} of {len(gates)} quality gates not met; {len(fails)} of {s['total_queries']} queries failed.")

page = f"""<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Smartrecord AI Search Quality Report</title>
<style>
:root{{--bg:#fff;--fg:#1f2430;--mut:#6b7280;--line:#e3e6ec;--ok:#0a7d33;--bad:#c0281c;--bl:#2f6fed;--card:#f7f8fa}}
@media(prefers-color-scheme:dark){{:root{{--bg:#14161b;--fg:#e6e8ee;--mut:#9aa3b2;--line:#2b2f3a;--card:#1c1f27}}}}
body{{font-family:system-ui,Segoe UI,Arial;margin:0;background:var(--bg);color:var(--fg)}}main{{max-width:1050px;margin:0 auto;padding:28px 20px 60px}}
h1{{margin:0 0 4px}}h2{{margin:34px 0 8px;border-bottom:1px solid var(--line);padding-bottom:6px}}.sub{{color:var(--mut);font-size:14px}}
.verdict{{margin:18px 0;padding:16px 20px;border-radius:12px;font-size:16px}}.vok{{background:#e8f6ed;color:#0a5d27}}.vbad{{background:#fdecea;color:#9b1c12}}.verdict b{{font-size:22px;display:block}}
.cards{{display:flex;gap:14px;flex-wrap:wrap}}.card{{flex:1;min-width:140px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 18px;font-size:13px;color:var(--mut)}}.card b{{display:block;font-size:30px;color:var(--fg)}}
table{{border-collapse:collapse;width:100%;margin:10px 0}}td,th{{border:1px solid var(--line);padding:7px 10px;text-align:left;font-size:14px;vertical-align:top}}th{{background:var(--card)}}
tr.ok td:last-child{{color:var(--ok);font-weight:600}}tr.bad td:last-child{{color:var(--bad);font-weight:600}}tr.bad{{background:rgba(192,40,28,.08)}}small{{color:var(--mut)}}
.bar{{display:flex;align-items:center;gap:10px;margin:7px 0}}.bar span{{width:150px;text-transform:capitalize}}.track{{flex:1;background:var(--line);height:14px;border-radius:7px}}.fill{{background:var(--bl);height:14px;border-radius:7px}}.fill.low{{background:var(--bad)}}
.fails li{{margin:10px 0;line-height:1.5}}.fails em{{color:var(--mut)}}.note{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;font-size:14px;line-height:1.55}}
.tools button{{border:1px solid var(--line);background:var(--card);color:var(--fg);padding:5px 14px;border-radius:16px;cursor:pointer;margin-right:6px}}.tools button.on{{background:var(--bl);color:#fff;border-color:var(--bl)}}
dl{{display:grid;grid-template-columns:180px 1fr;gap:6px 14px;font-size:14px}}dt{{font-weight:600}}dd{{margin:0;color:var(--mut)}}
</style><main>
<h1>Smartrecord - AI Search Quality Report</h1>
<div class=sub>Generated {datetime.datetime.now():%Y-%m-%d %H:%M} &nbsp;|&nbsp; Environment: {esc(S.ENV_NAME)} &nbsp;|&nbsp; Target: {esc(S.BASE_URL)} &nbsp;|&nbsp; Model/build: {esc(S.MODEL_VERSION)} &nbsp;|&nbsp; Golden set: {s["total_queries"]} queries</div>
<div class="verdict {verdict_cls}"><b>{verdict}</b>{verdict_txt}</div>
<div class=cards>
<div class=card>Hit rate@{K}<b>{pct(s["hit_rate_at_k"])}</b></div><div class=card>Hit rate@1<b>{pct(s["hit_rate_at_1"])}</b></div><div class=card>MRR<b>{s["mrr"]:.2f}</b></div>
<div class=card>Cross-patient leaks<b>{"0" if s["security_pass_rate"]==1 else "FOUND"}</b></div><div class=card>Latency p50 / p95<b style="font-size:22px">{s["latency_p50_ms"]:.0f} / {s["latency_p95_ms"]:.0f} ms</b></div></div>

<h2>1. Quality gates</h2><p class=sub>Targets were agreed with the team before testing. Each gate must pass.</p>
<table><tr><th>Metric</th><th>Target</th><th>Actual</th><th>Result</th></tr>{grows}</table>

<h2>2. Pass rate by type of search</h2>{bars}
<p class=sub>Red bars are below 80%. Each type of search exercises a different capability of the AI.</p>

<h2>3. What failed and what to do about it</h2>{fail_block}

<h2>4. All results</h2>
<div class=tools><button class=on onclick="f('all',this)">All ({len(rows)})</button><button onclick="f('fail',this)">Failed ({len(fails)})</button><button onclick="f('pass',this)">Passed ({len(rows)-len(fails)})</button></div>
<table id=t><tr><th>ID</th><th>Type</th><th>Search query</th><th>Expected</th><th>Top result returned</th><th>Rank</th><th>Result</th></tr>{"".join(row_html(r) for r in rows)}</table>

<h2>5. How to read this report</h2>
<div class=note><dl>
<dt>Golden set</dt><dd>A list of searches where we already know the correct answer, like an answer key.</dd>
<dt>Hit rate@{K}</dt><dd>Out of all searches, how often the right page appeared in the top {K} results.</dd>
<dt>Hit rate@1</dt><dd>How often the right page was the very first result.</dd>
<dt>MRR</dt><dd>Score for ranking quality: 1.0 means the right page is always first; 0.5 means usually second.</dd>
<dt>No-result accuracy</dt><dd>For nonsense or unrelated searches, how often the system correctly returned nothing.</dd>
<dt>Cross-patient leak</dt><dd>Whether a search ever returned another patient's record. Must always be zero.</dd>
<dt>Latency p50 / p95</dt><dd>Typical response time, and the time 95% of searches beat.</dd>
</dl></div>
<h2>6. Method</h2>
<div class=note>Black-box evaluation through the search API. Each golden-set query is sent as a real request; the returned documents and page numbers are compared with the expected answer. Metrics are calculated over the whole set and compared with agreed targets. Test data: synthetic or de-identified records only; no real patient information is used. Results reflect this golden set and this build only, and should be re-run after any model or configuration change.</div>
</main>
<script>function f(m,b){{document.querySelectorAll('.tools button').forEach(x=>x.classList.remove('on'));b.classList.add('on');
document.querySelectorAll('#t tr[data-r]').forEach(r=>r.style.display=(m==='all'||r.dataset.r===m)?'':'none')}}</script></html>"""
(S.REPORTS / "scorecard.html").write_text(page, encoding="utf-8")
print(f"\nWrote {S.REPORTS/'results.csv'} and {S.REPORTS/'scorecard.html'}")
