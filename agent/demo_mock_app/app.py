from flask import Flask, request, jsonify, render_template_string
from search_engine import search
app = Flask(__name__)
PAGE = """<h1>Smartrecord (mock)</h1>
<input data-testid="search-box" id="q"> <button data-testid="search-btn" onclick="go()">Search</button>
<ul data-testid="results" id="r"></ul>
<script>async function go(){const q=document.getElementById('q').value;
const j=await (await fetch('/api/search',{method:'POST',headers:{'Content-Type':'application/json','X-Token':'demo-token'},body:JSON.stringify({query:q,patient_id:'P001'})})).json();
document.getElementById('r').innerHTML=j.results.map(x=>`<li data-testid="result">${x.doc} - page ${x.page}: ${x.snippet}</li>`).join('')||'<li data-testid="no-results">No results</li>';}</script>"""

@app.get("/")
def home(): return render_template_string(PAGE)

@app.post("/api/search")
def api_search():
    if request.headers.get("X-Token") != "demo-token":
        return jsonify(error="unauthorized"), 401
    b = request.get_json(force=True)
    return jsonify(query=b.get("query", ""), results=search(b.get("query", ""), b.get("patient_id")))

if __name__ == "__main__":
    app.run(port=5000)
