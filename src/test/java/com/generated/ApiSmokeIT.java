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
        RestAssured.baseURI = System.getenv("BASE_URL");
        if (RestAssured.baseURI == null || RestAssured.baseURI.isEmpty()) {
            RestAssured.baseURI = "http://localhost:8080";
        }
    }

    static Stream<Arguments> apiEndpoints() {
        return Stream.of(
            Arguments.of(Method.GET, "/ping"),
            Arguments.of(Method.GET, "/health"),
            Arguments.of(Method.GET, "/greet/1"),
            Arguments.of(Method.GET, "/echo"),
            Arguments.of(Method.POST, "/sum"),
            Arguments.of(Method.GET, "/time"),
            Arguments.of(Method.GET, "/version"),
            Arguments.of(Method.GET, "/status3")
        );
    }

    @ParameterizedTest
    @MethodSource("apiEndpoints")
    void verifyApiEndpointStatus(Method method, String path) {
        RestAssured.given()
            .request(method, path)
            .then()
            .statusCode(anyOf(is(200), is(201), is(400), is(401), is(403), is(404), is(405), is(422)));
    }
}