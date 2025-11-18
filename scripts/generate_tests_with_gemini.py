import os, json, pathlib, re, sys

# payload.json'dan endpointleri oku 
# A repo'sundan gelen client_payload burada duruyor
with open("payload.json", encoding="utf-8") as f:
    payload = json.load(f)

raw = payload.get("endpoints", [])

# raw = [{ "method": "GET", "path": "/ping" }, ...]
pairs = []
for e in raw:
    m = (e.get("method") or "GET").upper()
    p = e.get("path") or "/health"

    # Eğer hâlâ path param kalmışsa ("/greet/{name}" gibi) kaba bir default ver
    # A tarafındaki extract_endpoints genelde zaten /greet/1, /echo?msg=... olarak yolluyor.
    p = re.sub(r"\{[^/}]+\}", "1", p)

    pairs.append((m, p))

# Hiç endpoint yoksa, bari /health'i test et
if not pairs:
    pairs = [("GET", "/health")]

# Gemini API key kontrolü 
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY tanımlı değil; AI ile test üretemiyorum.")

# Gemini'ye prompt gönder
try:
    import google.generativeai as genai

    genai.configure(api_key=api_key)

    endpoints_block = "\n".join(f"- {m} {p}" for (m, p) in pairs)

    prompt = f"""
You are a senior backend QA engineer.

Generate ONE Java test file that calls a running Spring Boot API using RestAssured and JUnit 5.

Requirements:
- Package MUST be: com.generated
- Class MUST be: ApiSmokeIT
- Use JUnit 5 parameterized test with @ParameterizedTest and @MethodSource.
- Use io.restassured.http.Method enum for HTTP methods.
- The method source should return Stream<Arguments> where each Arguments.of has (Method, String path).
- In the test method, call: RestAssured.given().request(method, path)
- Read BASE_URL from environment variable BASE_URL (default http://localhost:8080 if not set).
- Status assertion: statusCode(anyOf(is(200), is(201), is(400), is(401), is(403), is(404), is(405), is(422))).
- Import these classes:
  - io.restassured.RestAssured
  - io.restassured.http.Method
  - org.junit.jupiter.api.BeforeAll
  - org.junit.jupiter.params.ParameterizedTest
  - org.junit.jupiter.params.provider.Arguments
  - org.junit.jupiter.params.provider.MethodSource
  - java.util.stream.Stream
  - static org.hamcrest.Matchers.anyOf
  - static org.hamcrest.Matchers.is
- Return ONLY Java code. No explanations, no markdown, no comments.

Endpoints to cover:
{endpoints_block}
"""

    print("=== Prompt to Gemini ===")
    print(endpoints_block)

    model = genai.GenerativeModel("models/gemini-2.5-flash")
    resp = model.generate_content(prompt)
    text = (getattr(resp, "text", "") or "").strip()

    # ```java ... ``` gibi code fence'leri temizle
    text = re.sub(r"^```(?:java)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    if not text or "class ApiSmokeIT" not in text:
        raise RuntimeError("Gemini response boş veya 'class ApiSmokeIT' içermiyor.")

    java_code = text

# quota, rate limit gibi hataları yakalıyor
except Exception as e:
    print("\nGEMINI TEST GENERATION FAILED", file=sys.stderr)
    print(f"[HATA]: {e}", file=sys.stderr)
    print("➡ Muhtemel sebep: free quota veya rate limit aşıldı.", file=sys.stderr)
    print("➡ Çözüm: Biraz bekleyip workflow'u yeniden çalıştır.", file=sys.stderr)
    print("➡ Not: Mevcut src/test/java/com/generated/ApiSmokeIT.java dosyası DEĞİŞMEDİ.", file=sys.stderr)
    sys.exit(1)

#  Başarılıysa Java dosyasını yaz 
outdir = pathlib.Path("src/test/java/com/generated")
outdir.mkdir(parents=True, exist_ok=True)
outfile = outdir / "ApiSmokeIT.java"
outfile.write_text(java_code, encoding="utf-8")
print(f"Wrote {outfile}")
