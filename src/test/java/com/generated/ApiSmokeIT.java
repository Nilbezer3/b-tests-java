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

    private static final String BASE_URL = System.getenv("BASE_URL") != null ? System.getenv("BASE_URL") : "http://localhost:8080";

    @BeforeAll
    static void setup() {
        RestAssured.baseURI = BASE_URL;
    }

    static Stream<Arguments> apiEndpoints() {
        return Stream.of(
            Arguments.of("GET", "/health")
        );
    }

    @ParameterizedTest(name = "{0} {1}")
    @MethodSource("apiEndpoints")
    void verifyApiEndpointStatus(String method, String path) {
        RestAssured.given()
            .when()
            .request(method, path)
            .then()
            .statusCode(anyOf(is(200), is(201), is(400), is(401), is(403), is(404), is(405), is(422)));
    }
}