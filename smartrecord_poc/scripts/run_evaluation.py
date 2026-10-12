"""Runs the golden set, prints a scorecard, writes reports/results.csv and reports/scorecard.html"""
import sys, csv, pathlib, html, datetime
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "tests"))
from metrics import evaluate

OUT = pathlib.Path(__file__).parent.parent / "reports"
rows, s = evaluate()

with open(OUT / "results.csv", "w", newline="", encoding="utf-8") as f:
    cols = ["id","category","query","expected_doc","expected_page","top_hit","rank","passed","latency_ms","notes"]
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def pct(x): return f"{x:.0%}"
gate = lambda ok: "PASS" if ok else "FAIL"
gates = [("Hit rate@5", pct(s["hit_rate_at_5"]), ">= 90%", s["hit_rate_at_5"] >= .9),
         ("MRR", f'{s["mrr"]:.2f}', ">= 0.80", s["mrr"] >= .8),
         ("No-result accuracy", pct(s["no_result_accuracy"]), ">= 90%", s["no_result_accuracy"] >= .9),
         ("Cross-patient leak test", pct(s["security_pass_rate"]), "= 100%", s["security_pass_rate"] == 1),
         ("Latency p95", f'{s["latency_p95_ms"]:.0f} ms', "< 500 ms", s["latency_p95_ms"] < 500)]

print("\n=== SMARTRECORD SEARCH QUALITY SCORECARD ===")
print(f'Queries: {s["total_queries"]}  (search-type: {s["positive_queries"]})')
print(f'Hit@1 {pct(s["hit_rate_at_1"])} | Hit@3 {pct(s["hit_rate_at_3"])} | Hit@5 {pct(s["hit_rate_at_5"])} | MRR {s["mrr"]:.2f}')
for n, v, t, ok in gates: print(f"  {gate(ok):4}  {n:26} {v:>8}   (target {t})")
print("\nBy category:")
for c, v in s["by_category"].items(): print(f'  {c:17} {v["passed"]}/{v["total"]}  {pct(v["rate"])}')
fails = [r for r in rows if not r["passed"]]
print(f"\nFailed queries ({len(fails)}):")
for r in fails: print(f'  {r["id"]} [{r["category"]}] "{r["query"]}" expected {r["expected_doc"] or "nothing"} p{r["expected_page"]} -> got {r["top_hit"]}')

# ---------- HTML scorecard ----------
def row_html(r):
    cls = "ok" if r["passed"] else "bad"
    return (f'<tr class="{cls}"><td>{r["id"]}</td><td>{r["category"]}</td><td>{html.escape(r["query"])}</td>'
            f'<td>{r["expected_doc"] or "(nothing)"} {("p"+r["expected_page"]) if r["expected_page"] else ""}</td>'
            f'<td>{r["top_hit"]}</td><td>{r["rank"] or "-"}</td><td>{"PASS" if r["passed"] else "FAIL"}</td></tr>')
cat_bars = "".join(f'<div class="bar"><span>{c}</span><div class="track"><div class="fill" style="width:{v["rate"]*100:.0f}%"></div></div><b>{v["passed"]}/{v["total"]}</b></div>' for c, v in s["by_category"].items())
gate_rows = "".join(f'<tr class="{"ok" if ok else "bad"}"><td>{n}</td><td>{t}</td><td>{v}</td><td>{gate(ok)}</td></tr>' for n, v, t, ok in gates)
doc = f"""<!doctype html><meta charset=utf-8><title>Smartrecord AI Search Scorecard</title>
<style>body{{font-family:system-ui;margin:32px;color:#222}}h1{{margin-bottom:0}}.sub{{color:#666}}
.cards{{display:flex;gap:16px;margin:20px 0}}.card{{border:1px solid #ddd;border-radius:10px;padding:14px 20px}}.card b{{font-size:28px;display:block}}
table{{border-collapse:collapse;width:100%;margin:12px 0 28px}}td,th{{border:1px solid #ddd;padding:6px 10px;text-align:left;font-size:14px}}
tr.ok td:last-child{{color:#0a7d33;font-weight:600}}tr.bad{{background:#fff1f0}}tr.bad td:last-child{{color:#c0281c;font-weight:600}}
.bar{{display:flex;align-items:center;gap:10px;margin:6px 0}}.bar span{{width:140px}}.track{{flex:1;background:#eee;height:14px;border-radius:7px}}.fill{{background:#2f6fed;height:14px;border-radius:7px}}</style>
<h1>Smartrecord - AI Search Quality Scorecard</h1><div class=sub>Generated {datetime.datetime.now():%Y-%m-%d %H:%M} | {s["total_queries"]} golden-set queries | MOCK data</div>
<div class=cards><div class=card>Hit rate@5<b>{pct(s["hit_rate_at_5"])}</b></div><div class=card>Hit rate@1<b>{pct(s["hit_rate_at_1"])}</b></div><div class=card>MRR<b>{s["mrr"]:.2f}</b></div><div class=card>Cross-patient leaks<b>{"0" if s["security_pass_rate"]==1 else "FOUND"}</b></div><div class=card>Latency p95<b>{s["latency_p95_ms"]:.0f} ms</b></div></div>
<h2>Quality gates</h2><table><tr><th>Metric</th><th>Target</th><th>Actual</th><th>Result</th></tr>{gate_rows}</table>
<h2>Pass rate by query type</h2>{cat_bars}
<h2>All results</h2><table><tr><th>ID</th><th>Type</th><th>Query</th><th>Expected</th><th>Top result</th><th>Rank</th><th>Result</th></tr>{"".join(row_html(r) for r in rows)}</table>"""
(OUT / "scorecard.html").write_text(doc, encoding="utf-8")
print(f"\nWrote {OUT/'results.csv'} and {OUT/'scorecard.html'}")
