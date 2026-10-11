import os

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

import main


# Use a tiny isolated route so successful authentication can be tested
# without calling the database, Google Calendar, Gmail, or Railway.
auth_test_app = FastAPI()


@auth_test_app.get("/protected", dependencies=[Depends(main.require_api_key)])
def protected_test_route():
    return {"authenticated": True}


@pytest.fixture
def client():
    return TestClient(auth_test_app)


def test_missing_api_key_configuration_returns_503(client, monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)

    response = client.get("/protected")

    assert response.status_code == 503
    assert response.json()["detail"] == "API authentication is not configured."


def test_missing_request_api_key_returns_401(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "test-secret-key")

    response = client.get("/protected")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key."


def test_incorrect_request_api_key_returns_401(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "test-secret-key")

    response = client.get(
        "/protected",
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key."


def test_correct_request_api_key_is_accepted(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "test-secret-key")

    response = client.get(
        "/protected",
        headers={"X-API-Key": "test-secret-key"},
    )

    assert response.status_code == 200
    assert response.json() == {"authenticated": True}


def test_production_routes_are_wired_to_api_key_authentication():
    protected_paths = {
        "/properties/smart-match",
        "/properties/smart-match-builder",
        "/db-test",
        "/properties/search",
        "/calendar-test",
        "/availability/check",
        "/availability/book",
        "/gmail-test",
        "/notify-agent",
    }

    routes_by_path = {
        route.path: route
        for route in main.app.routes
        if hasattr(route, "dependant") and hasattr(route, "path")
    }

    for path in protected_paths:
        assert path in routes_by_path, f"Expected route {path} to exist"
        assert any(
            dependency.call is main.require_api_key
            for dependency in routes_by_path[path].dependant.dependencies
        ), f"Expected {path} to require an API key"


def test_public_health_endpoint_does_not_require_api_key(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)

    response = TestClient(main.app).get("/")

    assert response.status_code == 200
