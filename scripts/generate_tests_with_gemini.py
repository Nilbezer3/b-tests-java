import os, json, pathlib, re, sys

# ---------- 1) payload.json'dan endpointleri oku ----------
payload = json.loads(open("payload.json").read())
raw = payload.get("endpoints", [])

pairs = []
for e in raw:
    m = e.get("method", "GET").upper()
    p = e.get("path", "/health")
    # /greet/{name} -> /greet/World
    p = re.sub(r"\{[^/}]+\}", "World", p)
    # POST /sum için query param ekle
    if m == "POST" and p.startswith("/sum") and "?" not in p:
        p = p + "?a=1&b=2"
    pairs.append((m, p))

# hiçbir endpoint yoksa default
if not pairs:
    pairs = [("GET", "/health")]
java_code = None
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY tanımlı değil; AI ile test üretemiyorum.")

try:
    import google.generativeai as genai

    genai.configure(api_key=api_key)

    endpoints_block = "\n".join([f"- {m} {p}" for m, p in pairs])

    prompt = f"""

Generate ONE Java test file that calls a running Spring Boot API using RestAssured and JUnit 5.

Requirements:
- Package MUST be: com.generated
- Class MUST be: ApiSmokeIT
- Use JUnit 5 parameterized test with @ParameterizedTest and @MethodSource.
- Use io.restassured.RestAssured.given() to send HTTP requests.
- Read BASE_URL from environment variable (default http://localhost:8080 if not set).
- Parametrize over (method, path).
- Status assertion: statusCode(anyOf(is(200), is(201), is(400), is(401), is(403), is(404), is(405), is(422))).
- Import org.junit.jupiter.params.provider.Arguments and java.util.stream.Stream.
- Return ONLY Java code, no explanations, no comments, no code fences.

Endpoints to cover:
{endpoints_block}
"""

    model = genai.GenerativeModel("models/gemini-2.5-flash")
    resp = model.generate_content(prompt)
    text = (getattr(resp, "text", "") or "").strip()

   
    text = re.sub(r"^```(?:java)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    if text and "class ApiSmokeIT" in text:
        java_code = text
    else:
        raise RuntimeError("[Gemini] response boş veya 'class ApiSmokeIT' içermiyor; test üretimi başarısız.")

except Exception as e:
    
    raise RuntimeError(f"[Gemini] hata: {e}") from e

if not java_code:
    raise RuntimeError("Gemini'den hiç Java kodu alınamadı; ApiSmokeIT.java yazılmadı.")


outdir = pathlib.Path("src/test/java/com/generated")
outdir.mkdir(parents=True, exist_ok=True)
outfile = outdir / "ApiSmokeIT.java"
outfile.write_text(java_code, encoding="utf-8")
print(f"Wrote {outfile}")