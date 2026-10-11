# AI Voice Sales Agent

A FastAPI backend for a voice-based real-estate sales and receptionist workflow, demonstrated with the fictional **Northstar Real Estate** business and a Supabase/PostgreSQL property dataset.

The service connects a voice platform such as Retell AI to property search, requirement-aware smart matching, viewing availability, booking, Google Calendar, and email notification workflows.

> **Deployment status:** A public Railway demo deployment exists. The repository and sample property dataset are for demonstration and evaluation; do not treat the project as production-ready for real customers until the limitations in [Production readiness](#production-readiness-and-known-limitations) are addressed.

- **GitHub:** https://github.com/shahid-ai-automation/ai-voice-sales-agent
- **Production API base URL:** https://northstar-property-api-production.up.railway.app
- **Public health check:** https://northstar-property-api-production.up.railway.app/
- **Interactive API docs:** https://northstar-property-api-production.up.railway.app/docs

## Features

- **Property search** using area, property type, bedrooms, listing type, and maximum price.
- **Smart matching** with required, preferred, and flexible requirements; purpose-aware ranking; match explanations; and a maximum of three returned matches.
- **Alternative recommendations** when flexible or preferred criteria can be relaxed. Required criteria are not silently relaxed.
- **Viewing availability checks** against the assigned agent's existing events on the configured Google Calendar.
- **Viewing booking** with a conflict check, Google Calendar event creation, and an email notification attempt.
- **Agent notification endpoint** for sending a booking-related email.
- **API-key authentication** for business and diagnostic endpoints using the `X-API-Key` header.
- **Automated tests** run by GitHub Actions on pushes and pull requests.

## Architecture

```text
Retell AI / voice platform
          |
          | HTTPS + X-API-Key
          v
FastAPI service (Railway)
     |              |
     v              v
Supabase /       Google Calendar
PostgreSQL       and Gmail APIs
     |
     v
Property inventory and assigned agent IDs
```

The voice agent gathers customer requirements and calls backend endpoints. The backend is the source of truth for property records and the outcome of availability/booking operations. The voice agent must not claim a property was found, a time is available, or a viewing was booked unless the corresponding API response confirms it.

## API endpoints

All endpoints below are implemented in `main.py`. Protected routes require:

```http
X-API-Key: <your API_KEY value>
```

| Method | Endpoint | Authentication | Purpose / side effects |
|---|---|---|---|
| GET | `/` | Public | Health response; no external side effects |
| GET | `/docs` | Public | FastAPI Swagger documentation |
| GET | `/redoc` | Public | ReDoc API documentation |
| GET | `/db-test` | API key | Checks database connectivity and returns property count |
| GET | `/properties/search` | API key | Exact property search |
| POST | `/properties/smart-match` | API key | Smart matching from structured requirements |
| POST | `/properties/smart-match-builder` | API key | Builds a smart-match request from conversational fields |
| POST | `/availability/check` | API key | Checks whether the assigned agent has a calendar conflict |
| POST | `/availability/book` | API key | Creates a real Calendar event and attempts to send an email |
| POST | `/notify-agent` | API key | Sends a real email |
| GET | `/calendar-test` | API key | Reads upcoming Calendar events using the local `token.json` file |
| GET | `/gmail-test` | API key | Sends a real test email |
| GET | `/authorize` | Public OAuth entry point | Starts the legacy local OAuth flow; see the limitation below |
| GET | `/oauth2callback` | Public OAuth callback | Handles the legacy local OAuth flow and writes `token.json` |

**Important:** `/availability/book`, `/notify-agent`, and `/gmail-test` can create external side effects. Do not use them as casual health checks. Booking creates a real calendar event; the email endpoints send real email when configured successfully.

### Example: health check

```bash
curl https://northstar-property-api-production.up.railway.app/
```

Expected response:

```json
{
  "message": "Northstar Property API is running"
}
```

### Example: property search

```bash
curl -G "https://northstar-property-api-production.up.railway.app/properties/search" \
  -H "X-API-Key: $API_KEY" \
  --data-urlencode "community=Dubai Marina" \
  --data-urlencode "property_type=Apartment" \
  --data-urlencode "bedrooms=2" \
  --data-urlencode "listing_type=sale" \
  --data-urlencode "max_price=2000000"
```

### Example: check viewing availability

```bash
curl -X POST "https://northstar-property-api-production.up.railway.app/availability/check" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": "PROP-DXB-017",
    "requested_date": "2030-06-15",
    "requested_time": "14:00"
  }'
```

Dates use `YYYY-MM-DD`; times use 24-hour `HH:MM`. Viewing events are currently treated as 30 minutes long and use the `Asia/Karachi` timezone in the backend. Replace the sample property ID and date/time with valid values for your environment.

### Example: smart matching

The `/properties/smart-match-builder` endpoint accepts the conversational search fields documented in Swagger UI and translates them into the structured requirements used by `/properties/smart-match`. Each requirement uses a priority (`required`, `preferred`, or `flexible`) and a source (`explicit` or `inferred`). Inferred requirements cannot be marked as required without customer confirmation.

Use the live Swagger schema at `/docs` for the complete request and response model instead of guessing field names.

## Configuration

Configure secrets in the hosting provider's environment-variable settings. For local development, use a `.env` file that is not committed to Git.

| Variable / file | Purpose |
|---|---|
| `API_KEY` | Shared secret checked against the `X-API-Key` request header |
| `DATABASE_URL` | PostgreSQL connection string for the Supabase database |
| `GOOGLE_TOKEN_JSON` | Authorized Google OAuth token JSON used by availability, booking, and Gmail workflows |
| `client_secret_*.json` | Client-secret file expected by the legacy local OAuth helper; not committed to this repository |
| `token.json` | Local OAuth token file used by `/calendar-test`; not committed to this repository |

Never publish API keys, database credentials, Google OAuth client secrets, refresh tokens, or access tokens. If a secret is accidentally committed, removing it from the latest commit is not enough: rotate the secret.

## Run locally

### Prerequisites

- Python 3.12 recommended (the GitHub Actions workflow currently tests with Python 3.12)
- PostgreSQL/Supabase access for live database-backed use
- Google Calendar/Gmail credentials for live integrations

### Setup

Windows PowerShell:

```powershell
git clone https://github.com/shahid-ai-automation/ai-voice-sales-agent.git
cd ai-voice-sales-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create a local `.env` with the required configuration. Do not paste production secrets into source code, README files, issues, or chat logs.

Start the API:

```bash
python -m uvicorn main:app --reload
```

Then open:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/

## Automated tests

The test suite is in `tests/`. Install development dependencies and run it with:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

GitHub Actions runs the same command on pushes and pull requests.

The tests cover API-key behavior and route protection, Smart Matching behavior and edge cases, availability responses, booking outcomes, and double-booking rejection. External systems are mocked: the automated tests do **not** connect to production Supabase, create real Google Calendar events, or send real Gmail messages. A passing CI run verifies the covered backend behavior, not the full Retell-to-Railway-to-Google end-to-end flow.

## Deployment

The backend is deployed on Railway at:

`https://northstar-property-api-production.up.railway.app`

For a deployment or redeployment:

1. Confirm `API_KEY`, `DATABASE_URL`, and `GOOGLE_TOKEN_JSON` are configured in Railway.
2. Confirm the Retell custom functions send `X-API-Key` for every protected endpoint they call.
3. Check the public root endpoint first.
4. Use a protected, non-mutating endpoint for verification. Do not use booking or email test endpoints just to check whether the service is online.
5. Review Railway logs and the GitHub Actions test result after changes.

A GitHub merge triggers a Railway deployment only if the Railway service is configured to deploy from that repository/branch. Confirm the deployment status in Railway rather than assuming a successful GitHub merge means production has updated.

## Production readiness and known limitations

This is a working demonstration backend, not a fully hardened multi-tenant production service. Before using it for real customer bookings, address and verify the following:

- **Legacy OAuth helper:** `google_calendar.py` sets `OAUTHLIB_INSECURE_TRANSPORT=1`, expects a local client-secret file, and hard-codes a localhost redirect URI. The `/authorize` and `/oauth2callback` routes should not be treated as a configured Railway OAuth flow. The deployed availability/booking path currently uses `GOOGLE_TOKEN_JSON`; review and explicitly configure any OAuth changes before editing this flow.
- **Calendar booking concurrency:** the backend checks for conflicts and then inserts an event as separate operations. Simultaneous requests could race; use a stronger reservation/locking strategy before relying on it for high-volume bookings.
- **Notification routing:** the current email helper uses a hard-coded demo recipient address. Configure verified recipient routing before expecting notifications to reach each property's assigned agent.
- **Calendar diagnostics:** `/calendar-test` reads `token.json`, while the deployed booking and availability endpoints use `GOOGLE_TOKEN_JSON`. These are different credential paths.
- **Error handling and validation:** review date/time validation, external API failures, connection cleanup, and structured logging before production use.
- **Customer data:** use synthetic/demo data until privacy, retention, consent, and access controls are defined for real customer information.
- **Rate limiting and operations:** API-key authentication is implemented, but production use should also include suitable rate limiting, monitoring, secret rotation, backups, and an incident-response process.

The repository currently demonstrates one business scenario and does not yet provide tenant isolation or a configurable multi-business deployment layer.

## Project structure

```text
.
├── main.py                         # FastAPI application and endpoints
├── google_calendar.py              # Google OAuth helper and Gmail service setup
├── requirements.txt                # Runtime dependencies
├── requirements-dev.txt            # Test dependencies
├── tests/
│   ├── test_api_auth.py            # API-key and route-wiring tests
│   ├── test_smart_matching.py      # Smart Matching tests
│   └── test_availability_booking.py # Availability and booking tests
└── .github/
    └── workflows/
        └── tests.yml               # GitHub Actions test workflow
```

## Maintainer

**Shahid Abdullah**

Repository: https://github.com/shahid-ai-automation/ai-voice-sales-agent
