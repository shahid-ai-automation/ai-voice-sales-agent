import json

import pytest
from fastapi.testclient import TestClient

import main


API_KEY = "test-availability-key"
CHECK_ENDPOINT = "/availability/check"
BOOK_ENDPOINT = "/availability/book"


class FakeCursor:
    def __init__(self, row):
        self.row = row

    def execute(self, *_args, **_kwargs):
        return None

    def fetchone(self):
        return self.row

    def close(self):
        return None


class FakeConnection:
    def __init__(self, row):
        self.fake_cursor = FakeCursor(row)

    def cursor(self):
        return self.fake_cursor

    def close(self):
        return None


class FakeRequest:
    def __init__(self, result):
        self.result = result
        self.kwargs = None

    def execute(self):
        return self.result


class FakeEvents:
    def __init__(self, events=None, created_event=None):
        self.existing_events = events or []
        self.created_event = created_event or {"id": "calendar-event-123"}
        self.last_insert_body = None
        self.insert_calls = 0

    def list(self, **kwargs):
        return FakeRequest({"items": self.existing_events})

    def insert(self, **kwargs):
        self.insert_calls += 1
        self.last_insert_body = kwargs["body"]
        return FakeRequest(self.created_event)


class FakeCalendarService:
    def __init__(self, events=None):
        self.fake_events = FakeEvents(events=events)

    def events(self):
        return self.fake_events


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("API_KEY", API_KEY)
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("GOOGLE_TOKEN_JSON", json.dumps({
        "token": "fake-access-token",
        "refresh_token": "fake-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "scopes": ["https://www.googleapis.com/auth/calendar"],
    }))
    return TestClient(main.app)


def install_fake_database(monkeypatch, row=("AGENT-1",)):
    monkeypatch.setattr(
        main.psycopg,
        "connect",
        lambda *_args, **_kwargs: FakeConnection(row),
    )


def install_fake_calendar(monkeypatch, events=None):
    service = FakeCalendarService(events=events)
    monkeypatch.setattr(
        main.Credentials,
        "from_authorized_user_info",
        lambda *_args, **_kwargs: object(),
    )
    monkeypatch.setattr(main, "build", lambda *_args, **_kwargs: service)
    return service


def headers():
    return {"X-API-Key": API_KEY}


def check_payload(**overrides):
    payload = {
        "property_id": "PROP-100",
        "requested_date": "2030-06-15",
        "requested_time": "14:00",
    }
    payload.update(overrides)
    return payload


def booking_payload(**overrides):
    payload = {
        **check_payload(),
        "customer_name": "Test Customer",
        "customer_phone": "+971500000000",
        "purpose": "buy",
    }
    payload.update(overrides)
    return payload


def test_check_availability_returns_available_when_assigned_agent_is_free(
    client, monkeypatch
):
    install_fake_database(monkeypatch)
    install_fake_calendar(monkeypatch, events=[])

    response = client.post(CHECK_ENDPOINT, json=check_payload(), headers=headers())

    assert response.status_code == 200
    assert response.json() == {
        "available": True,
        "property_id": "PROP-100",
        "agent_id": "AGENT-1",
        "requested_date": "2030-06-15",
        "requested_time": "14:00",
        "message": "The assigned agent is available at the requested time.",
    }


def test_check_availability_returns_unavailable_for_assigned_agent_conflict(
    client, monkeypatch
):
    install_fake_database(monkeypatch)
    install_fake_calendar(
        monkeypatch,
        events=[{
            "description": "Viewing\nAssigned Agent: AGENT-1",
            "status": "confirmed",
        }],
    )

    response = client.post(CHECK_ENDPOINT, json=check_payload(), headers=headers())

    assert response.status_code == 200
    assert response.json()["available"] is False
    assert response.json()["agent_id"] == "AGENT-1"


def test_check_availability_returns_404_for_unknown_property(client, monkeypatch):
    install_fake_database(monkeypatch, row=None)

    response = client.post(CHECK_ENDPOINT, json=check_payload(), headers=headers())

    assert response.status_code == 404
    assert response.json()["detail"] == "Property not found"


def test_book_viewing_creates_calendar_event_and_notifies_agent(
    client, monkeypatch
):
    install_fake_database(monkeypatch)
    service = install_fake_calendar(monkeypatch, events=[])
    monkeypatch.setattr(
        main,
        "send_agent_notification",
        lambda **kwargs: {
            "notification_sent": True,
            "message_id": "email-message-123",
        },
    )

    response = client.post(BOOK_ENDPOINT, json=booking_payload(), headers=headers())

    assert response.status_code == 200
    body = response.json()
    assert body["booked"] is True
    assert body["property_id"] == "PROP-100"
    assert body["agent_id"] == "AGENT-1"
    assert body["event_id"] == "calendar-event-123"
    assert body["notification_sent"] is True
    assert body["notification_message_id"] == "email-message-123"
    assert service.fake_events.insert_calls == 1
    assert "Assigned Agent: AGENT-1" in service.fake_events.last_insert_body["description"]


def test_book_viewing_rejects_double_booking_without_creating_event(
    client, monkeypatch
):
    install_fake_database(monkeypatch)
    service = install_fake_calendar(
        monkeypatch,
        events=[{
            "description": "Existing viewing\nAssigned Agent: AGENT-1",
            "status": "confirmed",
        }],
    )
    monkeypatch.setattr(
        main,
        "send_agent_notification",
        lambda **kwargs: pytest.fail("Notification must not send on conflict"),
    )

    response = client.post(BOOK_ENDPOINT, json=booking_payload(), headers=headers())

    assert response.status_code == 409
    assert "already has a viewing" in response.json()["detail"]
    assert service.fake_events.insert_calls == 0


def test_book_viewing_returns_401_without_api_key(client, monkeypatch):
    monkeypatch.setattr(
        main.psycopg,
        "connect",
        lambda *_args, **_kwargs: pytest.fail("DB must not be accessed"),
    )

    response = client.post(BOOK_ENDPOINT, json=booking_payload())

    assert response.status_code == 401
