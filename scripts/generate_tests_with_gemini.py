import os
import json
import pathlib
import re
import sys

# ---------- 1) payload.json'dan endpointleri oku ----------
try:
    payload = json.loads(open("payload.json").read())
except FileNotFoundError:
    raise RuntimeError("payload.json bulunamadı. Workflow'da veya lokal testte önce payload.json oluşturulmalı.")

raw = payload.get("endpoints", [])

pairs = []
for e in raw:
    m = e.get("method", "GET").upper().strip()
    p = e.get("path", "/health").strip()

    # Path param'ları dummy değere çevir:  /users/{id} -> /users/1
    p = re.sub(r"\{[^/}]+\}", "1", p)

    # Bazı endpoint'ler için pratik örnek query param'ları ekleyelim
    # (bunlar tamamen sistemin düzgün 2xx dönmesi için "fixture" gibi)
    if m == "GET" and p == "/echo":
        # echo için msg gerekiyor, yoksa 400
        p = "/echo?msg=hello-from-tests"

    if m == "POST" and p == "/sum":
        # sum için a,b gerekiyor, yoksa 400
        p = "/sum?a=1&b=2"

    pairs.append((m, p))

# Hiç endpoint yoksa en azından /health test edilsin
if not pairs:
    pairs = [("GET", "/health")]

# ---------- 2) Gemini API key kontrol ----------
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY tanımlı değil; AI ile test üretemiyorum.")

# ---------- 3) Gemini'ye verilecek endpoint listesi (debug için de güzel) ----------
endpoints_block = "\n".join([f"- {m} {p}" for (m, p) in pairs])

# ---------- 4) Gemini'den Java test kodu iste ----------
try:
    import google.generativeai as genai
except ImportError:
    raise RuntimeError("google-generativeai paketi yüklü değil. 'pip install google-generativeai' gerekir.")

genai.configure(api_key=api_key)

prompt = f"""
You are a senior backend QA engineer.

Generate ONE Java test file that calls a running Spring Boot API using RestAssured and JUnit 5.

**VERY IMPORTANT REQUIREMENTS:**

- Package MUST be exactly: com.generated
- Class name MUST be exactly: ApiSmokeIT

- Use JUnit 5 parameterized test:
  - Use @ParameterizedTest and @MethodSource.
  - The method source MUST be named apiEndpoints and return Stream<Arguments>.
  - Each Arguments must contain: (String method, String path).

- Use RestAssured to send HTTP requests:
  - In @BeforeAll, read BASE_URL from environment variable "BASE_URL".
  - If BASE_URL is not set or empty, default to "http://localhost:8080".
  - Set RestAssured.baseURI accordingly.

- In the parameterized test:
  - Signature MUST be: void smokeTestApi(String method, String path)
  - Call the endpoint with:
      Response response = RestAssured
          .given()
          .when()
          .request(method, path);
  - Then extract the status code and assert that it is in
      (200, 201, 204, 400, 401, 403, 404, 405, 422)
    using Hamcrest matchers:
      import static org.hamcrest.Matchers.anyOf;
      import static org.hamcrest.Matchers.is;

- Use imports:
  - import io.restassured.RestAssured;
  - import io.restassured.response.Response;
  - import org.junit.jupiter.api.BeforeAll;
  - import org.junit.jupiter.params.ParameterizedTest;
  - import org.junit.jupiter.params.provider.Arguments;
  - import org.junit.jupiter.params.provider.MethodSource;
  - import java.util.stream.Stream;

- DO NOT include comments or explanations.
- DO NOT use code fences.
- Only output valid Java code for the single file.

Endpoints to cover (method and path, including query params where present):
{endpoints_block}
"""

print("=== Prompt to Gemini ===", file=sys.stderr)
print(endpoints_block, file=sys.stderr)

model = genai.GenerativeModel("models/gemini-2.5-flash")
resp = model.generate_content(prompt)
text = (getattr(resp, "text", "") or "").strip()

# code fence temizliği (çok nadiren gerek)
text = re.sub(r"^```(?:java)?\s*", "", text)
text = re.sub(r"\s*```$", "", text)

if not text or "class ApiSmokeIT" not in text:
    raise RuntimeError("[Gemini] response boş veya 'class ApiSmokeIT' içermiyor; test üretimi başarısız.")

# ---------- 5) Java dosyasını yaz ----------
outdir = pathlib.Path("src/test/java/com/generated")
outdir.mkdir(parents=True, exist_ok=True)
outfile = outdir / "ApiSmokeIT.java"
outfile.write_text(text, encoding="utf-8")
print(f"Wrote {outfile}")
