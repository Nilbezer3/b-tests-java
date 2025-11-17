package com.generated;

import io.restassured.RestAssured;
import io.restassured.http.Method;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import static org.hamcrest.Matchers.anyOf;
import static org.hamcrest.Matchers.is;

import java.util.stream.Stream;

public class ApiSmokeIT {

    private static final String BASE_URL_ENV = System.getenv("BASE_URL");
    private static final String DEFAULT_BASE_URL = "http://localhost:8080";
    private static String BASE_URI;

    @BeforeAll
    static void setup() {
        BASE_URI = BASE_URL_ENV != null && !BASE_URL_ENV.isEmpty() ? BASE_URL_ENV : DEFAULT_BASE_URL;
        RestAssured.baseURI = BASE_URI;
    }

    static Stream<Arguments> apiEndpoints() {
        return Stream.of(
            Arguments.of(Method.GET, "/ping"),
            Arguments.of(Method.GET, "/status2"),
            Arguments.of(Method.GET, "/health"),
            Arguments.of(Method.GET, "/greet/World"),
            Arguments.of(Method.GET, "/time"),
            Arguments.of(Method.GET, "/echo"),
            Arguments.of(Method.GET, "/version")
        );
    }

    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("apiEndpoints")
    void verifyApiEndpointStatus(Method method, String path) {
        RestAssured.given()
            .when()
            .request(method, path)
            .then()
            .statusCode(anyOf(is(200), is(201), is(400), is(401), is(403), is(404), is(405), is(422)));
    }
}