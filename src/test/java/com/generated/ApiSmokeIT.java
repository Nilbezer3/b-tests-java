package com.generated;

import io.restassured.RestAssured;
import io.restassured.http.Method;
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
        String baseUrl = System.getenv("BASE_URL");
        if (baseUrl == null || baseUrl.isEmpty()) {
            baseUrl = "http://localhost:8080";
        }
        RestAssured.baseURI = baseUrl;
    }

    static Stream<Arguments> apiEndpoints() {
        return Stream.of(
            Arguments.of(Method.GET, "/health")
        );
    }

    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("apiEndpoints")
    void smokeTestApiEndpoints(Method method, String path) {
        RestAssured.given()
            .request(method, path)
            .then()
            .statusCode(anyOf(is(200), is(201), is(400), is(401), is(403), is(404), is(405), is(422)));
    }
}