import os, json, pathlib, re, sys

# ---- payload.json'dan endpointleri yükle ----
payload = json.loads(open("payload.json").read())
raw = payload.get("endpoints", [])

pairs = []
for e in raw:
    m = e.get("method", "GET").upper()
    p = e.get("path", "/health")
    # path param -> basit sabit değer
    p = re.sub(r"\{[^/}]+\}", "World", p)  # /greet/{name} -> /greet/World
    if m == "POST" and p.startswith("/sum") and "?" not in p:
        p = p + "?a=1&b=2"
    pairs.append((m, p))

if not pairs:
    pairs = [("GET", "/health")]

# ---- Şimdilik direkt Java kodu üret (Gemini opsiyonel) ----
code = f"""// generated (fallback or Gemini)
package com.generated;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.anyOf;
import static org.hamcrest.Matchers.is;

import java.util.stream.Stream;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import org.junit.jupiter.params.provider.Arguments;

public class ApiSmokeIT {{

    static Stream<Arguments> cases() {{
        return Stream.of(
            {",\n            ".join([f"Arguments.of(\\"{m}\\", \\"{p}\\")" for m,p in pairs])}
        );
    }}

    @ParameterizedTest
    @MethodSource("cases")
    void smoke(String method, String path) {{
        String base = System.getenv().getOrDefault("BASE_URL", "http://localhost:8080");
        given()
        .when()
            .request(method, base + path)
        .then()
            .statusCode(anyOf(is(200), is(201), is(400), is(401), is(403), is(404), is(405), is(422)));
    }}
}}
"""

out = pathlib.Path("src/test/java/com/generated")
out.mkdir(parents=True, exist_ok=True)
(out / "ApiSmokeIT.java").write_text(code, encoding="utf-8")
print("Wrote src/test/java/com/generated/ApiSmokeIT.java")
