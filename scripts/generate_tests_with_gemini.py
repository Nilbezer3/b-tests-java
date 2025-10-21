import os, json, pathlib, re, sys
from typing import List, Tuple

# ---- Load endpoints from payload ----
payload = json.loads(open("payload.json").read())
raw_endpoints = payload.get("endpoints", [])

# Normalize (method, path)
pairs: List[Tuple[str, str]] = []
for e in raw_endpoints:
    m = e.get("method", "GET").upper()
    p = e.get("path", "/health")
    # path param örnekleri için basit örnek değer
    p = re.sub(r"\{[^/}]+\}", "World", p)  # /greet/{name} -> /greet/World
    pairs.append((m, p))

# default /health
if not pairs:
    pairs = [("GET", "/health")]

# Küçük heuristik: POST /sum için query param ekle
fixed = []
for (m, p) in pairs:
    if m == "POST" and p.startswith("/sum") and "?" not in p:
        fixed.append((m, p + "?a=1&b=2"))
    else:
        fixed.append((m, p))
pairs = fixed

# ---- Try Gemini ----
resp_text = ""
api_key = os.getenv("GEMINI_API_KEY", "")
if api_key:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Güncel, çalışır model isimlerinden biri
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        prompt = f"""
You are a senior backend QA engineer.

Generate ONE pytest file that calls a running API using requests.

- Read BASE_URL from env (default http://localhost:8080)
- Parametrize over (method, path)
- Keep assertion as: status_code in (200,201,400,401,403,404,405,422)
- Use a single test function.
- Return ONLY Python code (no fences).

Endpoints:
{chr(10).join([f"- {m} {p}" for m,p in pairs])}
"""
        resp = model.generate_content(prompt)
        resp_text = (getattr(resp, "text", "") or "").strip()
        # code fence temizliği
        resp_text = re.sub(r"^```(?:python)?\s*", "", resp_text)
        resp_text = re.sub(r"\s*```$", "", resp_text)
    except Exception as e:
        print(f"[Gemini] failed: {e}", file=sys.stderr)

# ---- Fallback (robust, parametrize) ----
if not resp_text:
    resp_text = f"""# generated (fallback)
import os, requests, pytest
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

@pytest.mark.parametrize("method,path", {pairs})
def test_smoke(method, path):
    url = BASE_URL + path
    r = requests.request(method, url, timeout=10)
    assert r.status_code in (200,201,400,401,403,404,405,422), f"{{method}} {{url}} -> {{r.status_code}} body={{r.text[:200]}}"
"""

# ---- Write test file ----
outdir = pathlib.Path("tests/generated")
outdir.mkdir(parents=True, exist_ok=True)
(outdir / "test_generated_endpoints.py").write_text(resp_text, encoding="utf-8")
print("written tests/generated/test_generated_endpoints.py")
