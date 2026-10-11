import pytest
from fastapi.testclient import TestClient

import main


API_KEY = "test-smart-match-key"
ENDPOINT = "/properties/smart-match-builder"


def property_row(
    *,
    property_id="PROP-100",
    listing_type="sale",
    community="Dubai Marina",
    property_type="Apartment",
    bedrooms=2,
    price=1_500_000,
    status="Available",
    price_per_sqft=1250,
):
    """Return a database row using the column order expected by main.smart_match."""
    return (
        property_id,          # property_id
        f"LIST-{property_id}", # listing_id
        listing_type,         # listing_type
        community,            # community
        "Marina Tower",       # building
        property_type,        # property_type
        bedrooms,             # bedrooms
        2,                    # bathrooms
        1200,                 # area_sqft
        price,                # price
        "AED",                # currency
        None,                 # rent_period
        price_per_sqft,       # price_per_sqft
        "furnished",          # furnishing
        "good",               # condition
        10,                   # floor
        "marina",             # view
        1,                    # parking
        ["pool"],             # amenities
        "vacant",             # occupancy
        status,               # status
        "AGENT-1",            # agent_id
    )


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, *_args, **_kwargs):
        return None

    def fetchall(self):
        return self.rows

    def close(self):
        return None


class FakeConnection:
    def __init__(self, rows):
        self.fake_cursor = FakeCursor(rows)

    def cursor(self):
        return self.fake_cursor

    def close(self):
        return None


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("API_KEY", API_KEY)
    return TestClient(main.app)


def request_payload(**overrides):
    payload = {
        "purpose": "buy",
        "listing_type": "sale",
        "community": "Dubai Marina",
        "property_type": "Apartment",
        "bedrooms": 2,
        "budget": 2_000_000,
        "community_priority": "required",
        "property_type_priority": "required",
        "bedrooms_priority": "required",
        "budget_priority": "required",
    }
    payload.update(overrides)
    return payload


def install_fake_database(monkeypatch, rows):
    # The endpoint checks this setting before calling psycopg.connect.
    # Use a dummy value and replace the actual connection with a fake.
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setattr(
        main.psycopg,
        "connect",
        lambda *_args, **_kwargs: FakeConnection(rows),
    )


def post_smart_match(client, payload):
    return client.post(
        ENDPOINT,
        json=payload,
        headers={"X-API-Key": API_KEY},
    )


def test_exact_match_returns_success_and_expected_response_shape(
    client, monkeypatch
):
    install_fake_database(monkeypatch, [property_row()])

    response = post_smart_match(client, request_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["match_count"] == 1
    assert len(body["matches"]) == 1

    match = body["matches"][0]
    assert match["property_id"] == "PROP-100"
    assert match["community"] == "Dubai Marina"
    assert match["match_score"] >= 85
    assert match["match_level"] == "strong"
    assert isinstance(match["match_reasons"], list)


def test_required_community_is_never_silently_relaxed(client, monkeypatch):
    install_fake_database(monkeypatch, [property_row(community="Dubai Marina")])

    response = post_smart_match(
        client,
        request_payload(community="Palm Jumeirah"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["match_count"] == 0
    assert body["matches"] == []
    assert "No strong matches" in body["message"]


def test_preferred_bedroom_count_can_return_a_ranked_alternative(
    client, monkeypatch
):
    install_fake_database(
        monkeypatch,
        [property_row(bedrooms=3)],
    )

    response = post_smart_match(
        client,
        request_payload(bedrooms_priority="preferred"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["match_count"] == 1

    match = body["matches"][0]
    assert match["bedrooms"] == 3
    assert "One-bedroom upgrade" in match["match_reasons"]


def test_invalid_priority_returns_400_without_database_access(
    client, monkeypatch
):
    def unexpected_database_call(*_args, **_kwargs):
        pytest.fail("Database should not be accessed for invalid priorities")

    monkeypatch.setattr(main.psycopg, "connect", unexpected_database_call)

    response = post_smart_match(
        client,
        request_payload(community_priority="must-have"),
    )

    assert response.status_code == 400
    assert "Invalid priority" in response.json()["detail"]


def test_empty_database_result_returns_clear_no_match_response(
    client, monkeypatch
):
    install_fake_database(monkeypatch, [])

    response = post_smart_match(client, request_payload())

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "match_count": 0,
        "matches": [],
        "message": "No strong matches found based on the current requirements.",
    }


def test_missing_required_input_returns_422(client):
    payload = request_payload()
    payload.pop("budget")

    response = post_smart_match(client, payload)

    assert response.status_code == 422


def test_slightly_over_budget_preferred_property_is_labeled_clearly(
    client, monkeypatch
):
    install_fake_database(
        monkeypatch,
        [property_row(price=1_040_000)],
    )

    response = post_smart_match(
        client,
        request_payload(
            budget=1_000_000,
            budget_priority="preferred",
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["match_count"] == 1

    match = body["matches"][0]
    assert match["price"] == 1_040_000
    assert "Slightly above target budget" in match["match_reasons"]


def test_only_top_three_matches_are_returned_in_score_order(
    client, monkeypatch
):
    rows = [
        property_row(property_id="PROP-LOW", price=1_100_000),
        property_row(property_id="PROP-MID1", price=1_300_000),
        property_row(property_id="PROP-MID2", price=1_500_000),
        property_row(property_id="PROP-HIGH", price=1_700_000),
    ]
    install_fake_database(monkeypatch, rows)

    response = post_smart_match(client, request_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["match_count"] == 3
    assert len(body["matches"]) == 3

    scores = [item["match_score"] for item in body["matches"]]
    assert scores == sorted(scores, reverse=True)
    returned_ids = {item["property_id"] for item in body["matches"]}
    assert "PROP-HIGH" not in returned_ids


def test_investment_matching_considers_price_per_square_foot(
    client, monkeypatch
):
    rows = [
        property_row(property_id="PROP-LOW-PSF", price_per_sqft=1000),
        property_row(property_id="PROP-MID-PSF", price_per_sqft=1250),
        property_row(property_id="PROP-HIGH-PSF", price_per_sqft=1500),
    ]
    install_fake_database(monkeypatch, rows)

    response = post_smart_match(
        client,
        request_payload(purpose="invest"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["match_count"] == 3

    lowest_cost_match = body["matches"][0]
    assert lowest_cost_match["property_id"] == "PROP-LOW-PSF"
    assert (
        "Competitive price per square foot"
        in lowest_cost_match["match_reasons"]
    )
    assert (
        "Competitive investment price per square foot"
        in lowest_cost_match["match_reasons"]
    )


def test_inferred_requirement_cannot_be_required(client, monkeypatch):
    def unexpected_database_call(*_args, **_kwargs):
        pytest.fail("Database should not be accessed for invalid requirements")

    monkeypatch.setattr(main.psycopg, "connect", unexpected_database_call)

    payload = {
        "purpose": "buy",
        "listing_type": "sale",
        "requirements": {
            "community": {
                "value": "Dubai Marina",
                "priority": "required",
                "source": "inferred",
            }
        },
    }

    response = client.post(
        "/properties/smart-match",
        json=payload,
        headers={"X-API-Key": API_KEY},
    )

    assert response.status_code == 400
    assert "cannot use priority 'required'" in response.json()["detail"]
