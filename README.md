# AI Voice Sales Agent

An AI-powered voice sales agent designed to understand customer needs, recommend relevant options, suggest alternatives, qualify leads, and guide customers toward the next step in their buying journey.

This repository contains the backend API for a real-estate voice-agent demonstration, built around the fictional business scenario **Northstar Real Estate**. The underlying approach is intended to support reusable conversational sales and booking workflows.

## Overview

Traditional voice receptionists often focus on answering questions and collecting information. This project explores a more proactive approach: helping customers discover suitable options, handling requirements intelligently, and supporting the journey from initial inquiry to appointment booking.

The backend connects the voice-agent workflow with property data, matching logic, availability checks, calendar operations, and agent notifications.

## Key Features

- **Smart property matching:** Evaluate customer requirements and identify relevant property options.
- **Alternative recommendations:** Support alternative property suggestions when an exact match is unavailable.
- **Property search API:** Retrieve property records using defined search criteria.
- **Availability checking:** Check an assigned agent's availability for a requested viewing.
- **Viewing booking:** Support booking requests through the backend API.
- **Calendar integration:** Integrate with Google Calendar for scheduling workflows.
- **Agent notifications:** Support email notifications to agents.
- **Lead and customer workflow support:** Connect conversational interactions to backend business logic.
- **Cloud deployment:** Backend deployed on Railway.

> Note: Feature behavior and integrations depend on the current implementation and configured credentials. The fictional Northstar dataset is for demonstration purposes and should not be treated as live property inventory.

## Architecture

```text
Customer
   |
   v
AI Voice Agent
   |
   v
FastAPI Backend
   |
   +---- Property Search
   |
   +---- Smart Matching
   |
   +---- Availability Checks
   |
   +---- Viewing Booking
   |
   +---- Google Calendar
   |
   +---- Agent Notifications
   |
   v
Property Database
(Supabase / PostgreSQL)
```

The voice agent gathers customer requirements and invokes backend tools. The API performs the relevant business logic and returns structured results for the agent to communicate to the customer.

The backend is designed to keep property data and scheduling operations separate from the conversational interface.

## Technology Stack

- **Language:** Python
- **API framework:** FastAPI
- **Database:** Supabase / PostgreSQL
- **Calendar integration:** Google Calendar API
- **Email integration:** Gmail API
- **Deployment:** Railway
- **API testing and documentation:** FastAPI interactive documentation

## API Endpoints

The following routes are defined in the current application.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Root endpoint |
| GET | `/db-test` | Database connectivity test |
| GET | `/properties/search` | Property search |
| POST | `/properties/smart-match` | Smart property matching |
| POST | `/properties/smart-match-builder` | Smart-match request builder |
| POST | `/availability/check` | Check viewing availability |
| POST | `/availability/book` | Submit a viewing booking request |
| POST | `/notify-agent` | Agent notification workflow |
| GET | `/authorize` | Google OAuth authorization |
| GET | `/oauth2callback` | Google OAuth callback |
| GET | `/calendar-test` | Calendar integration test |
| GET | `/gmail-test` | Gmail integration test |

Request fields, validation rules, and response formats are defined by the application. Refer to the actual endpoint implementation and the generated API documentation before integrating a client.

### Interactive API Documentation

When the application is running locally, open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

These pages expose the schemas and operations available in the running FastAPI application.

## Local Development Setup

### Prerequisites

- Python installed on your machine
- Git
- Access to the configured database
- Google API credentials if using calendar and email integrations

### 1. Clone the repository

```bash
git clone https://github.com/shahid-ai-automation/ai-voice-sales-agent.git
cd ai-voice-sales-agent
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file containing the configuration required by the application.

Check the source code for the exact environment variable names and required values. Typical configuration categories include:

- Database connection settings
- Google OAuth credentials and redirect settings
- Google Calendar and Gmail integration settings
- Any additional service credentials used by the application

Do not commit `.env` files, OAuth tokens, service-account credentials, or API secrets to GitHub.

### 5. Run the API

```bash
uvicorn main:app --reload
```

Once the server starts, open `http://127.0.0.1:8000/docs` to inspect and test the available endpoints.

## Deployment

The backend is deployed using Railway.

For production deployments:

1. Configure the required environment variables in Railway.
2. Keep all credentials in secure environment configuration.
3. Verify database connectivity and external integrations.
4. Test the API endpoints after deployment.
5. Restrict diagnostic and OAuth routes appropriately for the production environment.

The current production service URL and integration settings should be maintained separately from sensitive credentials.

## Security Considerations

- Never commit API keys, OAuth client secrets, access tokens, or private credentials.
- Keep local configuration files excluded through `.gitignore`.
- Use HTTPS for production traffic and OAuth redirects.
- Avoid exposing diagnostic endpoints publicly without appropriate access controls.
- Validate incoming requests and handle errors without returning sensitive internal information.
- Use test data for demonstrations unless the system has been configured and authorized for real customer data.

## Current Scope

This repository focuses on the backend supporting the AI voice sales agent demonstration.

The current real-estate scenario uses fictional business and property data. Production use with a real business would require appropriate data, credentials, security controls, operational monitoring, and validation of the relevant workflows.

## Roadmap

Potential future improvements include:

- Automated tests for property matching and booking workflows
- More detailed API examples and schema documentation
- Improved observability and structured logging
- Stronger authentication and access controls
- Reusable configuration for multiple businesses
- Modular business logic for different industries
- A browser-based voice-agent demonstration
- Expanded evaluation of recommendation quality and customer conversion flows

Items in this roadmap are planned improvements, not claims of completed functionality.

## Project Purpose

This project demonstrates practical AI engineering across conversational voice workflows, backend APIs, database integration, intelligent recommendations, and scheduling automation.

The long-term direction is to build reusable AI agents that can do more than answer questions: they can understand needs, help customers evaluate options, and guide them toward meaningful next steps.

---

**Maintainer:** Shahid Abdullah

**Repository:** [ai-voice-sales-agent](https://github.com/shahid-ai-automation/ai-voice-sales-agent)