package com.generated;

import io.restassured.RestAssured;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import java.util.stream.Stream;

import static org.hamcrest.Matchers.anyOf;
import static org.hamcrest.Matchers.is;

public class ApiSmokeIT {

    @BeforeAll
    static void setup() {
        String baseUrlEnv = System.getenv("BASE_URL");
        String defaultBaseUrl = "http://localhost:8080";
        RestAssured.baseURI = baseUrlEnv != null && !baseUrlEnv.isEmpty() ? baseUrlEnv : defaultBaseUrl;
    }

    static Stream<Arguments> apiEndpoints() {
        return Stream.of(
            Arguments.of("GET", "/ping"),
            Arguments.of("GET", "/health"),
            Arguments.of("GET", "/greet/World"),
            Arguments.of("GET", "/echo"),
            Arguments.of("GET", "/time"),
            Arguments.of("GET", "/version"),
            Arguments.of("GET", "/status3")
        );
    }

    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("apiEndpoints")
    void smokeTestApi(String method, String path) {
        // For the given endpoints, all requests are GET.
        // The 'method' parameter is included for future expansion as per requirements.
        RestAssured.given()
            .when()
            .get(path)
            .then()
            .log().all()
            .statusCode(anyOf(is(200), is(201), is(400), is(401), is(403), is(404), is(405), is(422)));
    }
}