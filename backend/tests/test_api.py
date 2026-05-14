"""API smoke and regression tests for VolunteerMap backend."""

import os

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_login_success(client: TestClient):
    r = client.post(
        "/auth/login",
        json={"identity": "admin@volunteermap.org", "password": "admin123"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("role") == "admin"
    assert "token" in data


def test_login_invalid(client: TestClient):
    r = client.post(
        "/auth/login",
        json={"identity": "admin@volunteermap.org", "password": "wrong"},
    )
    assert r.status_code == 401


def test_login_demo_disabled(monkeypatch: pytest.MonkeyPatch, client: TestClient):
    monkeypatch.setenv("ENABLE_DEMO_AUTH", "false")
    r = client.post(
        "/auth/login",
        json={"identity": "admin@volunteermap.org", "password": "admin123"},
    )
    assert r.status_code == 403


def test_surveys_all_shape(client: TestClient):
    r = client.get("/surveys/all")
    assert r.status_code == 200
    body = r.json()
    assert "surveys" in body
    assert "count" in body
    assert isinstance(body["surveys"], list)


def test_delete_volunteer_known_id(client: TestClient):
    """Regression: delete endpoint must not raise NameError."""
    r = client.delete("/volunteers/vol_001")
    assert r.status_code in (200, 404)


def test_csv_rejects_non_csv(client: TestClient):
    r = client.post(
        "/surveys/upload-csv",
        files={"file": ("test.txt", b"a,b", "text/plain")},
    )
    assert r.status_code == 400
